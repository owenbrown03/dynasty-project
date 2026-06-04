import httpx

from .config import SleeperConfig
from .auth import SleeperAuth
from .auth_api import SleeperAuthAPI
from .http import HTTPTransport
from .transport import SleeperTransport
from .limiter import TokenBucket
from .read import SleeperRead
from .write import SleeperWrite

class SleeperClientManager:
    _client = None

    @classmethod
    def get(cls):
        if cls._client is None:
            cls._client = SleeperClient()
        return cls._client
    
class SleeperClient:
    def __init__(
        self,
        token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.auth = SleeperAuth(token)

        self._owns_client = http_client is None

        self._http_client = (
            http_client
            or httpx.AsyncClient(
                timeout=httpx.Timeout(
                    10.0,
                    connect=5.0,
                )
            )
        )

        self.http = HTTPTransport(self._http_client)

        self.limiter = TokenBucket(
            rate=20,
            per=1.0,
        )

        self.config = SleeperConfig()

        self.transport = SleeperTransport(
            auth=self.auth,
            http=self.http,
            limiter=self.limiter,
            config=self.config,
        )

        self.auth_api = SleeperAuthAPI(
            self._http_client
        )

        self.read = SleeperRead(self.transport)
        self.write = SleeperWrite(self.transport)

    # -----------------------
    # Token helpers
    # -----------------------

    @property
    def token(self) -> str | None:
        return self.auth.token

    def set_token(self, token: str | None):
        self.auth.set_token(token)

    def clear_token(self):
        self.auth.clear()

    # -----------------------
    # HTTP access (debugging)
    # -----------------------

    @property
    def http_client(self) -> httpx.AsyncClient:
        return self._http_client

    # -----------------------
    # Lifecycle
    # -----------------------

    async def close(self):
        if self._owns_client:
            await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()