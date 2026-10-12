"""
Regression tests for the lyrics_request intent (app/ai/conversation.py).

Covers the reported bug: a lyrics request ("هاتلي كلمات انت عمري") must
resolve the exact song title and respect `lyrics_license`, never fall back
to an unrelated semantic recommendation.
"""

from tests.conftest import unique_email

from app.models.artist import Artist
from app.models.song import Song
from app.models.user import User


def _make_user(db_session) -> User:
    user = User(name="Test Author", email=unique_email())
    db_session.add(user)
    db_session.commit()
    return user


def _make_artist(db_session, name_ar: str) -> Artist:
    artist = Artist(name_ar=name_ar)
    db_session.add(artist)
    db_session.commit()
    return artist


def test_lyrics_request_restricted_song_hides_text(client, db_session):
    user = _make_user(db_session)
    artist = _make_artist(db_session, "أم كلثوم")

    song = Song(
        title="انت عمري",
        lyrics="رجعوني عينيك لأيامي اللي راحوا",
        lyrics_license="restricted",
        lyrics_rights_note="حقوق محفوظة، لا يوجد ترخيص عرض",
        artist_id=artist.id,
        created_by=user.id,
    )
    db_session.add(song)
    db_session.commit()

    response = client.post("/assistant", json={"message": "هاتلي كلمات انت عمري", "limit": 5})

    assert response.status_code == 200
    data = response.json()

    assert data["analysis"]["intent"] == "lyrics_request"
    assert [r["id"] for r in data["results"]] == [song.id]
    # The restricted lyrics text must never be leaked verbatim.
    assert "رجعوني عينيك" not in data["answer"]
    assert "حقوق النشر" in data["answer"]
    # Must not fall back to an unrelated recommendation.
    assert data["results"][0]["title"] == "انت عمري"


def test_lyrics_request_licensed_song_returns_full_text(client, db_session):
    user = _make_user(db_session)
    artist = _make_artist(db_session, "شاعر تراثي")

    song = Song(
        title="موشح قديم",
        lyrics="يا ليل الصب متى غده",
        lyrics_license="public_domain",
        lyrics_rights_note="نص تراثي من الملك العام",
        artist_id=artist.id,
        created_by=user.id,
    )
    db_session.add(song)
    db_session.commit()

    response = client.post("/assistant", json={"message": "كلمات موشح قديم", "limit": 5})

    assert response.status_code == 200
    data = response.json()

    assert data["analysis"]["intent"] == "lyrics_request"
    assert "يا ليل الصب متى غده" in data["answer"]


def test_lyrics_request_unknown_title_returns_not_found(client, db_session):
    _make_user(db_session)

    response = client.post(
        "/assistant",
        json={"message": "عطيني كلمات اغنية مش موجودة خالص بالدنيا", "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["analysis"]["intent"] == "lyrics_request"
    assert data["results"] == []
    assert "لم أجد" in data["answer"]
