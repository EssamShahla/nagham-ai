"""
Session-scoped multi-turn conversation support and the non-song-search
intents: music theory questions, maqam comparison, song-specific
questions, and follow-ups that reference a previous turn.

History is never persisted server-side. The caller (eval harness or the
frontend) holds the conversation and resends the relevant prior turns with
each request -- this file only ever reads the `history` list it is given
for the duration of one request. See [[project_nagham_ai]] memory for why:
no persistent storage of private conversations without an explicit
privacy/retention design.

Each history turn is a dict:
{
    "role": "user" | "assistant",
    "content": str,
    "analysis": dict | None,       # assistant turns only
    "result_ids": list[int] | None,  # assistant turns only
}
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session, joinedload

from app.ai.arabic_text import (
    find_all_entity_mentions,
    normalize_arabic,
    resolve_song_title,
)
from app.ai.song_creation import get_last_song_creation_draft, is_song_creation_trigger
from app.models.maqam import Maqam
from app.models.maqam_jins import MaqamJins
from app.models.song import Song
from app.models.song_source import SongSource


DIFFICULTY_RANK = {"easy": 0, "medium": 1, "hard": 2}

_COMPARISON_MARKERS = ["الفرق بين", "الفرق ما بين", "شو الفرق", "ما الفرق"]

_THEORY_QUESTION_WORDS = ["شو", "ما هو", "ما هي", "ماهو", "ماهي", "ايش", "وش", "كيف", "اشرح", "فسر"]
_THEORY_TOPIC_WORDS = ["مقام", "جنس", "سلم", "غماز", "درجات", "درجة"]
_SONG_NOUNS = ["اغنية", "اغاني", "اغنيتين", "أغنية", "أغاني", "أغنيتين"]

_RECOMMEND_SIMILAR_MARKERS = ["نفس المقام", "بنفس المقام", "نفس اللحن", "نفس الجو", "مثلها", "شبيهة", "مشابهة"]

# Lyrics requests say "كلمات" / "نص الأغنية", not "أغنية"/"أغاني" -- they must
# NOT depend on _SONG_NOUNS, or a message like "هاتلي كلمات انت عمري" never
# reaches resolve_song_title and falls through to an unrelated semantic
# recommendation instead (the exact bug this route exists to fix).
_LYRICS_MARKERS = [
    "كلمات", "كلمات اغنية", "كلمات أغنية", "كلمات الاغنية", "كلمات الأغنية",
    "نص الاغنية", "نص الأغنية", "نص اغنية", "نص أغنية", "lyrics",
]

_FOLLOWUP_REFERENCE_MARKERS = [
    "هالاغاني", "هاي الاغاني", "هذه الاغاني", "من هالاغاني", "منهم", "من هذول",
    "اول اغنية", "أول اغنية", "اول أغنية", "الاغنية الاولى",
    "تاني اغنية", "ثاني اغنية", "الاغنية الثانية",
    "اخر اغنية", "آخر اغنية", "الاغنية الاخيرة",
    "الاسهل", "أسهل", "الاصعب", "أصعب", "اختار",
]

_ORDINAL_MARKERS = [
    (["اول", "أول"], 0),
    (["تاني", "ثاني"], 1),
    (["ثالث"], 2),
    (["اخر", "آخر"], -1),
]


def _normalized_contains(message: str, phrases: list[str]) -> bool:
    normalized = normalize_arabic(message)
    return any(normalize_arabic(p) in normalized for p in phrases)


def get_last_assistant_turn(history: list[dict] | None) -> dict | None:
    for turn in reversed(history or []):
        if turn.get("role") == "assistant" and turn.get("result_ids"):
            return turn
    return None


@dataclass
class ClassifiedIntent:
    route: str
    maqam_matches: list = field(default_factory=list)
    resolved_song_id: int | None = None


def classify_deterministic_intent(
    db: Session,
    message: str,
    history: list[dict] | None,
) -> ClassifiedIntent:
    """
    Deterministic pre-classification, tried BEFORE the LLM intent extractor.
    The small local LLM is not a reliable deterministic router for these
    cases, so recognizable patterns (comparison, theory, explicit song
    reference, follow-up reference words) are routed here directly.

    Falls through to "song_search" (the existing LLM-based pipeline) when
    nothing deterministic matches.
    """

    # Continuation takes priority over everything else: if the most
    # recent assistant turn was itself an in-progress song-creation draft,
    # always keep routing there regardless of this message's wording --
    # this is what lets "اسمها نسمة ليل" (no creation verb at all)
    # correctly continue an in-progress draft.
    active_draft = get_last_song_creation_draft(history)
    if active_draft and active_draft.get("stage") in ("collecting", "confirming"):
        return ClassifiedIntent(route="song_creation")

    if is_song_creation_trigger(message):
        return ClassifiedIntent(route="song_creation")

    last_turn = get_last_assistant_turn(history)

    if last_turn and _normalized_contains(message, _RECOMMEND_SIMILAR_MARKERS):
        return ClassifiedIntent(route="recommend_similar")

    if last_turn and _normalized_contains(message, _FOLLOWUP_REFERENCE_MARKERS):
        return ClassifiedIntent(route="follow_up")

    if _normalized_contains(message, _LYRICS_MARKERS):
        song_match = resolve_song_title(db, message)
        return ClassifiedIntent(
            route="lyrics_request",
            resolved_song_id=song_match[0] if song_match else None,
        )

    if _normalized_contains(message, _COMPARISON_MARKERS):
        maqam_matches = find_all_entity_mentions(db, message, "maqam")
        if len(maqam_matches) >= 2:
            return ClassifiedIntent(route="maqam_comparison", maqam_matches=maqam_matches[:2])
        # "الفرق بين" mentioned but we couldn't resolve two real maqamat --
        # still a theory-style question, let theory_node explain what it can.
        return ClassifiedIntent(route="theory_question", maqam_matches=maqam_matches)

    has_theory_question_word = _normalized_contains(message, _THEORY_QUESTION_WORDS)
    has_theory_topic_word = _normalized_contains(message, _THEORY_TOPIC_WORDS)
    has_song_noun = _normalized_contains(message, _SONG_NOUNS)

    if has_theory_question_word and has_theory_topic_word and not has_song_noun:
        maqam_matches = find_all_entity_mentions(db, message, "maqam")
        return ClassifiedIntent(route="theory_question", maqam_matches=maqam_matches)

    if has_song_noun:
        song_match = resolve_song_title(db, message)
        if song_match is not None:
            return ClassifiedIntent(route="song_question", resolved_song_id=song_match[0])

    return ClassifiedIntent(route="song_search")


_INTERVAL_NAMES_AR = {
    0.5: "نصف تون",
    0.75: "ثلاثة أرباع تون",
    1.0: "تون كامل",
    1.5: "تون ونصف",
}


def render_scale_pattern_ar(scale_pattern: list | None) -> str | None:
    """
    Render a maqam's numeric `scale_pattern` (interval sizes in whole-tone
    units between consecutive degrees) as Arabic interval-name words
    instead of raw numbers.

    qwen2.5:3b was caught live fabricating a bogus pseudo-scale instead of
    transcribing the real numeric array given in the prompt (e.g. Hijaz's
    real [0.5, 1.5, 0.5, 1.0, 0.5, 1.0, 1.0] came back as a nonsense
    "[د4، ج4، ج4، د5، ج4، د5، د5]"). Doing the translation deterministically
    in code removes that failure mode entirely -- the model only has to
    read Arabic words it was already given, never transcribe numbers.
    """

    if not scale_pattern:
        return None

    names = [_INTERVAL_NAMES_AR.get(float(step), str(step)) for step in scale_pattern]
    return " - ".join(names)


def build_maqam_facts(maqam: Maqam) -> str:
    """
    Grounded fact sheet for a maqam, read from the full ajnas breakdown
    (not just the legacy root/branch_jins pair) so multi-jins maqamat like
    Saba (3 overlapping ajnas) are described completely.
    """

    unavailable = "غير متوفر حاليًا في قاعدة البيانات"

    if maqam.ajnas_breakdown:
        ajnas_lines = []
        for entry in maqam.ajnas_breakdown:
            alt_note = "" if entry.is_primary_alternative else " (بديل موثّق غير أساسي)"
            ajnas_lines.append(
                f"  - الدرجة {entry.start_degree}: جنس {entry.jins.name_ar}{alt_note}"
            )
        ajnas_text = "\n".join(ajnas_lines)
    else:
        root = maqam.root_jins.name_ar if maqam.root_jins else unavailable
        branch = maqam.branch_jins.name_ar if maqam.branch_jins else unavailable
        ajnas_text = f"  - الجنس الأساسي: {root}\n  - الجنس الفرعي: {branch}"

    lines = [
        f"الاسم: {maqam.name_ar}" + (f" ({maqam.name_en})" if maqam.name_en else ""),
        f"الدرجة الأساس (tonic): {maqam.tonic or unavailable}",
        f"تفكيك الأجناس:\n{ajnas_text}",
        f"الغماز: {maqam.ghammaz or unavailable}",
        f"سلّم الدرجات (المسافات بين الدرجات المتتالية): "
        f"{render_scale_pattern_ar(maqam.scale_pattern) or unavailable}",
        f"الطابع/المزاج: {maqam.mood or unavailable}",
        f"الوصف: {maqam.description or unavailable}",
    ]

    return "\n".join(lines)


def build_song_facts(song: Song) -> str:
    unavailable = "غير متوفر"

    return "\n".join([
        f"العنوان: {song.title}",
        f"الفنان: {song.artist.name_ar if song.artist else unavailable}",
        f"الملحن: {song.composer.name_ar if song.composer else unavailable}",
        f"المقام: {song.maqam.name_ar if song.maqam else unavailable}",
        f"الصعوبة: {song.difficulty or unavailable}",
        f"السنة: {song.year or unavailable}",
        f"الوصف: {song.description or unavailable}",
    ])


def run_theory_node(db: Session, message: str, maqam_matches: list) -> dict:
    from app.ai.agent import generate_grounded_answer

    if not maqam_matches:
        answer = (
            "لم أتعرف على اسم مقام أو جنس محدد في سؤالك ضمن قاعدة البيانات "
            "الحالية، فلا أستطيع تقديم معلومات موثقة عنه."
        )
        return {"answer": answer, "results": [], "search_type": "theory_question"}

    maqam = (
        db.query(Maqam)
        .options(
            joinedload(Maqam.root_jins),
            joinedload(Maqam.branch_jins),
            joinedload(Maqam.ajnas_breakdown).joinedload(MaqamJins.jins),
        )
        .filter(Maqam.id == maqam_matches[0].entity_id)
        .first()
    )

    facts = build_maqam_facts(maqam)
    answer = generate_grounded_answer(message, facts, suggest_explorer=True)

    return {"answer": answer, "results": [], "search_type": "theory_question"}


def run_comparison_node(db: Session, message: str, maqam_matches: list) -> dict:
    from app.ai.agent import generate_grounded_answer

    maqamat = (
        db.query(Maqam)
        .options(
            joinedload(Maqam.root_jins),
            joinedload(Maqam.branch_jins),
            joinedload(Maqam.ajnas_breakdown).joinedload(MaqamJins.jins),
        )
        .filter(Maqam.id.in_([m.entity_id for m in maqam_matches]))
        .all()
    )

    facts = "\n\n".join(
        f"--- مقام {m.name_ar} ---\n{build_maqam_facts(m)}" for m in maqamat
    )

    answer = generate_grounded_answer(message, facts, suggest_explorer=True)

    return {"answer": answer, "results": [], "search_type": "maqam_comparison"}


def run_song_question_node(db: Session, song_id: int, message: str) -> dict:
    from app.ai.agent import generate_grounded_answer

    song = (
        db.query(Song)
        .options(joinedload(Song.artist), joinedload(Song.composer), joinedload(Song.maqam))
        .filter(Song.id == song_id)
        .first()
    )

    if song is None:
        return {
            "answer": "لم أجد هذه الأغنية في قاعدة البيانات.",
            "results": [],
            "search_type": "song_question",
        }

    answer = generate_grounded_answer(message, build_song_facts(song))

    return {
        "answer": answer,
        "results": [{"song": song, "similarity": None}],
        "search_type": "song_question",
    }


def _fallback_song_summary(song: Song) -> str:
    """
    Minimal summary built strictly from already-verified Song fields, used
    when `description` is empty -- unlike an LLM, this never invents
    biographical/historical prose about the song.
    """

    parts = [f'أغنية "{song.title}"']

    if song.artist:
        parts.append(f"لـ {song.artist.name_ar}")

    if song.maqam:
        parts.append(f"على مقام {song.maqam.name_ar}")

    return " ".join(parts) + "."


def run_lyrics_request_node(db: Session, song_id: int | None, message: str) -> dict:
    """
    Handle an explicit lyrics request ("كلمات اغنية ..."). Entirely
    deterministic/template-based -- no LLM call -- so it can never garble
    text or leak copyrighted lyrics: the only two outputs are "not found"
    or a response gated by `Song.lyrics_license` (see the Alembic migration
    `3eff4281930a` docstring for the license semantics).
    """

    if song_id is None:
        return {
            "answer": (
                "لم أجد أغنية بهذا الاسم في قاعدة البيانات، فلا أستطيع "
                "تزويدك بكلماتها."
            ),
            "results": [],
            "search_type": "lyrics_request",
        }

    song = (
        db.query(Song)
        .options(joinedload(Song.artist), joinedload(Song.composer), joinedload(Song.maqam))
        .filter(Song.id == song_id)
        .first()
    )

    if song is None:
        return {
            "answer": "لم أجد هذه الأغنية في قاعدة البيانات.",
            "results": [],
            "search_type": "lyrics_request",
        }

    if not song.lyrics:
        return {
            "answer": (
                f'لدي معلومات عن أغنية "{song.title}" لكن كلماتها غير '
                "مُدرجة في قاعدة البيانات حاليًا."
            ),
            "results": [{"song": song, "similarity": None}],
            "search_type": "lyrics_request",
        }

    if song.lyrics_license in ("public_domain", "licensed"):
        header = f'كلمات أغنية "{song.title}"'
        if song.artist:
            header += f" - {song.artist.name_ar}"

        attribution = f"\n\n({song.lyrics_rights_note})" if song.lyrics_rights_note else ""

        return {
            "answer": f"{header}:\n\n{song.lyrics}{attribution}",
            "results": [{"song": song, "similarity": None}],
            "search_type": "lyrics_request",
        }

    # "restricted" or unset -- Song.lyrics is never displayed verbatim here.
    source = (
        db.query(SongSource)
        .filter(SongSource.song_id == song.id, SongSource.source_type == "lyrics")
        .first()
    )

    lines = [
        f'لا يمكنني عرض كلمات أغنية "{song.title}" هنا بسبب قيود حقوق النشر.',
        "",
        f"الفنان: {song.artist.name_ar if song.artist else 'غير متوفر'}",
        f"الملحن: {song.composer.name_ar if song.composer else 'غير متوفر'}",
        f"المقام: {song.maqam.name_ar if song.maqam else 'غير متوفر'}",
    ]

    if song.year:
        lines.append(f"السنة: {song.year}")
    if song.difficulty:
        lines.append(f"الصعوبة: {song.difficulty}")

    lines.append("")
    lines.append(song.description or _fallback_song_summary(song))

    if source and source.source_url:
        lines.append("")
        lines.append(f"يمكنك مطالعة كلماتها عبر مصدر موثّق: {source.source_url}")
    else:
        lines.append("")
        lines.append("لا يوجد حاليًا رابط لمصدر موثّق لعرض الكلمات في قاعدة البيانات.")

    return {
        "answer": "\n".join(lines),
        "results": [{"song": song, "similarity": None}],
        "search_type": "lyrics_request",
    }


def _resolve_ordinal_index(message: str) -> int | None:
    normalized = normalize_arabic(message)
    for words, index in _ORDINAL_MARKERS:
        if any(normalize_arabic(w) in normalized for w in words):
            return index
    return None


def run_follow_up_node(db: Session, message: str, history: list[dict]) -> dict:
    from app.ai.agent import generate_grounded_answer, generate_rag_answer

    last_turn = get_last_assistant_turn(history)

    if last_turn is None:
        return {
            "answer": "لا يوجد نتائج سابقة في هذه المحادثة لأرجع إليها.",
            "results": [],
            "search_type": "follow_up",
        }

    result_ids = last_turn["result_ids"]
    songs = (
        db.query(Song)
        .options(joinedload(Song.artist), joinedload(Song.composer), joinedload(Song.maqam))
        .filter(Song.id.in_(result_ids))
        .all()
    )
    songs_by_id = {s.id: s for s in songs}
    ordered_songs = [songs_by_id[i] for i in result_ids if i in songs_by_id]

    if not ordered_songs:
        return {
            "answer": "لم أعد أجد الأغاني السابقة في قاعدة البيانات.",
            "results": [],
            "search_type": "follow_up",
        }

    normalized = normalize_arabic(message)
    wants_easiest = normalize_arabic("الاسهل") in normalized or normalize_arabic("أسهل") in normalized
    wants_hardest = normalize_arabic("الاصعب") in normalized or normalize_arabic("أصعب") in normalized

    if wants_easiest or wants_hardest:
        ranked = [s for s in ordered_songs if s.difficulty in DIFFICULTY_RANK]
        if not ranked:
            return {
                "answer": "لا تتوفر معلومات عن مستوى الصعوبة لهذه الأغاني.",
                "results": [],
                "search_type": "follow_up",
            }
        chosen = (
            min(ranked, key=lambda s: DIFFICULTY_RANK[s.difficulty])
            if wants_easiest
            else max(ranked, key=lambda s: DIFFICULTY_RANK[s.difficulty])
        )
        results = [{"song": chosen, "similarity": None}]
        answer = generate_rag_answer(user_message=message, search_results=results)
        return {"answer": answer, "results": results, "search_type": "follow_up"}

    ordinal_index = _resolve_ordinal_index(message)
    if ordinal_index is not None:
        try:
            chosen = ordered_songs[ordinal_index]
        except IndexError:
            return {
                "answer": "لا يوجد عدد كافٍ من الأغاني السابقة لتحديد هذا الترتيب.",
                "results": [],
                "search_type": "follow_up",
            }
        answer = generate_grounded_answer(message, build_song_facts(chosen))
        return {
            "answer": answer,
            "results": [{"song": chosen, "similarity": None}],
            "search_type": "follow_up",
        }

    # Reference recognized, but no specific selection criterion understood --
    # answer about the full previous result set rather than guessing.
    results = [{"song": s, "similarity": None} for s in ordered_songs]
    answer = generate_rag_answer(user_message=message, search_results=results)
    return {"answer": answer, "results": results, "search_type": "follow_up"}


def run_recommend_similar_node(db: Session, message: str, history: list[dict], limit: int) -> dict:
    from app.ai.agent import generate_rag_answer
    from app.ai.tools import structured_search_songs

    last_turn = get_last_assistant_turn(history)

    if last_turn is None:
        return {
            "answer": "لا يوجد أغنية سابقة في هذه المحادثة لأقترح أغنية مشابهة لها.",
            "results": [],
            "search_type": "recommend_similar",
        }

    previous_ids = last_turn["result_ids"]
    reference_song = (
        db.query(Song)
        .options(joinedload(Song.maqam))
        .filter(Song.id == previous_ids[0])
        .first()
    )

    if reference_song is None or reference_song.maqam is None:
        return {
            "answer": "لا أعرف مقام الأغنية السابقة، فلا أستطيع اقتراح أغنية بنفس المقام.",
            "results": [],
            "search_type": "recommend_similar",
        }

    candidates = structured_search_songs(
        db=db,
        maqam=reference_song.maqam.name_ar,
        limit=limit + len(previous_ids),
    )
    filtered = [s for s in candidates if s.id not in previous_ids][:limit]

    results = [{"song": s, "similarity": None} for s in filtered]
    answer = generate_rag_answer(user_message=message, search_results=results)

    return {"answer": answer, "results": results, "search_type": "recommend_similar"}
