import httpx
from .auth import UnderdogAuth
from .config import UnderdogConfig


class UnderdogTransport:
    def __init__(self, *, http: httpx.AsyncClient, auth: UnderdogAuth, config: UnderdogConfig):
        self.http = http
        self.auth = auth
        self.config = config

    async def stats_get(self, path: str, params: dict | None = None) -> dict:
        """GET from stats.underdogfantasy.com — public, no auth required."""
        url = self.config.stats_base_url + path
        merged_params = {**self.config.default_params, **(params or {})}
        response = await self.http.get(url, params=merged_params)
        response.raise_for_status()
        return response.json()

    async def api_get(self, path: str, params: dict | None = None) -> dict:
        """GET from api.underdogfantasy.com — requires auth."""
        await self.auth.ensure_valid(self.http, self.config)
        url = self.config.api_base_url + path
        merged_params = {**self.config.default_params, **(params or {})}
        response = await self.http.get(
            url,
            params=merged_params,
            headers=self.auth.auth_header,
        )
        response.raise_for_status()
        return response.json()
