import httpx

SLEEPER_GRAPHQL = "https://sleeper.com/graphql"

class SleeperAuthAPI:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def _post(self, query: str, variables: dict):
        resp = await self.http.post(
            SLEEPER_GRAPHQL,
            json={
                "query": query,
                "variables": variables,
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SleeperSDK/1.0",
            },
        )

        resp.raise_for_status()

        data = resp.json()

        if data.get("errors"):
            raise RuntimeError(data["errors"])

        return data["data"]

    async def send_code(self, username: str, captcha: str | None = None):
        query = """
        mutation($email_or_phone: String!, $captcha: String) {
            create_verification_code(
                email_or_phone: $email_or_phone,
                captcha: $captcha
            )
        }
        """

        return await self._post(
            query,
            {
                "email_or_phone": username,
                "captcha": captcha,
            },
        )

    async def verify_code(self, username: str, code: str, captcha: str | None = None):
        query = """
        query($username: String!, $code: String!, $captcha: String) {
            login(
                email_or_phone_or_username: $username,
                password: $code,
                captcha: $captcha
            ) {
                token
            }
        }
        """

        data = await self._post(
            query,
            {
                "username": username,
                "code": code,
                "captcha": captcha,
            },
        )

        login = data.get("login")
        if not login or not login.get("token"):
            raise RuntimeError("Sleeper auth failed")

        return login["token"]