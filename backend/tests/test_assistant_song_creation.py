"""
Regression tests for the conversational song-creation workflow
(app/ai/song_creation.py), driven through the real `/assistant` HTTP
endpoint -- not just the in-process graph -- so auth, history
round-tripping, and the server-side pending-operation security model are
all genuinely exercised.

All synthetic data is clearly test-marked ("اختبار" in every title/name)
and lives only in the disposable test database from tests/conftest.py.
Each test uses its own distinct, hand-written name/title (no random
digit suffixes) -- qwen2.5:3b was observed to occasionally mis-transcribe
an appended random token while extracting several fields from one
sentence (a small-LLM transcription-fidelity quirk, not a bug in the
extraction code), so uniqueness here comes from wording, not randomness.

`_post_retry` additionally tolerates the local model's rare run-to-run
extraction variance (CPU floating-point summation order can flip a
near-tied greedy-decoding choice even at temperature=0) by retrying the
one non-deterministic step a couple of times -- this guards test
stability against LLM inference noise, not against a product bug.
"""

from app.core.security import create_access_token
from app.models.artist import Artist
from app.models.maqam import Maqam
from app.models.pending_song_creation import PendingSongCreation
from app.models.song import Song
from app.models.user import User
from tests.conftest import unique_email


def _make_user(db_session) -> tuple[User, str]:
    user = User(name="Test Author", email=unique_email())
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.id)
    return user, token


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assistant_turn_from_response(user_message: str, data: dict) -> list[dict]:
    """Builds the two `history` entries a real client would append after
    one exchange, in the exact ConversationTurn shape."""

    return [
        {"role": "user", "content": user_message},
        {
            "role": "assistant",
            "content": data["answer"],
            "analysis": data["analysis"],
            "result_ids": [r["id"] for r in data["results"]],
        },
    ]


def _post_retry(client, payload, headers, predicate, attempts=3):
    data = None
    for _ in range(attempts):
        response = client.post("/assistant", json=payload, headers=headers)
        data = response.json()
        if predicate(data):
            return response, data
    return response, data


def test_creation_requires_login(client, db_session):
    response = client.post(
        "/assistant",
        json={"message": "بدي أضيف أغنية جديدة", "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["analysis"]["intent"] == "song_creation"
    assert "تسجيل الدخول" in data["answer"]
    assert data["analysis"]["draft_song"] is None
    assert data["results"] == []


def test_multi_turn_collection_across_history(client, db_session):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار المرحلي الاول")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار المرحلية الاولى"
    msg1 = f"بدي أضيف أغنية جديدة اسمها {title}"

    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("fields", {}).get("title") == title,
    )

    assert data1["analysis"]["intent"] == "song_creation"
    draft1 = data1["analysis"]["draft_song"]
    assert draft1["stage"] == "collecting"
    assert draft1["fields"]["title"] == title
    assert draft1["fields"]["artist"] is None

    history = _assistant_turn_from_response(msg1, data1)

    msg2 = f"المغني هو {artist.name_ar}"
    _, data2 = _post_retry(
        client, {"message": msg2, "limit": 5, "history": history}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )

    draft2 = data2["analysis"]["draft_song"]
    assert draft2["stage"] == "confirming"
    assert "pending_token" in draft2
    assert title in draft2["summary"]
    assert artist.name_ar in draft2["summary"]

    assert db_session.query(Song).filter(Song.title == title).first() is None


def test_one_shot_multi_field_reaches_confirmation(client, db_session):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار الدفعة الواحدة")
    maqam = Maqam(name_ar="مقام الاختبار الاول")
    db_session.add_all([artist, maqam])
    db_session.commit()

    title = "اغنية الاختبار بالدفعة الواحدة"
    message = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}، مقامها {maqam.name_ar}"

    _, data = _post_retry(
        client, {"message": message, "limit": 5}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )

    draft = data["analysis"]["draft_song"]
    assert draft["stage"] == "confirming"
    assert title in draft["summary"]
    assert artist.name_ar in draft["summary"]
    assert maqam.name_ar in draft["summary"]


def test_unknown_maqam_then_proceed_without_it(client, db_session):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار الرابع")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار الخامسة"
    # Deliberately fake but NOT phrased as "doesn't exist" -- qwen2.5:3b
    # was observed to treat a maqam value literally containing "لا وجود
    # له" (doesn't exist) as meta-commentary and dump it into
    # "description" instead of extracting it as the maqam field.
    unknown_maqam = "مقام الكوكب البعيد الوهمي"
    msg1 = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}، مقامها {unknown_maqam}"

    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: (
            (d["analysis"].get("draft_song") or {}).get("unresolved_maqam_name") == unknown_maqam
            and not (d["analysis"].get("draft_song") or {}).get("pending_artist_confirmation")
        ),
        attempts=6,
    )
    draft1 = data1["analysis"]["draft_song"]

    assert draft1["stage"] == "collecting"
    assert draft1["unresolved_maqam_name"] == unknown_maqam
    assert not draft1["pending_artist_confirmation"]

    history = _assistant_turn_from_response(msg1, data1)
    r2 = client.post(
        "/assistant",
        json={"message": "بدون مقام", "limit": 5, "history": history},
        headers=_auth(token),
    )
    data2 = r2.json()
    draft2 = data2["analysis"]["draft_song"]

    assert draft2["stage"] == "confirming"
    assert "المقام" not in draft2["summary"]


