import math

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.song import Song
from app.models.user import User
from app.schemas.song import (
    SongCreate,
    SongUpdate,
    SongResponse,
    SongListResponse,
    SongDifficulty,
)
from app.core.security import get_current_user
from app.services.song_service import (
    ArtistNotFoundError,
    ComposerNotFoundError,
    RhythmNotFoundError,
    MaqamNotFoundError,
    DuplicateSongError,
    create_song_and_embed,
    ensure_artist_exists,
    ensure_composer_exists,
    ensure_rhythm_exists,
    ensure_maqam_exists,
    find_duplicate_song,
    regenerate_song_embedding,
)


router = APIRouter(
    prefix="/songs",
    tags=["Songs"]
)


def _get_song_or_404(db: Session, song_id: int) -> Song:
    song = (
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

    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found"
        )

    return song


def _ensure_can_manage_song(song: Song, current_user: User) -> None:
    if song.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this song"
        )


@router.post(
    "",
    response_model=SongResponse,
    status_code=status.HTTP_201_CREATED
)
def create_song(
    song_data: SongCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return create_song_and_embed(
            db,
            title=song_data.title,
            artist_id=song_data.artist_id,
            composer_id=song_data.composer_id,
            rhythm_id=song_data.rhythm_id,
            maqam_id=song_data.maqam_id,
            lyrics=song_data.lyrics.strip() if song_data.lyrics else None,
            description=(
                song_data.description.strip()
                if song_data.description
                else None
            ),
            moods=song_data.moods,
            topics=song_data.topics,
            year=song_data.year,
            difficulty=song_data.difficulty,
            created_by=current_user.id,
        )
    except ArtistNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
    except ComposerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Composer not found")
    except RhythmNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rhythm not found")
    except MaqamNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maqam not found")
    except DuplicateSongError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Song already exists")


@router.get(
    "",
    response_model=SongListResponse
)
def get_songs(
    search: Optional[str] = Query(default=None),
    artist_id: Optional[int] = Query(default=None),
    composer_id: Optional[int] = Query(default=None),
    rhythm_id: Optional[int] = Query(default=None),
    maqam_id: Optional[int] = Query(default=None),
    difficulty: Optional[SongDifficulty] = Query(default=None),
    year: Optional[int] = Query(default=None),
    created_by: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Song)

    if search:
        clean_search = search.strip()

        if clean_search:
            query = query.filter(Song.title.ilike(f"%{clean_search}%"))

    if artist_id is not None:
        query = query.filter(Song.artist_id == artist_id)

    if composer_id is not None:
        query = query.filter(Song.composer_id == composer_id)

    if rhythm_id is not None:
        query = query.filter(Song.rhythm_id == rhythm_id)

    if maqam_id is not None:
        query = query.filter(Song.maqam_id == maqam_id)

    if difficulty is not None:
        query = query.filter(Song.difficulty == difficulty)

    if year is not None:
        query = query.filter(Song.year == year)

    if created_by is not None:
        query = query.filter(Song.created_by == created_by)

    total = query.count()
    pages = math.ceil(total / page_size)

    songs = (
        query.order_by(Song.created_at.desc(), Song.id.desc())
        .options(
            joinedload(Song.artist),
            joinedload(Song.composer),
            joinedload(Song.rhythm),
            joinedload(Song.maqam),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return SongListResponse(
        items=songs,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages
    )


@router.get(
    "/{song_id}",
    response_model=SongResponse
)
def get_song(
    song_id: int,
    db: Session = Depends(get_db)
):
    return _get_song_or_404(db, song_id)


@router.patch(
    "/{song_id}",
    response_model=SongResponse
)
def update_song(
    song_id: int,
    song_data: SongUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    song = _get_song_or_404(db, song_id)

    _ensure_can_manage_song(song, current_user)

    updates = song_data.model_dump(exclude_unset=True)
    embedding_fields = {
        "title",
        "lyrics",
        "description",
        "moods",
        "topics",
        "artist_id",
        "composer_id",
        "maqam_id",
    }

    should_regenerate_embedding = bool(
        embedding_fields.intersection(updates.keys())
    )

    try:
        if "artist_id" in updates:
            ensure_artist_exists(db, updates["artist_id"])

        if (
            "composer_id" in updates
            and updates["composer_id"] is not None
        ):
            ensure_composer_exists(db, updates["composer_id"])

        if (
            "rhythm_id" in updates
            and updates["rhythm_id"] is not None
        ):
            ensure_rhythm_exists(db, updates["rhythm_id"])

        if (
            "maqam_id" in updates
            and updates["maqam_id"] is not None
        ):
            ensure_maqam_exists(db, updates["maqam_id"])
    except ArtistNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
    except ComposerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Composer not found")
    except RhythmNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rhythm not found")
    except MaqamNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maqam not found")

    if "title" in updates or "artist_id" in updates:
        prospective_title = updates.get("title", song.title)
        prospective_artist_id = updates.get("artist_id", song.artist_id)

        if find_duplicate_song(
            db,
            prospective_title,
            prospective_artist_id,
            exclude_id=song.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Song already exists"
            )

    if "title" in updates:
        song.title = updates["title"]

    if "lyrics" in updates:
        song.lyrics = (
            updates["lyrics"].strip()
            if updates["lyrics"]
            else None
        )
    
    if "description" in updates:
        song.description = (
            updates["description"].strip()
            if updates["description"]
            else None
        )

    if "moods" in updates:
        song.moods = updates["moods"]

    if "topics" in updates:
        song.topics = updates["topics"]

    if "year" in updates:
        song.year = updates["year"]

    if "difficulty" in updates:
        song.difficulty = updates["difficulty"]

    if "artist_id" in updates:
        song.artist_id = updates["artist_id"]

    if "composer_id" in updates:
        song.composer_id = updates["composer_id"]

    if "rhythm_id" in updates:
        song.rhythm_id = updates["rhythm_id"]

    if "maqam_id" in updates:
        song.maqam_id = updates["maqam_id"]

    if should_regenerate_embedding:
        regenerate_song_embedding(db, song)

    db.commit()
    db.refresh(song)

    return song


@router.delete(
    "/{song_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    song = _get_song_or_404(db, song_id)

    _ensure_can_manage_song(song, current_user)

    db.delete(song)
    db.commit()

    return None