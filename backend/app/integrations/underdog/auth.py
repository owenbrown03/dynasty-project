import time
import httpx
import base64
import binascii
import json
from .config import UnderdogConfig


def _decode_jwt_exp(token: str) -> int | None:
    """Decode expiry from JWT payload without a library."""
    try:
        payload_b64 = token.split(".")[1]
        # Pad base64 if needed
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("exp")
    except (
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        binascii.Error,
        json.JSONDecodeError,
    ):
        return None


class UnderdogAuth:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ):
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._email = email
        self._password = password

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def auth_header(self) -> dict:
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    def is_expired(self) -> bool:
        if not self._access_token:
            return True
        exp = _decode_jwt_exp(self._access_token)
        if exp is None:
            return True
        # Treat as expired 60s early to avoid edge cases
        return time.time() >= (exp - 60)

    async def ensure_valid(self, http: httpx.AsyncClient, config: UnderdogConfig) -> None:
        """Refresh or re-login if token is expired."""
        if not self.is_expired():
            return

        if self._refresh_token:
            await self._refresh(http, config)
        elif self._email and self._password:
            await self._login(http, config)
        else:
            raise RuntimeError(
                "Underdog token is expired and no refresh_token or credentials provided. "
                "Pass a fresh access_token, refresh_token, or email+password to UnderdogAuth."
            )

    async def _refresh(self, http: httpx.AsyncClient, config: UnderdogConfig) -> None:
        response = await http.post(
            config.auth_url,
            json={
                "grant_type": "refresh_token",
                "client_id": config.client_id,
                "refresh_token": self._refresh_token,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        if "refresh_token" in data:
            self._refresh_token = data["refresh_token"]

    async def _login(self, http: httpx.AsyncClient, config: UnderdogConfig) -> None:
        response = await http.post(
            config.auth_url,
            json={
                "grant_type": "password",
                "client_id": config.client_id,
                "username": self._email,
                "password": self._password,
                "scope": "offline_access",
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token")
