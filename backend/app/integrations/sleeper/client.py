from .config import SleeperConfig
from .auth import SleeperAuth
from .transport import SleeperTransport
from .limiter import TokenBucket
from .read import SleeperRead
from .write import SleeperWrite


class SleeperClient:
    def __init__(
        self,
        *,
        transport: SleeperTransport,
        auth: SleeperAuth,
        limiter: TokenBucket,
        config: SleeperConfig,
    ):
        self.transport = transport
        self.auth = auth
        self.limiter = limiter
        self.config = config

        self.read = SleeperRead(
            self.transport,
        )

        self.write = SleeperWrite(
            self.transport,
            self.auth,
        )

    @property
    def token(self) -> str | None:
        return self.auth.token

    @property
    def can_write(self) -> bool:
        return self.auth.is_authenticated()

    def with_token(
        self,
        token: str,
    ) -> "SleeperClient":
        auth = SleeperAuth(
            token,
        )

        transport = SleeperTransport(
            auth=auth,
            http=self.transport.http,
            limiter=self.limiter,
            config=self.config,
        )

        return SleeperClient(
            transport=transport,
            auth=auth,
            limiter=self.limiter,
            config=self.config,
        )

    def without_token(
        self,
    ) -> "SleeperClient":
        auth = SleeperAuth()

        transport = SleeperTransport(
            auth=auth,
            http=self.transport.http,
            limiter=self.limiter,
            config=self.config,
        )

        return SleeperClient(
            transport=transport,
            auth=auth,
            limiter=self.limiter,
            config=self.config,
        )

    def debug_state(self) -> dict:
        return {
            "has_token": bool(self.token),
            "can_write": self.can_write,
            "rate_limit": self.limiter.capacity,
        }