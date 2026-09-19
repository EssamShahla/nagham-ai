from typing import Optional, Literal

from pydantic import BaseModel, field_validator

from datetime import datetime

SongSourceType = Literal[
    "website",
    "book",
    "article",
    "database",
    "user_contribution",
    "other",
]


class SongSourceCreate(BaseModel):
    source_type: SongSourceType
    source_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    @field_validator("source_url", "title", "description")
    @classmethod
    def trim_optional_strings(cls, value: Optional[str]):
        if value is None:
            return None

        value = value.strip()

        return value if value else None


class SongSourceResponse(BaseModel):
    id: int
    song_id: int
    source_type: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True