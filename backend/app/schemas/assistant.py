from typing import Any
from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


class AssistantSongResult(BaseModel):
    id: int
    title: str
    artist: str | None = None
    maqam: str | None = None
    difficulty: str | None = None
    year: int | None = None
    description: str | None = None
    moods: list[str] | None = None
    topics: list[str] | None = None
    similarity: float | None = None


class AssistantResponse(BaseModel):
    answer: str
    search_type: str
    analysis: dict[str, Any]
    results: list[AssistantSongResult]