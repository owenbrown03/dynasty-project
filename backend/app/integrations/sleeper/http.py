import httpx
from .retry import retry


class HTTPTransport:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get(self, url: str, params=None, headers=None):
        async def _call():
            resp = await self.client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp

        return await retry(_call)

    async def post(self, url: str, json=None, headers=None):
        async def _call():
            resp = await self.client.post(url, json=json, headers=headers)
            resp.raise_for_status()
            return resp

        return await retry(_call)