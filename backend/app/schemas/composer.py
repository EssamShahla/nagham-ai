from typing import Optional

from pydantic import BaseModel


class ComposerCreate(BaseModel):
    name_ar: str
    name_en: Optional[str] = None
    bio: Optional[str] = None


class ComposerResponse(BaseModel):
    id: int
    name_ar: str
    name_en: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True