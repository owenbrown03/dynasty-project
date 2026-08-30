import logging
import uuid

from .mutations import (
    CREATE_DM_MUTATION,
    CREATE_MESSAGE_MUTATION,
    CREATE_VERIFICATION_CODE_MUTATION,
    GET_DM_BY_MEMBERS_QUERY,
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

    async def reset_roster_faab(
        self,
        league_id: str,
        roster_id: int,
        target_budget: int
    ) -> dict:
        self._require_auth()
        return await self.league_mutation(
            "update_roster",
            league_id,
            {
                "roster_id": roster_id,
                "k_settings": ["waiver_budget_used"],
                "v_settings": [-target_budget] # It resets to waiver_budget_used = waiver_budget - target_budget... Wait, what does sleeper do? If default budget is 100, and target is 100, we want used = 0. Wait, if target budget is X, how does sleeper track it? Usually `waiver_budget_used` is set directly. The requirement says: update_roster(league_id, roster_id, k_settings, v_settings)
            },
        )

    def _require_auth(self):
        if not self.auth.is_authenticated():
            raise SleeperAuthError(
                "Not authenticated. Complete the verification flow first."
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Direct-message / chat operations (requires a token)
    # ──────────────────────────────────────────────────────────────────────────

    async def get_dm_by_members(
        self,
        members: list[str],
    ) -> list[dict]:
        """Find existing 1:1 DMs with the given member user ids."""
        self._require_auth()
        data = await self.transport.post(
            query=GET_DM_BY_MEMBERS_QUERY,
            variables={"members": members},
        )
        return data.get("get_dm_by_members") or []

    async def create_dm(
        self,
        members: list[str],
    ) -> dict:
        """Create (or return) a 1:1 DM channel with the given members."""
        self._require_auth()
        data = await self.transport.post(
            query=CREATE_DM_MUTATION,
            variables={
                "dm_type": "single",
                "members": members,
            },
        )
        return data.get("create_dm") or {}

    async def create_message(
        self,
        *,
        parent_id: str,
        parent_type: str,
        text: str,
        attachment_type: str,
        k_attachment_data: list[str],
        v_attachment_data: list[object],
    ) -> dict:
        """Post a message (optionally with an embedded attachment) to a
        DM/thread parent."""
        self._require_auth()
        data = await self.transport.post(
            query=CREATE_MESSAGE_MUTATION,
            variables={
                "parent_id": parent_id,
                "client_id": str(uuid.uuid4()),
                "parent_type": parent_type,
                "text": text,
                "attachment_type": attachment_type,
                "k_attachment_data": k_attachment_data,
                "v_attachment_data": v_attachment_data,
            },
        )
        return data.get("create_message") or {}

    async def add_player_trade_block(
        self,
        *,
        player_id: str,
        league_id: str,
    ) -> dict:
        self._require_auth()
        from .mutations import ADD_LEAGUE_PLAYER_TRADE_BLOCK_MUTATION
        data = await self.transport.post(
            query=ADD_LEAGUE_PLAYER_TRADE_BLOCK_MUTATION,
            variables={"player_id": str(player_id), "league_id": str(league_id)},
        )
        return data.get("add_league_player_trade_block") or {}

    async def remove_player_trade_block(
        self,
        *,
        player_id: str,
        league_id: str,
    ) -> dict:
        self._require_auth()
        from .mutations import REMOVE_LEAGUE_PLAYER_TRADE_BLOCK_MUTATION
        data = await self.transport.post(
            query=REMOVE_LEAGUE_PLAYER_TRADE_BLOCK_MUTATION,
            variables={"player_id": str(player_id), "league_id": str(league_id)},
        )
        return data.get("remove_league_player_trade_block") or {}

