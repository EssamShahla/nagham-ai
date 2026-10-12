"""
Conversational "add a new song" workflow.

One LangGraph request = one turn. While collecting fields, the
in-progress draft round-trips through the client-resent `history` exactly
like follow_up/recommend_similar (app/ai/conversation.py) -- cheap, and no
write risk since nothing is inserted yet.

Once the draft is ready, the server creates an opaque, single-use,
short-lived `PendingSongCreation` row (same precedent as
`LoginExchangeCode`/`PendingGoogleLink`). From that point on, only the
opaque token crosses through `history` -- the client cannot forge or
replay a write by tampering with history content, because the actual
payload a confirm executes against always comes from a fresh server-side
re-read of that row, re-validated against whichever user is authenticated
on *that* request (never an identity implied by `history`).
"""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai.agent import extract_song_creation_fields
from app.ai.arabic_text import detect_difficulty, normalize_arabic, resolve_to_id
from app.models.pending_song_creation import PendingSongCreation
from app.models.user import User
from app.services.song_service import (
    DuplicateSongError,
    create_song_with_staged_entities,
    find_duplicate_song,
)


PENDING_TTL = timedelta(minutes=10)

SONG_CREATION_MARKERS = [
    "ضيف اغنية", "أضيف اغنية", "اضافة اغنية", "إضافة اغنية", "اضف اغنية",
    "سجل اغنية", "انشاء اغنية", "إنشاء اغنية", "ادخال اغنية", "إدخال اغنية",
    "اعمل اغنية جديدة", "ابي اضيف اغنية", "بدي اضيف اغنية", "بدي أضيف اغنية",
    "حابب اضيف اغنية",
]

_CONFIRM_WORDS = [
    "نعم", "ايه", "اه", "أكد", "اكد", "تأكيد", "تاكيد", "تمام", "موافق", "اوكي", "ok", "yes",
]
_CANCEL_WORDS = [
    "لا", "لأ", "إلغاء", "الغاء", "تراجع", "كنسل", "الغي", "cancel", "no",
]

LOGIN_REQUIRED_MESSAGE = "يرجى تسجيل الدخول لإضافة أغنية جديدة."

_NOTHING_PENDING_MESSAGE = (
    "لا يوجد طلب إضافة أغنية معلّق حاليًا في هذه المحادثة. "
    "يمكنك البدء من جديد بطلب إضافة أغنية."
)


def _normalized_words(message: str) -> set[str]:
    return set(normalize_arabic(message).split())


def is_song_creation_trigger(message: str) -> bool:
    normalized = normalize_arabic(message)
    return any(normalize_arabic(marker) in normalized for marker in SONG_CREATION_MARKERS)


def get_last_song_creation_draft(history: list[dict] | None):
    """
    The draft is only "live" if the MOST RECENT assistant turn was itself
    a song_creation turn -- if the user moved on to something else, an
    older in-progress draft is considered abandoned, not resumed.
    """

    for turn in reversed(history or []):
        if turn.get("role") == "assistant":
            analysis = turn.get("analysis") or {}
            if analysis.get("intent") == "song_creation":
                return analysis.get("draft_song")
            return None
    return None


def _message_is_confirm(message: str) -> bool:
    words = _normalized_words(message)
    return bool(words & {normalize_arabic(w) for w in _CONFIRM_WORDS})


def _message_is_cancel(message: str) -> bool:
    words = _normalized_words(message)
    return bool(words & {normalize_arabic(w) for w in _CANCEL_WORDS})


def _wants_to_skip(message: str, noun: str) -> bool:
    normalized = normalize_arabic(message)
    return normalize_arabic("بدون") in normalized and normalize_arabic(noun) in normalized


def _terminal(answer: str, draft: dict | None, results: list | None = None) -> dict:
    return {
        "answer": answer,
        "results": results or [],
        "search_type": "song_creation",
        "analysis": {"intent": "song_creation", "draft_song": draft},
    }


def _empty_draft() -> dict:
    return {
        "stage": "collecting",
        "fields": {
            "title": None,
            "artist": None,
            "composer": None,
            "lyricist_name": None,
            "musical_key": None,
            "maqam_id": None,
            "maqam_name": None,
            "rhythm_id": None,
            "rhythm_name": None,
            "difficulty": None,
            "description": None,
            "source_url": None,
        },
        "pending_artist_confirmation": None,
        "pending_composer_confirmation": None,
        "unresolved_maqam_name": None,
        "unresolved_rhythm_name": None,
    }


def _resolve_name_choice(db: Session, category: str, name: str):
    match = resolve_to_id(db, category, name)
    if match:
        entity_id, canonical_name = match
        return {"kind": "existing", "id": entity_id, "name": canonical_name}, None
    return None, name.strip()


