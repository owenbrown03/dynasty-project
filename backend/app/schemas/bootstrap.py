from typing import Optional

from app.schemas.base import Base


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