import logging

from .mutations import (
    CREATE_VERIFICATION_CODE_MUTATION,
    LOGIN_QUERY,
    MUTATIONS,
)
from .exceptions import (
    SleeperAuthError,
    SleeperUnknownOperationError,
    SleeperValidationError,
)

logger = logging.getLogger(__name__)


class SleeperWrite:
    def __init__(self, transport, auth):
        self.transport = transport
        self.auth = auth

    # ──────────────────────────────────────────────────────────────────────────
    # Sleeper authentication
    # ──────────────────────────────────────────────────────────────────────────

    async def send_code(
        self,
        username: str,
        captcha: str,
    ) -> None:
        await self.transport.post(
            query=CREATE_VERIFICATION_CODE_MUTATION,
            variables={
                "email_or_phone": username,
                "captcha": captcha,
            },
        )

    async def verify_code(
        self,
        username: str,
        code: str,
        captcha: str | None = None,
    ) -> str:
        logger.debug(
            "[sleeper:verify_code] identifier=%r captcha=%s",
            username,
            "<present>" if captcha else None,
        )
        data = await self.transport.post(
            query=LOGIN_QUERY,
            variables={
                "email_or_phone_or_username": username,
                "password": code,
                "captcha": captcha,
            },
        )

        token = data.get("login", {}).get("token")
        if not token:
            raise SleeperAuthError(
                "Login accepted but no token returned — "
                "response was: " + str(data)
            )

        self.auth.set_token(token)
        return token

    # ──────────────────────────────────────────────────────────────────────────
    # Write operations (requires a token from verify_code above)
    # ──────────────────────────────────────────────────────────────────────────

    async def mutation(self, name: str, variables: dict):
        if name not in MUTATIONS:
            raise SleeperUnknownOperationError(name)
        return await self.transport.post(
            query=MUTATIONS[name],
            variables=variables,
        )

    async def league_mutation(self, name: str, league_id: str, variables: dict):
        if not league_id:
            raise SleeperValidationError("league_id is required")
        return await self.mutation(name, {**variables, "league_id": league_id})

    async def propose_trade(
        self,
        league_id: str,
        k_adds: list[str],
        v_adds: list[int],
        k_drops: list[str],
        v_drops: list[int],
        draft_picks: list[str] | None = None,
        waiver_budget: list[int] | None = None,
        expires_at: int | None = None,
    ) -> dict:
        self._require_auth()
        return await self.league_mutation(
            "propose_trade",
            league_id,
            {
                "k_adds": k_adds,
                "v_adds": v_adds,
                "k_drops": k_drops,
                "v_drops": v_drops,
                "draft_picks": draft_picks or [],
                "waiver_budget": waiver_budget or [],
                "expires_at": expires_at,
            },
        )

    async def submit_waiver_claim(
        self,
        league_id: str,
        k_adds: list[str],
        v_adds: list[int],
        k_drops: list[str],
        v_drops: list[int],
        k_settings: list[str] | None = None,
        v_settings: list[int] | None = None,
    ) -> dict:
        self._require_auth()
        return await self.league_mutation(
            "submit_waiver_claim",
            league_id,
            {
                "k_adds": k_adds,
                "v_adds": v_adds,
                "k_drops": k_drops,
                "v_drops": v_drops,
                "k_settings": k_settings or [],
                "v_settings": v_settings or [],
            },
        )

    def _require_auth(self):
        if not self.auth.is_authenticated():
            raise SleeperAuthError(
                "Not authenticated. Complete the verification flow first."
            )
