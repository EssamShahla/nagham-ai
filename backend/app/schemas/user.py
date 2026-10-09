from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    instrument: str

    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    music_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    bio: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    instrument: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    music_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    bio: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]):
        if value is None:
            return value

        clean = value.strip()

        if not clean:
            raise ValueError("Name cannot be empty")

        return clean


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    instrument: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    music_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    bio: Optional[str] = None
    is_verified: bool
    profile_completed: bool
    auth_provider: str
    role: str

    class Config:
        from_attributes = True
        
    
class ResendOTPRequest(BaseModel):
    email: EmailStr