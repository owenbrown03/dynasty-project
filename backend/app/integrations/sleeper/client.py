import asyncio
import httpx

from .config import SleeperConfig
from .auth import SleeperAuth
from .http import HTTPTransport
from .transport import SleeperTransport
from .limiter import TokenBucket
from .read import SleeperRead
from .write import SleeperWrite


class SleeperClient:
    def __init__(
        self,
        *,
        http: HTTPTransport,
        limiter: TokenBucket,
        config: SleeperConfig,
        token: str | None = None,
    ):
        self.http = http
        self.limiter = limiter
        self.config = config

        self.auth = SleeperAuth(token)

        self.transport = SleeperTransport(
            auth=self.auth,
            http=self.http,
            limiter=self.limiter,
            config=self.config,
        )

        self.read = SleeperRead(self.transport)
        self.write = SleeperWrite(
            self.transport,
            self.auth,
        )

    @property
    def token(self) -> str | None:
        return self.auth.token

    def with_token(
        self,
        token: str,
    ) -> "SleeperClient":
        return SleeperClient(
            http=self.http,
            limiter=self.limiter,
            config=self.config,
            token=token,
        )

    def without_token(self) -> "SleeperClient":
        return SleeperClient(
            http=self.http,
            limiter=self.limiter,
            config=self.config,
        )

    def debug_state(self) -> dict:
        return {
            "has_token": bool(self.token),
            "rate_limit": f"{self.limiter.capacity}/sec",
        }