"""
Shared song-creation business logic.

Used by both the REST `POST /songs` endpoint (app/routers/songs.py) and
the AI agent's conversational song-creation flow
(app/ai/song_creation.py), so validation, duplicate-detection, and
embedding-generation rules live in exactly one place instead of being
duplicated between the two callers.

Raises plain Python exceptions (never `HTTPException`) so both an HTTP
router and a LangGraph node can translate failures into whatever response
shape they need.
"""

from typing import Optional, TypedDict, Literal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.artist import Artist
from app.models.composer import Composer
from app.models.maqam import Maqam
from app.models.rhythm import Rhythm
from app.models.song import Song
from app.ai.semantic_search import build_song_embedding_text, generate_embedding


class ArtistNotFoundError(Exception):
    pass


class ComposerNotFoundError(Exception):
    pass


class RhythmNotFoundError(Exception):
    pass


class MaqamNotFoundError(Exception):
    pass


class DuplicateSongError(Exception):
    """Raised with the pre-existing song that matches title+artist."""

    def __init__(self, existing_song: Song):
        self.existing_song = existing_song
        super().__init__(f"Song already exists (id={existing_song.id})")


class EntityChoice(TypedDict):
    kind: Literal["existing", "new"]
    id: Optional[int]
    name: Optional[str]


def ensure_artist_exists(db: Session, artist_id: int) -> None:
    if db.query(Artist).filter(Artist.id == artist_id).first() is None:
        raise ArtistNotFoundError(f"Artist {artist_id} not found")


def ensure_composer_exists(db: Session, composer_id: int) -> None:
    if db.query(Composer).filter(Composer.id == composer_id).first() is None:
        raise ComposerNotFoundError(f"Composer {composer_id} not found")


def ensure_rhythm_exists(db: Session, rhythm_id: int) -> None:
    if db.query(Rhythm).filter(Rhythm.id == rhythm_id).first() is None:
        raise RhythmNotFoundError(f"Rhythm {rhythm_id} not found")


def ensure_maqam_exists(db: Session, maqam_id: int) -> None:
    if db.query(Maqam).filter(Maqam.id == maqam_id).first() is None:
        raise MaqamNotFoundError(f"Maqam {maqam_id} not found")


def find_duplicate_song(
    db: Session,
    title: str,
    artist_id: int,
    exclude_id: Optional[int] = None,
) -> Optional[Song]:
    query = db.query(Song).filter(
        func.lower(Song.title) == title.lower(),
        Song.artist_id == artist_id,
    )

    if exclude_id is not None:
        query = query.filter(Song.id != exclude_id)

    return query.first()


def _generate_song_embedding(db: Session, song: Song) -> None:
    db.flush()
    db.refresh(song)

    song = (
        db.query(Song)
        .options(
            joinedload(Song.artist),
            joinedload(Song.composer),
            joinedload(Song.rhythm),
            joinedload(Song.maqam),
        )
        .filter(Song.id == song.id)
        .one()
    )

    embedding_text = build_song_embedding_text(song)
    song.embedding = generate_embedding(embedding_text)


def _verify_persisted(db: Session, song_id: int) -> Song:
    """
    Re-query by id in a fresh query (not the in-memory object the ORM
    handed back) so a caller never reports success on a write that didn't
    actually persist.
    """

    verified = (
        db.query(Song)
        .options(
            joinedload(Song.artist),
            joinedload(Song.composer),
            joinedload(Song.rhythm),
            joinedload(Song.maqam),
        )
        .filter(Song.id == song_id)
        .first()
    )

    if verified is None:
        raise RuntimeError(
            f"Song {song_id} could not be verified after commit"
        )

    return verified


def regenerate_song_embedding(db: Session, song: Song) -> None:
    """Public wrapper for `update_song`-style callers that already have a
    `Song` instance and just need its embedding refreshed."""

    _generate_song_embedding(db, song)


