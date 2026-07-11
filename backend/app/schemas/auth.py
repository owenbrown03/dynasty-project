from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.base import Base

class Login(Base):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class AuthSessionResponse(Base):
    authenticated: bool
    user_id: str | None = None


class ThemePreferenceUpdate(Base):
    theme_preference: Literal["light", "dark", "system"]


class ThemePreferenceResponse(Base):
    theme_preference: Literal["light", "dark", "system"] | None
