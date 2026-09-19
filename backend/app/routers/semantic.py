from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ai.semantic_search import semantic_search_songs


router = APIRouter(
    prefix="/semantic-search",
    tags=["Semantic Search"]
)


@router.get("")
def search_songs_semantically(
    query: str = Query(..., min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        results = semantic_search_songs(
            db=db,
            query=query,
            limit=limit,
        )

        return {
            "query": query,
            "count": len(results),
            "results": [
                {
                    "id": result["song"].id,
                    "title": result["song"].title,
                    "artist_id": result["song"].artist_id,
                    "artist_name": (
                        result["song"].artist.name_ar
                        if result["song"].artist
                        else None
                    ),
                    "description": result["song"].description,
                    "moods": result["song"].moods,
                    "topics": result["song"].topics,
                    "maqam_id": result["song"].maqam_id,
                    "maqam_name": (
                        result["song"].maqam.name_ar
                        if result["song"].maqam
                        else None
                    ),
                    "similarity": round(result["similarity"], 4),
                }
                for result in results
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )