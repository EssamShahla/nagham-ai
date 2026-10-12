from typing import Optional

from pydantic import BaseModel, field_validator

MAX_SCALE_INTERVAL = 4.0


class JinsCreate(BaseModel):
    name_ar: str
    name_en: Optional[str] = None

    tonic: Optional[str] = None
    accidentals: Optional[str] = None

    scale_pattern: Optional[list[float]] = None
    degree_names: Optional[list[str]] = None

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


class JinsResponse(BaseModel):
    id: int

    name_ar: str
    name_en: Optional[str] = None

    tonic: Optional[str] = None
    accidentals: Optional[str] = None

    scale_pattern: Optional[list[float]] = None
    degree_names: Optional[list[str]] = None

    description: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True