def create_song_and_embed(
    db: Session,
    *,
    title: str,
    artist_id: int,
    composer_id: Optional[int] = None,
    rhythm_id: Optional[int] = None,
    maqam_id: Optional[int] = None,
    lyrics: Optional[str] = None,
    lyricist_name: Optional[str] = None,
    musical_key: Optional[str] = None,
    description: Optional[str] = None,
    moods: Optional[list[str]] = None,
    topics: Optional[list[str]] = None,
    year: Optional[int] = None,
    difficulty: Optional[str] = None,
    created_by: int,
) -> Song:
    """
    Create a song referencing entities that already exist by id -- the
    path used by the REST `/songs` endpoint, which has no concept of
    "create a new artist inline".
    """

    try:
        ensure_artist_exists(db, artist_id)

        if composer_id is not None:
            ensure_composer_exists(db, composer_id)
        if rhythm_id is not None:
            ensure_rhythm_exists(db, rhythm_id)
        if maqam_id is not None:
            ensure_maqam_exists(db, maqam_id)

        duplicate = find_duplicate_song(db, title, artist_id)
        if duplicate is not None:
            raise DuplicateSongError(duplicate)

        new_song = Song(
            title=title,
            lyrics=lyrics,
            lyricist_name=lyricist_name,
            musical_key=musical_key,
            description=description,
            moods=moods,
            topics=topics,
            year=year,
            difficulty=difficulty,
            artist_id=artist_id,
            composer_id=composer_id,
            rhythm_id=rhythm_id,
            maqam_id=maqam_id,
            created_by=created_by,
        )
        db.add(new_song)
        _generate_song_embedding(db, new_song)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _verify_persisted(db, new_song.id)


def _resolve_or_create_entity(
    db: Session,
    model,
    choice: Optional[EntityChoice],
    not_found_error,
) -> Optional[int]:
    if choice is None:
        return None

    if choice["kind"] == "existing":
        entity_id = choice["id"]
        if db.query(model).filter(model.id == entity_id).first() is None:
            raise not_found_error(
                f"{model.__name__} {entity_id} no longer exists"
            )
        return entity_id

    # "new" -- re-check for a same-named row created since collection
    # (e.g. by another request) rather than creating a duplicate catalog
    # entry; otherwise insert it now, in the same uncommitted transaction
    # as the Song it belongs to.
    name = choice["name"].strip()
    existing = (
        db.query(model).filter(func.lower(model.name_ar) == name.lower()).first()
    )
    if existing is not None:
        return existing.id

    new_entity = model(name_ar=name)
    db.add(new_entity)
    db.flush()
    return new_entity.id


def create_song_with_staged_entities(
    db: Session,
    *,
    title: str,
    artist_choice: EntityChoice,
    composer_choice: Optional[EntityChoice] = None,
    rhythm_id: Optional[int] = None,
    maqam_id: Optional[int] = None,
    lyricist_name: Optional[str] = None,
    musical_key: Optional[str] = None,
    description: Optional[str] = None,
    moods: Optional[list[str]] = None,
    topics: Optional[list[str]] = None,
    year: Optional[int] = None,
    difficulty: Optional[str] = None,
    created_by: int,
) -> Song:
    """
    The path the conversational song-creation flow calls at final
    confirmation only. `artist_choice`/`composer_choice` are tagged
    unions resolved during collection -- never a bare id assumed to still
    exist. Any new Artist/Composer row, the duplicate re-check, and the
    Song insert all happen in ONE transaction: any failure anywhere rolls
    back everything, so a new artist is never left orphaned without its
    song.
    """

    try:
        artist_id = _resolve_or_create_entity(
            db, Artist, artist_choice, ArtistNotFoundError
        )
        composer_id = _resolve_or_create_entity(
            db, Composer, composer_choice, ComposerNotFoundError
        )

        if rhythm_id is not None:
            ensure_rhythm_exists(db, rhythm_id)
        if maqam_id is not None:
            ensure_maqam_exists(db, maqam_id)

        # Re-checked fresh here (not trusted from collection time) --
        # another request could have created a matching song in between.
        duplicate = find_duplicate_song(db, title, artist_id)
        if duplicate is not None:
            raise DuplicateSongError(duplicate)

        new_song = Song(
            title=title,
            lyricist_name=lyricist_name,
            musical_key=musical_key,
            description=description,
            moods=moods,
            topics=topics,
            year=year,
            difficulty=difficulty,
            artist_id=artist_id,
            composer_id=composer_id,
            rhythm_id=rhythm_id,
            maqam_id=maqam_id,
            created_by=created_by,
        )
        db.add(new_song)
        _generate_song_embedding(db, new_song)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _verify_persisted(db, new_song.id)
