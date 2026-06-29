import httpx
from .config import KTCConfig
from .transport import KTCTransport
from .read import KTCRead


class KTCClient:
    def __init__(self, *, http: httpx.AsyncClient, config: KTCConfig | None = None):
        self.config = config or KTCConfig()
        self.transport = KTCTransport(http=http, config=self.config)
        self.read = KTCRead(self.transport)

    def debug_state(self) -> dict:
        return {
            "base_url": self.config.base_url,
            "pages_per_format": self.config.pages,
            "request_delay": self.config.request_delay,
        }
