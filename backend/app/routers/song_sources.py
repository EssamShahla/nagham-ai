from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.song import Song
from app.models.song_source import SongSource
from app.models.user import User
from app.schemas.song_source import SongSourceCreate, SongSourceResponse
from app.core.security import get_current_user


router = APIRouter(
    tags=["Song Sources"]
)


def _get_song_or_404(db: Session, song_id: int) -> Song:
    song = db.query(Song).filter(Song.id == song_id).first()

    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found"
        )

    return song


def _get_source_or_404(db: Session, source_id: int) -> SongSource:
    source = (
        db.query(SongSource)
        .filter(SongSource.id == source_id)
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song source not found"
        )

    return source


@router.get(
    "/songs/{song_id}/sources",
    response_model=list[SongSourceResponse]
)
def get_song_sources(
    song_id: int,
    db: Session = Depends(get_db)
):
    _get_song_or_404(db, song_id)

    return (
        db.query(SongSource)
        .filter(SongSource.song_id == song_id)
        .order_by(SongSource.id.asc())
        .all()
    )


@router.post(
    "/songs/{song_id}/sources",
    response_model=SongSourceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_song_source(
    song_id: int,
    source_data: SongSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    song = _get_song_or_404(db, song_id)

    if song.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add sources to this song"
        )

    if source_data.source_url is not None:
        existing = (
            db.query(SongSource)
            .filter(
                SongSource.song_id == song_id,
                SongSource.source_url == source_data.source_url
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Song source already exists"
            )

    new_source = SongSource(
        song_id=song_id,
        source_type=source_data.source_type,
        source_url=source_data.source_url,
        title=source_data.title,
        description=source_data.description,
        created_by=current_user.id
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source


@router.delete(
    "/songs/{song_id}/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_song_source(
    song_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    source = _get_source_or_404(db, source_id)

    if source.song_id != song_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song source not found"
        )

    song = _get_song_or_404(db, song_id)

    is_song_creator = song.created_by == current_user.id
    is_source_creator = source.created_by == current_user.id
    is_admin = current_user.role == "admin"

    if not (is_song_creator or is_source_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this source"
        )

    db.delete(source)
    db.commit()

    return None