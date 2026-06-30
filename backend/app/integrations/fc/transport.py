import httpx

from .config import FantasyCalcConfig


class FantasyCalcTransport:
    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        config: FantasyCalcConfig | None = None,
    ):
        self.http = http
        self.config = config or FantasyCalcConfig()

    async def get(
        self,
        path: str,
        *,
        params: dict | None = None,
    ) -> dict:

        response = await self.http.get(
            f"{self.config.base_url}{path}",
            params=params,
        )

        response.raise_for_status()

        return response.json()