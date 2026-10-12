from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database.connection import get_db

from app.models.maqam import Maqam
from app.models.ajnas import Jins
from app.models.user import User

from app.schemas.maqam import (
    MaqamCreate,
    MaqamResponse,
)

from app.core.security import require_admin


router = APIRouter(
    prefix="/maqamat",
    tags=["Maqamat"]
)


@router.post(
    "",
    response_model=MaqamResponse,
    status_code=status.HTTP_201_CREATED
)
def create_maqam(
    maqam_data: MaqamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    clean_name_ar = maqam_data.name_ar.strip()

    if not clean_name_ar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arabic maqam name cannot be empty"
        )

    clean_name_en = (
        maqam_data.name_en.strip()
        if maqam_data.name_en and maqam_data.name_en.strip()
        else None
    )

    duplicate_filters = [
        func.lower(Maqam.name_ar) == clean_name_ar.lower()
    ]

    if clean_name_en:
        duplicate_filters.append(
            func.lower(Maqam.name_en) == clean_name_en.lower()
        )

    existing_maqam = (
        db.query(Maqam)
        .filter(or_(*duplicate_filters))
        .first()
    )

    if existing_maqam:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Maqam already exists"
        )

    if maqam_data.root_jins_id is not None:
        root_jins = (
            db.query(Jins)
            .filter(
                Jins.id == maqam_data.root_jins_id
            )
            .first()
        )

        if not root_jins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Root jins not found"
            )

    if maqam_data.branch_jins_id is not None:
        branch_jins = (
            db.query(Jins)
            .filter(
                Jins.id == maqam_data.branch_jins_id
            )
            .first()
        )

        if not branch_jins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch jins not found"
            )

    maqam = Maqam(
        name_ar=clean_name_ar,

        name_en=clean_name_en,

        tonic=maqam_data.tonic,
        accidentals=maqam_data.accidentals,

        scale_pattern=maqam_data.scale_pattern,
        degree_names=maqam_data.degree_names,

        root_jins_id=maqam_data.root_jins_id,
        branch_jins_id=maqam_data.branch_jins_id,

        ghammaz=maqam_data.ghammaz,
        mood=maqam_data.mood,

        notation_format=maqam_data.notation_format,
        musicxml_data=maqam_data.musicxml_data,
        audio_sample_url=maqam_data.audio_sample_url,

        description=maqam_data.description,
        notes=maqam_data.notes,
    )

    try:
        db.add(maqam)
        db.commit()
        db.refresh(maqam)

        return maqam

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create maqam"
        )


@router.get(
    "",
    response_model=list[MaqamResponse]
)
def get_maqamat(
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Maqam)

    if search:
        clean_search = search.strip()

        query = query.filter(
            or_(
                Maqam.name_ar.ilike(
                    f"%{clean_search}%"
                ),
                Maqam.name_en.ilike(
                    f"%{clean_search}%"
                )
            )
        )

    return (
        query
        .order_by(Maqam.name_ar.asc())
        .all()
    )


@router.get(
    "/{maqam_id}",
    response_model=MaqamResponse
)
def get_maqam(
    maqam_id: int,
    db: Session = Depends(get_db)
):
    maqam = (
        db.query(Maqam)
        .filter(Maqam.id == maqam_id)
        .first()
    )

    if not maqam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maqam not found"
        )

    return maqam