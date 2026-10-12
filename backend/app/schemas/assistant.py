from typing import Any
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """
    One turn of prior conversation. The client (frontend or eval harness)
    holds the conversation and resends recent turns with each request --
    nothing here is persisted server-side. See app/ai/conversation.py.
    """

    role: str
    content: str
    analysis: dict[str, Any] | None = None
    result_ids: list[int] | None = None


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=10)
    history: list[ConversationTurn] = Field(default_factory=list)


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