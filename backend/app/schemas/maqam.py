from typing import Optional, Literal

from pydantic import BaseModel, field_validator

MAX_SCALE_INTERVAL = 4.0


class MaqamCreate(BaseModel):
    name_ar: str
    name_en: Optional[str] = None

    tonic: Optional[str] = None
    accidentals: Optional[str] = None

    scale_pattern: Optional[list[float]] = None

    root_jins_id: Optional[int] = None
    branch_jins_id: Optional[int] = None

    ghammaz: Optional[str] = None
    mood: Optional[str] = None

    notation_format: Literal["musicxml"] = "musicxml"

    musicxml_data: Optional[str] = None
    audio_sample_url: Optional[str] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("scale_pattern")
    @classmethod
    def validate_scale_pattern(
        cls,
        value: Optional[list[float]]
    ):
        if value is None:
            return value

        if len(value) == 0:
            raise ValueError(
                "Scale pattern cannot be empty"
            )

        if any(interval <= 0 for interval in value):
            raise ValueError(
                "Scale intervals must be greater than 0"
            )

        if any(interval > MAX_SCALE_INTERVAL for interval in value):
            raise ValueError(
                f"Scale intervals must not exceed {MAX_SCALE_INTERVAL}"
            )

        return value


class MaqamResponse(BaseModel):
    id: int

    name_ar: str
    name_en: Optional[str] = None

    tonic: Optional[str] = None
    accidentals: Optional[str] = None

    scale_pattern: Optional[list[float]] = None

    root_jins_id: Optional[int] = None
    branch_jins_id: Optional[int] = None

    ghammaz: Optional[str] = None
    mood: Optional[str] = None

    notation_format: str

    musicxml_data: Optional[str] = None
    audio_sample_url: Optional[str] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True