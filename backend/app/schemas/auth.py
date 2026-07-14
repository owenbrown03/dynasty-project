from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.base import Base
from app.services.draft.projection import (
    DraftPickProjectionMethod,
    DraftPickProjectionPhaseMethod,
)
from app.services.values.basis import ValueBasis
from app.services.values.war_settings import (
    WarScope,
    WarTimeframe,
)

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
    verification_url: str | None = None


class EmailVerificationConfirmRequest(Base):
    token: str


class ThemePreferenceUpdate(Base):
    theme_preference: Literal["light", "dark", "system"]


class ThemePreferenceResponse(Base):
    theme_preference: Literal["light", "dark", "system"] | None


AccentColor = Literal[
    "blue", "green", "purple", "red", "orange", "teal", "pink",
]


class AccentColorUpdate(Base):
    accent_color: AccentColor


class AccentColorResponse(Base):
    accent_color: AccentColor | None


class ValuePreferenceUpdate(Base):
    value_preference: ValueBasis


class ValuePreferenceResponse(Base):
    value_preference: ValueBasis | None


class WarValueConfig(Base):
    timeframe: WarTimeframe = "dynasty"
    scope: WarScope = "roster"


class WarValueSettings(Base):
    sleeper_projection: WarValueConfig = Field(
        default_factory=WarValueConfig,
    )
    my: WarValueConfig = Field(
        default_factory=WarValueConfig,
    )


class WarValueSettingsUpdate(Base):
    settings: WarValueSettings


class WarValueSettingsResponse(Base):
    settings: WarValueSettings


class DraftPickProjectionSettings(Base):
    enabled: bool = True
    switch_week: int = Field(
        default=4,
        ge=1,
        le=18,
    )
    before_week_method: DraftPickProjectionPhaseMethod = "none"
    from_week_method: DraftPickProjectionMethod = "max_pf"


class DraftPickProjectionSettingsUpdate(Base):
    settings: DraftPickProjectionSettings


class DraftPickProjectionSettingsResponse(Base):
    settings: DraftPickProjectionSettings
