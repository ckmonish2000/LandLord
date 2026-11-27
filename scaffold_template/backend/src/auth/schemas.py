from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.auth.constants import PASSWORD_MIN_LENGTH


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)
    name: str = Field(min_length=1, max_length=200)


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """A user as the API shows it: never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        """SQLite drops the time zone; every stored time is UTC, so say so in the response."""
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value
