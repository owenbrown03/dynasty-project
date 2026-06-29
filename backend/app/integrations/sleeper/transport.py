from .exceptions import SleeperGraphQLError


class SleeperTransport:

    def __init__(
        self,
        *,
        auth,
        http,
        limiter,
        config,
    ):
        self.auth = auth
        self.http = http
        self.limiter = limiter
        self.config = config

    async def get(self, path: str, alt=False, params=None):
        await self.limiter.acquire()

        if(alt):
            url = f"{self.config.rest_alt.rstrip('/')}/{path.lstrip('/')}"
        else:
            url = f"{self.config.rest_base.rstrip('/')}/{path.lstrip('/')}"
            
        resp = await self.http.get(
            url,
            params=params,
            headers=self.auth.headers(),
        )

        return resp.json()

    async def post(self, query: str, variables: dict):
        await self.limiter.acquire()

        data = await self.http.post(
            self.config.graphql_url,
            json={"query": query, "variables": variables},
            headers=self.auth.headers(),
        )

        payload = data.json()

        if payload.get("errors"):
            raise SleeperGraphQLError(payload["errors"])

        return payload["data"]