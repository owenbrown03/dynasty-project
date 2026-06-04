import httpx

class HTTPTransport:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get(self, url: str, params: dict | None = None, headers: dict | None = None):
        return await self.client.get(url, params=params, headers=headers)

    async def post(self, url: str, json: dict | None = None, headers: dict | None = None):
        return await self.client.post(url, json=json, headers=headers)