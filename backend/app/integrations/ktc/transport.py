import asyncio
import httpx
from .config import KTCConfig


class KTCTransport:
    def __init__(self, http: httpx.AsyncClient, config: KTCConfig):
        self.http = http
        self.config = config

    async def get_html(self, path: str, params: dict) -> str:
        url = self.config.base_url + path
        headers = {"User-Agent": self.config.user_agent}
        response = await self.http.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.text

    async def get_all_pages(self, path: str, format: int) -> list[str]:
        """Fetch all pages for a given format, with delay between requests."""
        pages = []
        for page in range(self.config.pages):
            html = await self.get_html(path, {"page": page, "filters": "QB|WR|RB|TE|RDP", "format": format})
            pages.append(html)
            if page < self.config.pages - 1:
                await asyncio.sleep(self.config.request_delay)
        return pages
