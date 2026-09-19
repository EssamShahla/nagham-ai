from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.rhythm import Rhythm
from app.schemas.rhythm import RhythmCreate, RhythmResponse
from app.core.security import require_admin
from app.models.user import User


router = APIRouter(
    prefix="/rhythms",
    tags=["Rhythms"]
)


@router.post(
    "",
    response_model=RhythmResponse,
    status_code=status.HTTP_201_CREATED
)
def create_rhythm(
    rhythm_data: RhythmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    clean_name_ar = rhythm_data.name_ar.strip()

    if not clean_name_ar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arabic rhythm name cannot be empty"
        )

    existing_rhythm = (
        db.query(Rhythm)
        .filter(
            func.lower(Rhythm.name_ar)
            == clean_name_ar.lower()
        )
        .first()
    )

    if existing_rhythm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rhythm already exists"
        )

    if rhythm_data.sample_bpm is not None:
        if rhythm_data.sample_bpm <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sample BPM must be greater than 0"
            )

        if rhythm_data.sample_bpm > 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sample BPM must not exceed 400"
            )

    rhythm = Rhythm(
        name_ar=clean_name_ar,
        name_en=(
            rhythm_data.name_en.strip()
            if rhythm_data.name_en
            else None
        ),
        time_signature=rhythm_data.time_signature,
        pattern_text=rhythm_data.pattern_text,
        notation_format=rhythm_data.notation_format,
        musicxml_data=rhythm_data.musicxml_data,
        audio_sample_url=rhythm_data.audio_sample_url,
        sample_bpm=rhythm_data.sample_bpm,
        description=rhythm_data.description,
        notes=rhythm_data.notes,
    )

    try:
        db.add(rhythm)
        db.commit()
        db.refresh(rhythm)

        return rhythm

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rhythm"
        )


@router.get(
    "",
    response_model=list[RhythmResponse]
)
def get_rhythms(
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Rhythm)

    if search:
        clean_search = search.strip()

        query = query.filter(
            Rhythm.name_ar.ilike(
                f"%{clean_search}%"
            )
        )

    return (
        query
        .order_by(Rhythm.name_ar.asc())
        .all()
    )


@router.get(
    "/{rhythm_id}",
    response_model=RhythmResponse
)
def get_rhythm(
    rhythm_id: int,
    db: Session = Depends(get_db)
):
    rhythm = (
        db.query(Rhythm)
        .filter(Rhythm.id == rhythm_id)
        .first()
    )

    if not rhythm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rhythm not found"
        )

    return rhythm