def _resolve_reference_entity(db: Session, category: str, name: str):
    match = resolve_to_id(db, category, name)
    if match:
        return match[0], match[1], None
    return None, None, name.strip()


def _merge_extracted_fields(db: Session, draft: dict, extracted: dict, message: str) -> None:
    fields = draft["fields"]

    if extracted.get("title"):
        fields["title"] = extracted["title"].strip()

    if extracted.get("artist"):
        choice, needs_confirm = _resolve_name_choice(db, "artist", extracted["artist"])
        if choice:
            fields["artist"] = choice
            draft["pending_artist_confirmation"] = None
        else:
            draft["pending_artist_confirmation"] = needs_confirm

    if extracted.get("composer"):
        choice, needs_confirm = _resolve_name_choice(db, "composer", extracted["composer"])
        if choice:
            fields["composer"] = choice
            draft["pending_composer_confirmation"] = None
        else:
            draft["pending_composer_confirmation"] = needs_confirm

    if extracted.get("lyricist_name"):
        fields["lyricist_name"] = extracted["lyricist_name"].strip()

    if extracted.get("musical_key"):
        fields["musical_key"] = extracted["musical_key"].strip()

    if extracted.get("maqam"):
        entity_id, canonical, unresolved = _resolve_reference_entity(db, "maqam", extracted["maqam"])
        if entity_id:
            fields["maqam_id"], fields["maqam_name"] = entity_id, canonical
            draft["unresolved_maqam_name"] = None
        else:
            draft["unresolved_maqam_name"] = unresolved

    if extracted.get("rhythm"):
        entity_id, canonical, unresolved = _resolve_reference_entity(db, "rhythm", extracted["rhythm"])
        if entity_id:
            fields["rhythm_id"], fields["rhythm_name"] = entity_id, canonical
            draft["unresolved_rhythm_name"] = None
        else:
            draft["unresolved_rhythm_name"] = unresolved

    if extracted.get("difficulty"):
        fields["difficulty"] = extracted["difficulty"]
    elif not fields.get("difficulty"):
        detected = detect_difficulty(message)
        if detected:
            fields["difficulty"] = detected

    if extracted.get("description"):
        fields["description"] = extracted["description"].strip()

    if extracted.get("source_url"):
        fields["source_url"] = extracted["source_url"].strip()


def _consume_new_entity_confirmation(
    message: str, draft: dict, fields: dict, *, entity_key: str, pending_key: str, label: str
):
    """Returns a terminal response dict to stop here this turn, or None to
    fall through to normal extraction (the pending flag has been resolved
    either way)."""

    name = draft[pending_key]

    if _message_is_confirm(message):
        fields[entity_key] = {"kind": "new", "name": name}
        draft[pending_key] = None
        return None

    if _message_is_cancel(message):
        fields[entity_key] = None
        draft[pending_key] = None
        return _terminal(
            f'تم التراجع عن إضافة {label} جديد. من فضلك أعطني اسم {label} موجود في قاعدة البيانات.',
            draft,
        )

    return _terminal(
        f'هل تؤكد إضافة "{name}" كـ{label} جديد؟ أجب بنعم أو لا.',
        draft,
    )


def _build_summary(fields: dict) -> str:
    lines = [f'العنوان: {fields["title"]}']

    artist = fields.get("artist") or {}
    artist_line = f'الفنان: {artist.get("name")}'
    if artist.get("kind") == "new":
        artist_line += " (فنان جديد)"
    lines.append(artist_line)

    composer = fields.get("composer")
    if composer:
        composer_line = f'الملحن: {composer.get("name")}'
        if composer.get("kind") == "new":
            composer_line += " (ملحن جديد)"
        lines.append(composer_line)

    if fields.get("lyricist_name"):
        lines.append(f'كلمات: {fields["lyricist_name"]}')
    if fields.get("maqam_name"):
        lines.append(f'المقام: {fields["maqam_name"]}')
    if fields.get("musical_key"):
        lines.append(f'المفتاح: {fields["musical_key"]}')
    if fields.get("rhythm_name"):
        lines.append(f'الوزن: {fields["rhythm_name"]}')
    if fields.get("difficulty"):
        lines.append(f'الصعوبة: {fields["difficulty"]}')
    if fields.get("description"):
        lines.append(f'الوصف: {fields["description"]}')
    if fields.get("source_url"):
        lines.append(f'المصدر: {fields["source_url"]}')

    return "\n".join(lines)


