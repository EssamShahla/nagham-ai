from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.composer import Composer
from app.models.user import User
from app.schemas.composer import ComposerCreate, ComposerResponse
from app.core.security import get_current_user


router = APIRouter(
    prefix="/composers",
    tags=["Composers"]
)


@router.post(
    "",
    response_model=ComposerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_composer(
    composer_data: ComposerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_name_ar = composer_data.name_ar.strip()

    if not clean_name_ar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arabic composer name is required"
        )

    existing_composer = (
        db.query(Composer)
        .filter(
            func.lower(Composer.name_ar) == clean_name_ar.lower()
        )
        .first()
    )

    if existing_composer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Composer already exists"
        )

    new_composer = Composer(
        name_ar=clean_name_ar,
        name_en=(
            composer_data.name_en.strip()
            if composer_data.name_en
            else None
        ),
        bio=(
            composer_data.bio.strip()
            if composer_data.bio
            else None
        )
    )

    db.add(new_composer)
    db.commit()
    db.refresh(new_composer)

    return new_composer


@router.get(
    "",
    response_model=list[ComposerResponse]
)
def get_composers(
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Composer)

    if search:
        clean_search = search.strip()

        if clean_search:
            query = query.filter(
                Composer.name_ar.ilike(f"%{clean_search}%")
            )

    composers = (
        query
        .order_by(Composer.name_ar.asc())
        .all()
    )

    return composers