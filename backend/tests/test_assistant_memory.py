"""
Regression tests for session-scoped multi-turn memory through the real
HTTP API (app/routers/assistant.py -> app/ai/graph.py), not just the
in-process eval harness.

Covers the reported bug: the chat must use the *previous turn's* results
when the user asks a follow-up, and two independent conversations
(empty `history`) must never bleed into each other.
"""

import uuid

from tests.conftest import unique_email

from app.models.artist import Artist
from app.models.maqam import Maqam
from app.models.song import Song
from app.models.user import User


def _seed_maqam_songs(db_session):
    # Each call needs its own uniquely-named artist/maqam -- Artist.name_ar
    # and Maqam.name_ar are both UNIQUE, and the test DB is shared across
    # every test function within this pytest session.
    #
    # Suffix is plain digits appended after a space, never a hyphenated
    # hex token glued onto a real maqam name -- qwen2.5:3b was observed
    # (see tests/test_assistant_song_creation.py) to sometimes drop a
    # trailing "-<hex>" suffix while extracting the maqam name, which then
    # fails the exact structured-search match against this seeded row's
    # full name (it only takes a dropped suffix in `canonicalize_value`'s
    # Levenshtein match vs. the extracted value to make this test flaky).
    suffix = str(uuid.uuid4().int)[:8]

    user = User(name="Test Author", email=unique_email())
    artist = Artist(name_ar=f"فنان تجريبي {suffix}")
    maqam = Maqam(name_ar=f"مقام تجريبي {suffix}")
    db_session.add_all([user, artist, maqam])
    db_session.commit()

    songs = [
        Song(title=f"اغنية الاختبار الاولى {suffix}", artist_id=artist.id, maqam_id=maqam.id, created_by=user.id),
        Song(title=f"اغنية الاختبار الثانية {suffix}", artist_id=artist.id, maqam_id=maqam.id, created_by=user.id),
    ]
    db_session.add_all(songs)
    db_session.commit()
    return maqam, songs


def test_follow_up_uses_previous_turn_results(client, db_session):
    maqam, _ = _seed_maqam_songs(db_session)
    search_message = f"اعطيني اغاني على مقام {maqam.name_ar}"

    first = client.post("/assistant", json={"message": search_message, "limit": 5})
    assert first.status_code == 200
    first_data = first.json()
    assert len(first_data["results"]) >= 1

    history = [
        {"role": "user", "content": search_message},
        {
            "role": "assistant",
            "content": first_data["answer"],
            "analysis": first_data["analysis"],
            "result_ids": [r["id"] for r in first_data["results"]],
        },
    ]

    second = client.post(
        "/assistant",
        json={"message": "من هالاغاني، اختار اول اغنية", "limit": 5, "history": history},
    )
    assert second.status_code == 200
    second_data = second.json()

    assert second_data["analysis"]["intent"] == "follow_up"
    first_result_id = first_data["results"][0]["id"]
    assert [r["id"] for r in second_data["results"]] == [first_result_id]


def test_follow_up_phrasing_without_history_does_not_use_follow_up_route(client, db_session):
    _seed_maqam_songs(db_session)

    response = client.post(
        "/assistant",
        json={"message": "من هالاغاني، اختار اول اغنية", "limit": 5, "history": []},
    )

    assert response.status_code == 200
    data = response.json()
    # No prior turn in THIS conversation -- must not be treated as a
    # follow-up referencing another conversation's results.
    assert data["analysis"]["intent"] != "follow_up"


def test_independent_conversations_do_not_bleed(client, db_session):
    maqam, _ = _seed_maqam_songs(db_session)

    conversation_a = client.post(
        "/assistant",
        json={"message": f"اعطيني اغاني على مقام {maqam.name_ar}", "limit": 5, "history": []},
    ).json()

    # A second, unrelated conversation starting fresh must not see
    # conversation A's results just because the server process is shared.
    conversation_b = client.post(
        "/assistant",
        json={"message": "من هالاغاني، اختار اول اغنية", "limit": 5, "history": []},
    ).json()

    assert conversation_b["analysis"]["intent"] != "follow_up"
    # With an empty `history`, conversation B can structurally never see
    # conversation A's song ids -- nothing is kept server-side between
    # requests (see app/ai/conversation.py's module docstring).
    conversation_a_ids = {r["id"] for r in conversation_a["results"]}
    conversation_b_ids = {r["id"] for r in conversation_b.get("results", [])}
    assert not (conversation_a_ids & conversation_b_ids)
