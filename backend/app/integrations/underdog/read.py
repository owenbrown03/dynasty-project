from .transport import UnderdogTransport
from .schemas import (
    UnderdogSlate,
    UnderdogContestStyle,
    UnderdogPlayer,
    UnderdogTeam,
    UnderdogAppearance,
    UnderdogProjection,
)


class UnderdogRead:
    def __init__(self, transport: UnderdogTransport):
        self.transport = transport

    # --------------------
    # Slates
    # --------------------
    async def get_nfl_slates(self) -> list[UnderdogSlate]:
        data = await self.transport.stats_get("/sports/nfl/slates")
        return [UnderdogSlate.model_validate(s) for s in data["slates"]]

    async def get_active_nfl_best_ball_slates(self) -> list[UnderdogSlate]:
        """Returns non-hidden best ball slates — the ones users actually draft in."""
        slates = await self.get_nfl_slates()
        return [s for s in slates if s.best_ball and not s.lobby_hidden]

    # --------------------
    # Contest Styles
    # --------------------
    async def get_contest_styles(self) -> list[UnderdogContestStyle]:
        data = await self.transport.stats_get("/contest_styles")
        return [UnderdogContestStyle.model_validate(cs) for cs in data["contest_styles"]]

    async def get_nfl_best_ball_contest_styles(self) -> list[UnderdogContestStyle]:
        styles = await self.get_contest_styles()
        return [
            cs for cs in styles
            if cs.sport_id == "NFL" and cs.best_ball and cs.status == "active"
        ]

    # --------------------
    # Teams
    # --------------------
    async def get_nfl_teams(self) -> list[UnderdogTeam]:
        data = await self.transport.stats_get("/teams", params={"sport_id": "NFL"})
        return [UnderdogTeam.model_validate(t) for t in data["teams"]]

    async def get_team_map(self) -> dict[str, str]:
        """Returns {team_uuid: abbr} for quick lookups."""
        teams = await self.get_nfl_teams()
        return {t.id: t.abbr for t in teams}

    # --------------------
    # Players
    # --------------------
    async def get_slate_players(self, slate_id: str) -> list[UnderdogPlayer]:
        data = await self.transport.stats_get(f"/slates/{slate_id}/players")
        return [UnderdogPlayer.model_validate(p) for p in data["players"]]

    async def get_player_map(self, slate_id: str) -> dict[str, UnderdogPlayer]:
        """Returns {player_uuid: UnderdogPlayer} for joining with appearances."""
        players = await self.get_slate_players(slate_id)
        return {p.id: p for p in players}

    # --------------------
    # Appearances / ADP
    # --------------------
    async def get_appearances(
        self,
        slate_id: str,
        scoring_type_id: str,
    ) -> list[UnderdogAppearance]:
        data = await self.transport.stats_get(
            f"/slates/{slate_id}/scoring_types/{scoring_type_id}/appearances"
        )
        return [
            UnderdogAppearance.model_validate(a)
            for a in data["appearances"]
        ]

    async def get_enriched_appearances(
        self,
        slate_id: str,
        scoring_type_id: str,
    ) -> list[UnderdogAppearance]:
        """
        Fetches appearances and joins player + team data onto each one.
        This is the main method to use for ADP pipelines.
        """
        appearances, player_map, team_map = await _gather_all(
            self.get_appearances(slate_id, scoring_type_id),
            self.get_player_map(slate_id),
            self.get_nfl_teams(),
        )
        team_abbr_map = {t.id: t.abbr for t in team_map}

        enriched = []
        for app in appearances:
            player = player_map.get(app.player_id)
            app.player = player
            app.team_abbr = team_abbr_map.get(app.team_id) if app.team_id else None
            enriched.append(app)

        return enriched

    async def get_nfl_adp(
        self,
        *,
        superflex: bool = False,
    ) -> list[UnderdogAppearance]:
        """
        Convenience method: fetches ADP for the current active NFL best ball slate.
        Set superflex=True for the SF slate.
        """
        slates = await self.get_active_nfl_best_ball_slates()
        if not slates:
            raise RuntimeError("No active NFL best ball slates found.")

        # Pick SF or standard slate by title
        target_title = "Superflex" if superflex else "2026 Season"
        slate = next(
            (s for s in slates if ("Superflex" in s.title) == superflex and not s.lobby_hidden),
            slates[0],
        )

        # Get the scoring_type_id from the contest style
        styles = await self.get_nfl_best_ball_contest_styles()
        style_ids = set(slate.contest_style_ids)
        style = next((cs for cs in styles if cs.id in style_ids), None)
        if not style:
            raise RuntimeError(f"No matching contest style found for slate {slate.id}")

        return await self.get_enriched_appearances(slate.id, style.scoring_type_id)


# asyncio.gather helper to run coroutines concurrently
import asyncio

async def _gather_all(*coros):
    return await asyncio.gather(*coros)
