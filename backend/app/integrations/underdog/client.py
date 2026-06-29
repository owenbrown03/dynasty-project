import httpx
from .auth import UnderdogAuth
from .config import UnderdogConfig
from .transport import UnderdogTransport
from .read import UnderdogRead


class UnderdogClient:
    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        config: UnderdogConfig | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ):
        self.config = config or UnderdogConfig()
        self.auth = UnderdogAuth(
            access_token=access_token,
            refresh_token=refresh_token,
            email=email,
            password=password,
        )
        self.transport = UnderdogTransport(
            http=http,
            auth=self.auth,
            config=self.config,
        )
        self.read = UnderdogRead(self.transport)

    def with_token(self, access_token: str, refresh_token: str | None = None) -> "UnderdogClient":
        return UnderdogClient(
            http=self.transport.http,
            config=self.config,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def debug_state(self) -> dict:
        return {
            "has_token": bool(self.auth.access_token),
            "token_expired": self.auth.is_expired(),
            "stats_base_url": self.config.stats_base_url,
        }
