from typing import Literal, Optional

from app.schemas.base import Base
from app.services.values.basis import ValueBasis


class BootstrapUser(Base):
    id: str
    email: str


class BootstrapSleeper(Base):
    linked: bool
    sleeper_username: Optional[str] = None
    sleeper_user_id: Optional[str] = None
    can_read: bool = False
    can_write: bool = False


class BootstrapResponse(Base):
    authenticated: bool
    site_user: Optional[BootstrapUser] = None
    sleeper: BootstrapSleeper
    theme_preference: Literal["light", "dark", "system"] | None = None
    value_preference: ValueBasis | None = None
