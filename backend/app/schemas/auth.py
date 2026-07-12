from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.base import Base
from app.services.values.basis import ValueBasis

class Login(Base):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class AuthSessionResponse(Base):
    authenticated: bool
    user_id: str | None = None


class EmailVerificationStatusResponse(Base):
    email_verified: bool
    verification_email_sent_at: datetime | None = None


class EmailVerificationRequestResponse(Base):
    email_verified: bool
    verification_email_sent_at: datetime | None = None
    delivery: Literal["smtp", "log"]


class EmailVerificationConfirmRequest(Base):
    token: str


class ThemePreferenceUpdate(Base):
    theme_preference: Literal["light", "dark", "system"]


class ThemePreferenceResponse(Base):
    theme_preference: Literal["light", "dark", "system"] | None


class ValuePreferenceUpdate(Base):
    value_preference: ValueBasis


class ValuePreferenceResponse(Base):
    value_preference: ValueBasis | None
