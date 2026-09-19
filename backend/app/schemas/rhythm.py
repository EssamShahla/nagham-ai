from typing import Optional, Literal
import re

from pydantic import BaseModel, field_validator


class RhythmCreate(BaseModel):
    name_ar: str
    name_en: Optional[str] = None

    time_signature: Optional[str] = None
    pattern_text: Optional[str] = None

    notation_format: Literal["musicxml"] = "musicxml"
    musicxml_data: Optional[str] = None

    audio_sample_url: Optional[str] = None
    sample_bpm: Optional[int] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("time_signature")
    @classmethod
    def validate_time_signature(
        cls,
        value: Optional[str]
    ):
        if value is None:
            return value

        pattern = re.compile(r"^\d{1,2}/\d{1,2}$")

        if not pattern.match(value.strip()):
            raise ValueError(
                "Time signature must be in the form of 'numerator/denominator', e.g. 4/4, 6/8"
            )

        numerator, denominator = value.strip().split("/")

        if int(numerator) <= 0 or int(denominator) <= 0:
            raise ValueError(
                "Time signature parts must be greater than 0"
            )

        return value.strip()


class RhythmResponse(BaseModel):
    id: int

    name_ar: str
    name_en: Optional[str] = None

    time_signature: Optional[str] = None
    pattern_text: Optional[str] = None

    notation_format: str
    musicxml_data: Optional[str] = None

    audio_sample_url: Optional[str] = None
    sample_bpm: Optional[int] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True