def test_duplicate_song_refused_at_collection(client, db_session):
    user, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار للتكرار")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار المكررة"
    existing_song = Song(title=title, artist_id=artist.id, created_by=user.id)
    db_session.add(existing_song)
    db_session.commit()

    message = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}"
    _, data = _post_retry(
        client, {"message": message, "limit": 5}, _auth(token),
        lambda d: str(existing_song.id) in d["answer"],
    )
    draft = data["analysis"]["draft_song"]

    assert draft["stage"] == "collecting"
    assert str(existing_song.id) in data["answer"]
    assert db_session.query(Song).filter(Song.title == title).count() == 1


def test_cancellation_mid_flow(client, db_session):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار للإلغاء")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار للإلغاء"
    msg1 = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}"
    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )
    assert data1["analysis"]["draft_song"]["stage"] == "confirming"

    history = _assistant_turn_from_response(msg1, data1)
    r2 = client.post(
        "/assistant", json={"message": "لا، إلغاء", "limit": 5, "history": history}, headers=_auth(token)
    )
    data2 = r2.json()

    assert "إلغاء" in data2["answer"]
    assert data2["analysis"]["draft_song"] is None
    assert db_session.query(Song).filter(Song.title == title).first() is None


def test_db_failure_is_reported_honestly_and_not_replayable(client, db_session, monkeypatch):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار للفشل")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار للفشل"
    msg1 = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}"
    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )
    pending_token = data1["analysis"]["draft_song"]["pending_token"]

    import app.ai.song_creation as song_creation_module

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(song_creation_module, "create_song_with_staged_entities", _boom)

    history = _assistant_turn_from_response(msg1, data1)
    r2 = client.post(
        "/assistant", json={"message": "نعم", "limit": 5, "history": history}, headers=_auth(token)
    )
    data2 = r2.json()

    assert "خطأ" in data2["answer"]
    assert "نجاح" not in data2["answer"]
    assert db_session.query(Song).filter(Song.title == title).first() is None

    pending = (
        db_session.query(PendingSongCreation)
        .filter(PendingSongCreation.token == pending_token)
        .first()
    )
    assert pending.is_used is True


def test_success_with_new_artist_is_atomic_and_searchable(client, db_session):
    _, token = _make_user(db_session)
    maqam = Maqam(name_ar="مقام الاختبار للنجاح")
    db_session.add(maqam)
    db_session.commit()

    new_artist_name = "فنان نور الاختبار"
    title = "اغنية الاختبار الناجحة"

    msg1 = f"ضيف أغنية اسمها {title}، المغني {new_artist_name}، مقامها {maqam.name_ar}"
    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: (
            (d["analysis"].get("draft_song") or {}).get("pending_artist_confirmation")
            and not (d["analysis"].get("draft_song") or {}).get("unresolved_maqam_name")
        ),
    )
    draft1 = data1["analysis"]["draft_song"]
    assert draft1["stage"] == "collecting"
    staged_artist_name = draft1["pending_artist_confirmation"]
    assert staged_artist_name == new_artist_name
    assert not draft1["unresolved_maqam_name"]

    history = _assistant_turn_from_response(msg1, data1)
    r2 = client.post(
        "/assistant", json={"message": "نعم", "limit": 5, "history": history}, headers=_auth(token)
    )
    data2 = r2.json()
    draft2 = data2["analysis"]["draft_song"]
    assert draft2["stage"] == "confirming"

    history = _assistant_turn_from_response("نعم", data2)
    r3 = client.post(
        "/assistant", json={"message": "نعم اؤكد", "limit": 5, "history": history}, headers=_auth(token)
    )
    data3 = r3.json()

    assert "نجاح" in data3["answer"]
    assert title in data3["answer"]

    db_session.expire_all()
    new_artist = db_session.query(Artist).filter(Artist.name_ar == new_artist_name).first()
    assert new_artist is not None

    saved_song = db_session.query(Song).filter(Song.title == title).first()
    assert saved_song is not None
    assert saved_song.artist_id == new_artist.id
    assert saved_song.maqam_id == maqam.id

    structured = client.post(
        "/assistant",
        json={"message": f"اعطيني اغاني {new_artist_name}", "limit": 5},
    )
    structured_ids = [r["id"] for r in structured.json()["results"]]
    assert saved_song.id in structured_ids

    semantic = client.post(
        "/assistant",
        json={"message": title, "limit": 5},
    )
    semantic_ids = [r["id"] for r in semantic.json()["results"]]
    assert saved_song.id in semantic_ids


