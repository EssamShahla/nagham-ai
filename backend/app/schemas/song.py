from typing import Optional, Literal
from pydantic import BaseModel, field_validator, model_validator

from datetime import datetime

MIN_YEAR = 1800
MAX_TITLE_LENGTH = 255

SongDifficulty = Literal["easy", "medium", "hard"]


def _validate_title_value(value: str):
    clean = value.strip()

    if not clean:
        raise ValueError("Song title cannot be empty")

    if len(clean) > MAX_TITLE_LENGTH:
        raise ValueError(
            f"Song title is too long (max {MAX_TITLE_LENGTH} characters)"
        )

    return clean


def _validate_year_value(value: Optional[int]):
    if value is None:
        return value

    if value < MIN_YEAR or value > datetime.now().year:
        raise ValueError(
            f"Year must be between {MIN_YEAR} and the current year"
        )

    return value

def _validate_string_list(
    value: Optional[list[str]]
) -> Optional[list[str]]:
    if value is None:
        return None

    cleaned = []

    for item in value:
        item = item.strip()

        if item and item not in cleaned:
            cleaned.append(item)

    return cleaned


class SongCreate(BaseModel):
    title: str
    lyrics: Optional[str] = None
    description: Optional[str] = None
    moods: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    year: Optional[int] = None
    difficulty: Optional[SongDifficulty] = None

    artist_id: int
    composer_id: Optional[int] = None
    rhythm_id: Optional[int] = None
    maqam_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str):
        return _validate_title_value(value)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: Optional[int]):
        return _validate_year_value(value)
    
    @field_validator("moods", "topics")
    @classmethod
    def validate_string_lists(cls, value: Optional[list[str]]):
        return _validate_string_list(value)


class SongUpdate(BaseModel):
    title: Optional[str] = None
    lyrics: Optional[str] = None
    description: Optional[str] = None
    moods: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    year: Optional[int] = None
    difficulty: Optional[SongDifficulty] = None
    artist_id: Optional[int] = None
    composer_id: Optional[int] = None
    rhythm_id: Optional[int] = None
    maqam_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]):
        if value is None:
            raise ValueError("Song title cannot be set to null")

        return _validate_title_value(value)

    @field_validator("artist_id")
    @classmethod
    def validate_artist_id(cls, value: Optional[int]):
        if value is None:
            raise ValueError("Song artist cannot be set to null")

        return value

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: Optional[int]):
        return _validate_year_value(value)
    
    @field_validator("moods", "topics")
    @classmethod
    def validate_string_lists(cls, value: Optional[list[str]]):
        return _validate_string_list(value)


class SongResponse(BaseModel):
    id: int
    title: str
    lyrics: Optional[str] = None
    description: Optional[str] = None
    moods: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    year: Optional[int] = None
    difficulty: Optional[str] = None
    description: Optional[str] = None
    moods: Optional[list[str]] = None
    topics: Optional[list[str]] = None

    artist_id: int
    artist_name: str

    composer_id: Optional[int] = None
    composer_name: Optional[str] = None

    rhythm_id: Optional[int] = None
    rhythm_name: Optional[str] = None

    maqam_id: Optional[int] = None
    maqam_name: Optional[str] = None

    created_by: int

    @model_validator(mode="before")
    @classmethod
    def populate_display_names(cls, data):
        if isinstance(data, dict):
            return data

        return {
            "id": data.id,
            "title": data.title,
            "lyrics": data.lyrics,
            "description": data.description,
            "moods": data.moods,
            "topics": data.topics,
            "year": data.year,
            "difficulty": data.difficulty,
            "artist_id": data.artist_id,
            "artist_name": data.artist.name_ar if data.artist else None,
            "composer_id": data.composer_id,
            "composer_name": data.composer.name_ar if data.composer else None,
            "rhythm_id": data.rhythm_id,
            "rhythm_name": data.rhythm.name_ar if data.rhythm else None,
            "maqam_id": data.maqam_id,
            "maqam_name": data.maqam.name_ar if data.maqam else None,
            "created_by": data.created_by,
        }

    class Config:
        from_attributes = True


class SongListResponse(BaseModel):
    items: list[SongResponse]
    page: int
    page_size: int
    total: int
    pages: int