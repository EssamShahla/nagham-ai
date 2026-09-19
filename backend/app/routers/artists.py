from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database.connection import get_db
from app.models.artist import Artist
from app.models.user import User
from app.schemas.artist import ArtistCreate, ArtistResponse
from app.core.security import get_current_user


router = APIRouter(
    prefix="/artists",
    tags=["Artists"]
)


@router.post(
    "",
    response_model=ArtistResponse,
    status_code=status.HTTP_201_CREATED
)
def create_artist(
    artist_data: ArtistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    clean_name_ar = artist_data.name_ar.strip()

    if not clean_name_ar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arabic artist name is required"
        )

    existing_artist = (
        db.query(Artist)
        .filter(func.lower(Artist.name_ar) == clean_name_ar.lower())
        .first()
    )

    if existing_artist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Artist already exists"
        )

    new_artist = Artist(
        name_ar=clean_name_ar,
        name_en=artist_data.name_en.strip() if artist_data.name_en else None,
        bio=artist_data.bio.strip() if artist_data.bio else None
    )

    db.add(new_artist)
    db.commit()
    db.refresh(new_artist)

    return new_artist


@router.get(
    "",
    response_model=list[ArtistResponse]
)
def get_artists(
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Artist)

    if search:
        clean_search = search.strip()

        if clean_search:
            query = query.filter(
                Artist.name_ar.ilike(f"%{clean_search}%")
            )

    artists = (
        query
        .order_by(Artist.name_ar.asc())
        .all()
    )

    return artists