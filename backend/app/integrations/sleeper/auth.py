class SleeperAuth:
    def __init__(self, token: str | None = None):
        self._token = token

    @property
    def token(self) -> str | None:
        return self._token

    def set_token(self, token: str | None):
        self._token = token

    def clear(self):
        self._token = None

    def is_authenticated(self) -> bool:
        return self._token is not None

    def base_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SleeperSDK/1.0",
        }

    def auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}

        return {
            "Authorization": self._token,
        }

    def headers(self) -> dict[str, str]:
        return {
            **self.base_headers(),
            **self.auth_headers(),
        }