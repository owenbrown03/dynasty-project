from .exceptions import SleeperGraphQLError

class SleeperTransport:
    def __init__(self, auth, http, limiter, config):
        self.auth = auth
        self.http = http
        self.limiter = limiter
        self.config = config

    async def get(self, path: str, params: dict | None = None):
        await self.limiter.acquire()

        url = f"{self.config.REST_BASE.rstrip('/')}/{path.lstrip('/')}"

        resp = await self.http.get(
            url,
            params=params,
            headers=self.auth.headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def post(self, query: str, variables: dict):
        await self.limiter.acquire()

        resp = await self.http.post(
            self.config.GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=self.auth.headers(),
        )
        resp.raise_for_status()

        data = resp.json()

        errors = data.get("errors")
        if errors:
            raise SleeperGraphQLError(errors, data=data)

        return data["data"]