def _create_pending_and_summarize(db: Session, draft: dict, current_user: User) -> dict:
    fields = draft["fields"]

    # Catch an obvious duplicate as early as collection time, not only at
    # the final confirm -- an artist staged as brand-new can't possibly
    # collide (it doesn't exist yet), so this only applies once the
    # artist resolved to an existing row.
    artist = fields.get("artist") or {}
    if artist.get("kind") == "existing":
        duplicate = find_duplicate_song(db, fields["title"], artist["id"])
        if duplicate is not None:
            return _terminal(
                f'توجد أغنية بنفس العنوان لهذا الفنان مسبقًا (المعرف: {duplicate.id})، '
                f'فلا حاجة لإضافتها مرة أخرى. يمكنك تغيير العنوان أو اختيار فنان آخر.',
                draft,
            )

    summary = _build_summary(fields)

    token = secrets.token_urlsafe(32)
    pending = PendingSongCreation(
        token=token,
        user_id=current_user.id,
        payload=fields,
        expires_at=datetime.now(timezone.utc) + PENDING_TTL,
        is_used=False,
    )
    db.add(pending)
    db.commit()

    new_draft = {"stage": "confirming", "pending_token": token, "summary": summary}

    answer = "إليك ملخص الأغنية الجديدة:\n\n" + summary + "\n\nهل تؤكد إضافتها؟ (نعم/لا)"
    return _terminal(answer, new_draft)


def _advance_collecting(db: Session, draft: dict, current_user: User) -> dict:
    fields = draft["fields"]

    if draft.get("pending_artist_confirmation"):
        name = draft["pending_artist_confirmation"]
        return _terminal(
            f'لم أجد فنانًا باسم "{name}" في قاعدة البيانات. هل تريد إضافته كفنان جديد؟ (نعم/لا)',
            draft,
        )

    if draft.get("pending_composer_confirmation"):
        name = draft["pending_composer_confirmation"]
        return _terminal(
            f'لم أجد ملحنًا باسم "{name}" في قاعدة البيانات. هل تريد إضافته كملحن جديد؟ (نعم/لا)',
            draft,
        )

    if draft.get("unresolved_maqam_name"):
        name = draft["unresolved_maqam_name"]
        return _terminal(
            f'لم أتعرف على مقام باسم "{name}" في قاعدة البيانات. '
            f'أعطني اسم مقام موجود، أو قل "بدون مقام" للمتابعة بدونه.',
            draft,
        )

    if draft.get("unresolved_rhythm_name"):
        name = draft["unresolved_rhythm_name"]
        return _terminal(
            f'لم أتعرف على وزن باسم "{name}" في قاعدة البيانات. '
            f'أعطني اسم وزن موجود، أو قل "بدون وزن" للمتابعة بدونه.',
            draft,
        )

    missing = []
    if not fields.get("title"):
        missing.append("اسم الأغنية")
    if not fields.get("artist"):
        missing.append("اسم الفنان")

    if missing:
        return _terminal("لإضافة الأغنية أحتاج: " + "، ".join(missing) + ".", draft)

    return _create_pending_and_summarize(db, draft, current_user)


def _handle_collecting(db: Session, message: str, draft: dict, current_user: User) -> dict:
    fields = draft["fields"]

    # A bare yes/no (or a bare "skip this field" instruction) carries no
    # extractable song information. qwen2.5:3b was observed to hallucinate
    # an entire fake song (fabricated title/artist/composer/maqam/etc.)
    # when asked to extract fields from a short, low-content message like
    # "نعم" or "بدون مقام" alone -- skip the extractor call entirely for
    # these rather than risk contaminating the draft with invented values.
    is_pure_yes_no = _message_is_confirm(message) or _message_is_cancel(message)

    if draft.get("pending_artist_confirmation"):
        response = _consume_new_entity_confirmation(
            message, draft, fields, entity_key="artist",
            pending_key="pending_artist_confirmation", label="فنان",
        )
        if response is not None:
            return response

    if draft.get("pending_composer_confirmation"):
        response = _consume_new_entity_confirmation(
            message, draft, fields, entity_key="composer",
            pending_key="pending_composer_confirmation", label="ملحن",
        )
        if response is not None:
            return response

    skipped_a_reference_field = False

    if draft.get("unresolved_maqam_name") and _wants_to_skip(message, "مقام"):
        draft["unresolved_maqam_name"] = None
        skipped_a_reference_field = True

    if draft.get("unresolved_rhythm_name") and _wants_to_skip(message, "وزن"):
        draft["unresolved_rhythm_name"] = None
        skipped_a_reference_field = True

    if not is_pure_yes_no and not skipped_a_reference_field:
        extracted = extract_song_creation_fields(message)
        _merge_extracted_fields(db, draft, extracted, message)

    return _advance_collecting(db, draft, current_user)


