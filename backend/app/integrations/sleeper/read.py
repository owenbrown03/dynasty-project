from app.integrations.sleeper.schemas.api import (
    NFLState,
    User,
    League,
    Roster,
    Matchup,
    Transaction,
    TradedPicks,
    Draft,
    Player,
    TrendingPlayer,
    Projection,
)

class SleeperRead:
    def __init__(self, transport):
        self.transport = transport

    # --------------------
    # General
    # --------------------
    async def get_nfl_state(self) -> NFLState:
        data = await self.transport.get("state/nfl")
        return NFLState.model_validate(data)

    # --------------------
    # User
    # --------------------
    async def get_user_details_by_username(self, username: str) -> User:
        data = await self.transport.get(f"user/{username}")
        return User.model_validate(data)

    async def get_user_details_by_user_id(self, user_id: str) -> User:
        data = await self.transport.get(f"user/{user_id}")
        return User.model_validate(data)

    # --------------------
    # Avatars
    # --------------------
    async def get_avatar_full(self, avatar_id: str):
        return await self.transport.get(f"avatars/{avatar_id}")

    async def get_avatar_thumb(self, avatar_id: str):
        return await self.transport.get(f"avatars/thumbs/{avatar_id}")

    # --------------------
    # Leagues
    # --------------------
    async def get_leagues(
        self,
        user_id: str,
        season: str,
    ) -> list[League]:
        data = await self.transport.get(
            f"user/{user_id}/leagues/nfl/{season}"
        )
        return [League.model_validate(x) for x in data]

    async def get_league(self, league_id: str) -> League:
        data = await self.transport.get(
            f"league/{league_id}"
        )
        return League.model_validate(data)

    async def get_rosters(
        self,
        league_id: str,
    ) -> list[Roster]:
        data = await self.transport.get(
            f"league/{league_id}/rosters"
        )
        return [Roster.model_validate(x) for x in data]

    async def get_users(
        self,
        league_id: str,
    ) -> list[User]:
        data = await self.transport.get(
            f"league/{league_id}/users"
        )
        return [User.model_validate(x) for x in data]

    async def get_matchups(
        self,
        league_id: str,
        week: int,
    ) -> list[Matchup]:
        data = await self.transport.get(
            f"league/{league_id}/matchups/{week}"
        )
        return [Matchup.model_validate(x) for x in data]

    async def get_winners_bracket(
        self,
        league_id: str,
    ) -> list[Matchup]:
        data = await self.transport.get(
            f"league/{league_id}/winners_bracket"
        )
        return [Matchup.model_validate(x) for x in (data or [])]

    async def get_losers_bracket(
        self,
        league_id: str,
    ) -> list[Matchup]:
        data = await self.transport.get(
            f"league/{league_id}/losers_bracket"
        )
        return [Matchup.model_validate(x) for x in (data or [])]

    async def get_transactions(
        self,
        league_id: str,
        week: int,
    ) -> list[Transaction]:
        data = await self.transport.get(
            f"league/{league_id}/transactions/{week}"
        )
        return [Transaction.model_validate(x) for x in data]

    async def get_traded_picks(
        self,
        league_id: str,
    ) -> list[TradedPicks]:
        data = await self.transport.get(
            f"league/{league_id}/traded_picks"
        )
        return [TradedPicks.model_validate(x) for x in data]

    # --------------------
    # Drafts
    # --------------------
    async def get_drafts_user(
        self,
        user_id: str,
        season: str,
    ) -> list[Draft]:
        data = await self.transport.get(
            f"user/{user_id}/drafts/nfl/{season}"
        )
        return [Draft.model_validate(x) for x in data]

    async def get_drafts_league(
        self,
        league_id: str,
    ) -> list[Draft]:
        data = await self.transport.get(
            f"league/{league_id}/drafts"
        )
        return [Draft.model_validate(x) for x in data]

    async def get_draft(
        self,
        draft_id: str,
    ) -> Draft:
        data = await self.transport.get(
            f"draft/{draft_id}"
        )
        return Draft.model_validate(data)

    async def get_draft_picks(
        self,
        draft_id: str,
    ):
        return await self.transport.get(
            f"draft/{draft_id}/picks"
        )

    async def get_draft_traded_picks(
        self,
        draft_id: str,
    ) -> list[TradedPicks]:
        data = await self.transport.get(
            f"draft/{draft_id}/traded_picks"
        )
        return [TradedPicks.model_validate(x) for x in data]

    # --------------------
    # Players
    # --------------------
    async def get_all_players(
        self,
    ) -> dict[str, Player]:
        data = await self.transport.get(
            "players/nfl"
        )

        return {
            player_id: Player.model_validate(player_data)
            for player_id, player_data in data.items()
        }

    async def get_trending_players(
        self,
        type: str,
        lookback: int = 24,
        limit: int = 25,
    ) -> list[TrendingPlayer]:
        data = await self.transport.get(
            f"players/nfl/trending/{type}",
            params={
                "lookback_hours": lookback,
                "limit": limit,
            },
        )

        return [
            TrendingPlayer.model_validate(x)
            for x in data
        ]

    # --------------------
    # Projections
    # --------------------
    async def get_projections(
        self,
        season: int,
    ) -> Projection:

        data = await self.transport.get(
            f"projections/nfl/{season}",
            alt=True,
            params={
                "season_type": "regular",
            },
        )

        return [
            Projection.model_validate(x)
            for x in data
        ]

    async def get_regular_season_stats(
        self,
        season: int,
    ) -> dict:
        return await self.transport.get(
            f"v1/stats/nfl/regular/{season}",
            alt=True,
        )
