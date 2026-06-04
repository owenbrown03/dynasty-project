class SleeperRead:
    def __init__(self, transport):
        self.transport = transport

    # --------------------
    # General
    # --------------------
    async def get_nfl_state(self):
        return await self.transport.get("state/nfl")

    # --------------------
    # User
    # --------------------
    async def get_user_details_by_username(self, username: str):
        return await self.transport.get(f"user/{username}")

    async def get_user_details_by_user_id(self, user_id: str):
        return await self.transport.get(f"user/{user_id}")

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
    async def get_leagues(self, user_id: str, season: str):
        return await self.transport.get(f"user/{user_id}/leagues/nfl/{season}")

    async def get_league(self, league_id: str):
        return await self.transport.get(f"league/{league_id}")

    async def get_rosters(self, league_id: str):
        return await self.transport.get(f"league/{league_id}/rosters")

    async def get_users(self, league_id: str):
        return await self.transport.get(f"league/{league_id}/users")

    async def get_matchups(self, league_id: str, week: int):
        return await self.transport.get(f"league/{league_id}/matchups/{week}")

    async def get_winners_bracket(self, league_id: str):
        return await self.transport.get(f"league/{league_id}/winners_bracket")

    async def get_losers_bracket(self, league_id: str):
        return await self.transport.get(f"league/{league_id}/losers_bracket")

    async def get_transactions(self, league_id: str, week: int):
        return await self.transport.get(f"league/{league_id}/transactions/{week}")

    async def get_traded_picks(self, league_id: str):
        return await self.transport.get(f"league/{league_id}/traded_picks")

    # --------------------
    # Drafts
    # --------------------
    async def get_drafts_user(self, user_id: str, season: str):
        return await self.transport.get(f"user/{user_id}/drafts/nfl/{season}")

    async def get_drafts_league(self, league_id: str):
        return await self.transport.get(f"league/{league_id}/drafts")

    async def get_draft(self, draft_id: str):
        return await self.transport.get(f"draft/{draft_id}")

    async def get_draft_picks(self, draft_id: str):
        return await self.transport.get(f"draft/{draft_id}/picks")

    async def get_draft_traded_picks(self, draft_id: str):
        return await self.transport.get(f"draft/{draft_id}/traded_picks")

    # --------------------
    # Players
    # --------------------
    async def get_all_players(self):
        return await self.transport.get("players/nfl")

    async def get_trending_players(self, type: str, lookback: int = 24, limit: int = 25):
        return await self.transport.get(
            f"players/nfl/trending/{type}",
            params={"lookback_hours": lookback, "limit": limit},
        )