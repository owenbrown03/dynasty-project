import httpx

from .config import FantasyCalcConfig
from .transport import FantasyCalcTransport
from .read import FantasyCalcRead


class FantasyCalcClient:

    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        config: FantasyCalcConfig | None = None,
    ):
        self.config = config or FantasyCalcConfig()

        self.transport = FantasyCalcTransport(
            http=http,
            config=self.config,
        )

        self.read = FantasyCalcRead(
            self.transport
        )