from app.schemas.base import Base

class SleeperConnectionResponse(Base):
    sleeper_user_id: str | None
    username: str | None
    can_read: bool
    can_write: bool