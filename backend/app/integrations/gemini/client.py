import httpx

from .config import GeminiConfig
from .transport import GeminiTransport
from .read import GeminiRead


class GeminiClient:

    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        config: GeminiConfig | None = None,
    ):
        self.config = config or GeminiConfig()

        self.transport = GeminiTransport(
            http=http,
            config=self.config,
        )

        self.read = GeminiRead(self.transport)
