import httpx

from .retry import retry


class HTTPTransport:

    def __init__(
        self,
        client: httpx.AsyncClient,
    ):
        self.client = client


    async def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:

        async def _call():
            
            response = await self.client.get(
                url,
                params=params,
                headers=headers,
            )

            response.raise_for_status()

            return response

        return await retry(_call)


    async def post(
        self,
        url: str,
        *,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:

        async def _call():

            response = await self.client.post(
                url,
                json=json,
                headers=headers,
            )

            response.raise_for_status()

            return response

        return await retry(_call)