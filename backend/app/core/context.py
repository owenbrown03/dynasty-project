from dataclasses import dataclass
from typing import Optional
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.auth import SiteUser, UserSession
from app.models.db.sleeper.connection import SleeperConnection
from app.integrations.sleeper.client import SleeperClient
from app.infrastructure.redis.client import RedisClient


@dataclass
class Context:
    response: Response
    db: AsyncSession
    session: UserSession
    site_user: Optional[SiteUser]
    connection: Optional[SleeperConnection]
    sleeper: Optional[SleeperClient]
    redis: Optional[RedisClient]

    @property
    def is_authenticated(self) -> bool:
        return self.site_user is not None or self.session is not None

    @property
    def can_write(self) -> bool:
        if not self.connection:
            return False
        token = self.connection.encrypted_token
        return bool(token and token.strip())

    @property
    def sleeper_user_id(self) -> Optional[str]:
        if not self.connection:
            return None
        return self.connection.sleeper_user_id