def test_ordinary_search_never_triggers_creation(client, db_session):
    response = client.post(
        "/assistant",
        json={"message": "اعطيني اغاني جديدة لفيروز", "limit": 5},
    )
    data = response.json()

    assert data["analysis"]["intent"] != "song_creation"


def test_replay_of_confirmation_is_rejected(client, db_session):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار لإعادة التشغيل")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار لإعادة التشغيل"
    msg1 = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}"
    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )
    confirming_history = _assistant_turn_from_response(msg1, data1)

    r2 = client.post(
        "/assistant",
        json={"message": "نعم", "limit": 5, "history": confirming_history},
        headers=_auth(token),
    )
    data2 = r2.json()
    assert "نجاح" in data2["answer"]

    # Replay: resend the SAME confirming-stage history (as if the client
    # replayed an old request) with another confirm.
    r3 = client.post(
        "/assistant",
        json={"message": "نعم", "limit": 5, "history": confirming_history},
        headers=_auth(token),
    )
    data3 = r3.json()

    assert "لا يوجد طلب" in data3["answer"]
    assert db_session.query(Song).filter(Song.title == title).count() == 1


def test_cross_user_cannot_confirm_anothers_pending_operation(client, db_session):
    _, token_a = _make_user(db_session)
    _, token_b = _make_user(db_session)
    artist = Artist(name_ar="فنان الاختبار لحماية المستخدم")
    db_session.add(artist)
    db_session.commit()

    title = "اغنية الاختبار لحماية المستخدم"
    msg1 = f"ضيف أغنية اسمها {title}، المغني {artist.name_ar}"
    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token_a),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )
    confirming_history = _assistant_turn_from_response(msg1, data1)
    pending_token = data1["analysis"]["draft_song"]["pending_token"]

    # User B, authenticated as themselves, sends a forged history
    # claiming user A's in-progress confirmation.
    forged = client.post(
        "/assistant",
        json={"message": "نعم", "limit": 5, "history": confirming_history},
        headers=_auth(token_b),
    )
    forged_data = forged.json()

    assert "لا يوجد طلب" in forged_data["answer"]
    assert db_session.query(Song).filter(Song.title == title).first() is None

    pending = (
        db_session.query(PendingSongCreation)
        .filter(PendingSongCreation.token == pending_token)
        .first()
    )
    assert pending.is_used is False  # untouched by the failed cross-user attempt

    # The legitimate owner can still confirm it afterward.
    real_confirm = client.post(
        "/assistant",
        json={"message": "نعم", "limit": 5, "history": confirming_history},
        headers=_auth(token_a),
    )
    assert "نجاح" in real_confirm.json()["answer"]


def test_correction_during_confirmation_issues_new_token(client, db_session):
    _, token = _make_user(db_session)
    artist = Artist(name_ar="فنان التصحيح")
    db_session.add(artist)
    db_session.commit()

    original_title = "الاغنية الاولى للتصحيح"
    corrected_title = "الاغنية الثانية"

    msg1 = f"ضيف أغنية اسمها {original_title}، المغني {artist.name_ar}"
    _, data1 = _post_retry(
        client, {"message": msg1, "limit": 5}, _auth(token),
        lambda d: d["analysis"].get("draft_song", {}).get("stage") == "confirming",
    )
    old_token = data1["analysis"]["draft_song"]["pending_token"]

    # NOTE: deliberately NOT retried -- a correction consumes/invalidates
    # the old pending token as a side effect even on an attempt that
    # doesn't match what a retry predicate expects, so blind retries here
    # would race against the token state instead of just re-trying a
    # clean read.
    history = _assistant_turn_from_response(msg1, data1)
    correction_msg = f"غيّر العنوان إلى {corrected_title}"
    r2 = client.post(
        "/assistant", json={"message": correction_msg, "limit": 5, "history": history}, headers=_auth(token)
    )
    data2 = r2.json()
    draft2 = data2["analysis"]["draft_song"]

    assert draft2["stage"] == "confirming"
    new_token = draft2["pending_token"]
    assert new_token != old_token
    assert corrected_title in draft2["summary"]
    assert original_title not in draft2["summary"]

    old_pending = (
        db_session.query(PendingSongCreation).filter(PendingSongCreation.token == old_token).first()
    )
    assert old_pending.is_used is True

    history2 = _assistant_turn_from_response(correction_msg, data2)
    r3 = client.post(
        "/assistant", json={"message": "نعم", "limit": 5, "history": history2}, headers=_auth(token)
    )
    data3 = r3.json()

    assert "نجاح" in data3["answer"]
    saved = db_session.query(Song).filter(Song.title == corrected_title).first()
    assert saved is not None
    assert db_session.query(Song).filter(Song.title == original_title).first() is None
