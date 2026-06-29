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
            self.transport
        )

        self.write = SleeperWrite(
            self.transport,
            self.auth,
        )

    @property
    def token(self):
        return self.auth.token

    def debug_state(self):
        return {
            "has_token": bool(self.token),
            "rate_limit": self.limiter.capacity,
        }