from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ai.graph import nagham_graph
from app.schemas.assistant import (
    AssistantRequest,
    AssistantResponse,
    AssistantSongResult,
)


router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)


@router.post("", response_model=AssistantResponse)
def chat_with_assistant(
    request: AssistantRequest,
    db: Session = Depends(get_db),
):
    # Run the complete LangGraph agent
    graph_result = nagham_graph.invoke(
        {
            "user_message": request.message,
            "db": db,
            "limit": request.limit,
        }
    )

    # Convert SQLAlchemy Song objects into API-safe responses
    serialized_results = []

    for item in graph_result.get("results", []):
        song = item["song"]

        serialized_results.append(
            AssistantSongResult(
                id=song.id,
                title=song.title,
                artist=song.artist.name_ar if song.artist else None,
                maqam=song.maqam.name_ar if song.maqam else None,
                difficulty=song.difficulty,
                year=song.year,
                description=song.description,
                moods=song.moods,
                topics=song.topics,
                similarity=item.get("similarity"),
            )
        )

    return AssistantResponse(
        answer=graph_result["answer"],
        search_type=graph_result["search_type"],
        analysis=graph_result["analysis"],
        results=serialized_results,
    )