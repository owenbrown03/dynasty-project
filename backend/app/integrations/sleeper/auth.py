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
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Origin": "https://sleeper.com",
            "Referer": "https://sleeper.com/",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
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