def _has_real_change(extracted: dict, payload: dict) -> bool:
    for key in ("title", "lyricist_name", "musical_key", "difficulty", "description", "source_url"):
        value = extracted.get(key)
        if value and value.strip() != (payload.get(key) or ""):
            return True

    if extracted.get("artist"):
        current = (payload.get("artist") or {}).get("name")
        if extracted["artist"].strip() != (current or ""):
            return True

    if extracted.get("composer"):
        current = (payload.get("composer") or {}).get("name")
        if extracted["composer"].strip() != (current or ""):
            return True

    if extracted.get("maqam"):
        if extracted["maqam"].strip() != (payload.get("maqam_name") or ""):
            return True

    if extracted.get("rhythm"):
        if extracted["rhythm"].strip() != (payload.get("rhythm_name") or ""):
            return True

    return False


def _handle_correction(
    db: Session, message: str, extracted: dict, pending: PendingSongCreation, current_user: User
) -> dict:
    draft = {
        "stage": "collecting",
        "fields": dict(pending.payload),
        "pending_artist_confirmation": None,
        "pending_composer_confirmation": None,
        "unresolved_maqam_name": None,
        "unresolved_rhythm_name": None,
    }

    _merge_extracted_fields(db, draft, extracted, message)

    # Invalidate the old pending row -- it must never be confirmable again,
    # even by a stale/duplicate client message holding its token.
    pending.is_used = True
    db.commit()

    return _advance_collecting(db, draft, current_user)


def _execute_confirmed_creation(db: Session, pending: PendingSongCreation, current_user: User) -> dict:
    payload = pending.payload

    # Mark used and commit FIRST, as its own transaction -- so a failed
    # creation attempt below (which rolls back ITS OWN transaction) can
    # never leave this pending row replayable.
    pending.is_used = True
    db.commit()

    try:
        song = create_song_with_staged_entities(
            db,
            title=payload["title"],
            artist_choice=payload["artist"],
            composer_choice=payload.get("composer"),
            rhythm_id=payload.get("rhythm_id"),
            maqam_id=payload.get("maqam_id"),
            lyricist_name=payload.get("lyricist_name"),
            musical_key=payload.get("musical_key"),
            difficulty=payload.get("difficulty"),
            description=payload.get("description"),
            created_by=current_user.id,
        )
    except DuplicateSongError as exc:
        existing = exc.existing_song
        return _terminal(
            f'توجد أغنية بنفس العنوان لهذا الفنان مسبقًا (المعرف: {existing.id})، '
            f'فلم تتم إضافة الأغنية الجديدة. يمكنك تغيير العنوان أو إلغاء الطلب.',
            None,
        )
    except Exception:
        return _terminal(
            "حدث خطأ أثناء حفظ الأغنية في قاعدة البيانات، ولم تُضاف. يرجى المحاولة مرة أخرى.",
            None,
        )

    answer = (
        "تمت إضافة الأغنية بنجاح.\n"
        f'العنوان: {song.title}\n'
        f'الفنان: {song.artist.name_ar if song.artist else "غير متوفر"}\n'
        f'المقام: {song.maqam.name_ar if song.maqam else "غير متوفر"}\n'
        f'المعرف: {song.id}'
    )

    return {
        "answer": answer,
        "results": [{"song": song, "similarity": None}],
        "search_type": "song_creation",
        "analysis": {"intent": "song_creation", "draft_song": None},
    }


def _handle_confirming(db: Session, message: str, draft: dict, current_user: User) -> dict:
    token = draft.get("pending_token")

    pending = (
        db.query(PendingSongCreation)
        .filter(PendingSongCreation.token == token)
        .with_for_update()
        .first()
    )

    if (
        pending is None
        or pending.is_used
        or pending.expires_at < datetime.now(timezone.utc)
        or pending.user_id != current_user.id
    ):
        # Deliberately the same message whether the token is missing,
        # expired, already used, or belongs to a different user -- never
        # reveal which case it is.
        return _terminal(_NOTHING_PENDING_MESSAGE, None)

    if _message_is_cancel(message):
        pending.is_used = True
        db.commit()
        return _terminal("تم إلغاء إضافة الأغنية.", None)

    if _message_is_confirm(message):
        return _execute_confirmed_creation(db, pending, current_user)

    extracted = extract_song_creation_fields(message)
    if _has_real_change(extracted, pending.payload):
        return _handle_correction(db, message, extracted, pending, current_user)

    return _terminal(
        'من فضلك أكّد بإرسال "نعم" لإضافة الأغنية أو "لا" للإلغاء، أو أرسل التعديل الذي تريده.',
        draft,
    )


def run_song_creation_node(
    db: Session,
    message: str,
    history: list[dict] | None,
    current_user: User | None,
) -> dict:
    if current_user is None:
        return _terminal(LOGIN_REQUIRED_MESSAGE, None)

    draft = get_last_song_creation_draft(history) or _empty_draft()

    if draft.get("stage") == "confirming":
        return _handle_confirming(db, message, draft, current_user)

    return _handle_collecting(db, message, draft, current_user)
