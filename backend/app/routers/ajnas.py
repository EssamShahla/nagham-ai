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

from app.models.ajnas import Jins
from app.models.user import User

from app.schemas.ajnas import (
    JinsCreate,
    JinsResponse,
)

from app.core.security import require_admin


router = APIRouter(
    prefix="/ajnas",
    tags=["Ajnas"]
)


@router.post(
    "",
    response_model=JinsResponse,
    status_code=status.HTTP_201_CREATED
)
def create_jins(
    jins_data: JinsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    clean_name_ar = jins_data.name_ar.strip()

    if not clean_name_ar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arabic jins name cannot be empty"
        )

    clean_name_en = (
        jins_data.name_en.strip()
        if jins_data.name_en and jins_data.name_en.strip()
        else None
    )

    duplicate_filters = [
        func.lower(Jins.name_ar) == clean_name_ar.lower()
    ]

    if clean_name_en:
        duplicate_filters.append(
            func.lower(Jins.name_en) == clean_name_en.lower()
        )

    existing_jins = (
        db.query(Jins)
        .filter(or_(*duplicate_filters))
        .first()
    )

    if existing_jins:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Jins already exists"
        )

    jins = Jins(
        name_ar=clean_name_ar,

        name_en=clean_name_en,

        tonic=jins_data.tonic,
        accidentals=jins_data.accidentals,

        scale_pattern=jins_data.scale_pattern,

        description=jins_data.description,
        notes=jins_data.notes,
    )

    try:
        db.add(jins)
        db.commit()
        db.refresh(jins)

        return jins

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create jins"
        )


@router.get(
    "",
    response_model=list[JinsResponse]
)
def get_ajnas(
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Jins)

    if search:
        clean_search = search.strip()

        query = query.filter(
            or_(
                Jins.name_ar.ilike(
                    f"%{clean_search}%"
                ),
                Jins.name_en.ilike(
                    f"%{clean_search}%"
                )
            )
        )

    return (
        query
        .order_by(Jins.name_ar.asc())
        .all()
    )


@router.get(
    "/{jins_id}",
    response_model=JinsResponse
)
def get_jins(
    jins_id: int,
    db: Session = Depends(get_db)
):
    jins = (
        db.query(Jins)
        .filter(Jins.id == jins_id)
        .first()
    )

    if not jins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jins not found"
        )

    return jins