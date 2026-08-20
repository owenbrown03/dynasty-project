import asyncio
from types import SimpleNamespace

import pytest
from sqlmodel import select

from app.core.database import AsyncSessionLocal, engine
from app.models.db.sleeper.api import League, Transaction, Movement
from app.crud.sleeper import league as league_crud

# Reuse the transactional_session context manager defined in test_database_integration
from test_database_integration import transactional_session


class FakeSleeperRead:
    """Minimal read interface returning static mock data for sync_leagues."""
    def __init__(self, league_obj, users, rosters, drafts, transactions):
        self._league = league_obj
        self._users = users
        self._rosters = rosters
        self._drafts = drafts
        self._transactions = transactions

    async def get_league(self, league_id):
        return self._league

    async def get_users(self, league_id):
        return self._users

    async def get_rosters(self, league_id):
        return self._rosters

    async def get_drafts_league(self, league_id):
        return self._drafts

    async def get_transactions(self, league_id, week=None):
        # Return full list regardless of week for simplicity
        return self._transactions

    # No‑op helpers that the sync pipeline may call
    async def get_winners_bracket(self, *args, **kwargs):
        return []

    async def get_losers_bracket(self, *args, **kwargs):
        return []

    async def get_traded_picks(self, *args, **kwargs):
        return []

    async def get_draft_picks(self, *args, **kwargs):
        return []

    async def get_nfl_state(self):
        # Simple namespace mimicking Sleeper's NFL state response
        return SimpleNamespace(season="2026", week=1)


class FakeSleeperClient:
    def __init__(self, read: FakeSleeperRead):
        self.read = read


def test_sync_leagues_trade_transaction_integration():
    """Exercise `sync_leagues` with a real DB transaction containing a trade.

    The test verifies that a `trade` transaction and its movement rows are
    persisted correctly and that foreign‑key constraints are satisfied.
    """
    async def _inner():
        # 1️⃣  Create a minimal league record in the DB (required for FK links)
        league_id = "trade-league-123"
        draft_id = "draft-trade-123"
        league = League(
            league_id=league_id,
            name="Trade League",
            season="2026",
            status="in_season",
            roster_positions=["QB", "RB", "WR", "TE"],
            scoring_settings={},
            settings={},
            total_rosters=2,
            draft_id=draft_id,
        )

        # Build static sleeper payloads
        user_main = SimpleNamespace(user_id="user-1", username="owner")
        user_other = SimpleNamespace(user_id="user-2", username="opponent")
        users = [user_main, user_other]

        roster_main = SimpleNamespace(
            roster_id=1,
            owner_id=user_main.user_id,
            league_id=league_id,
            settings={},
            starters=["player-a", "player-b"],
        )
        roster_other = SimpleNamespace(
            roster_id=2,
            owner_id=user_other.user_id,
            league_id=league_id,
            settings={},
            starters=["player-c", "player-d"],
        )
        rosters = [roster_main, roster_other]

        # Add model_dump method to mimic Pydantic models
        league.model_dump = lambda: {
            "league_id": league.league_id,
            "name": league.name,
            "season": league.season,
            "status": league.status,
            "roster_positions": league.roster_positions,
            "settings": league.settings,
            "scoring_settings": league.scoring_settings,
            "total_rosters": league.total_rosters,
            "draft_id": league.draft_id,
        }
        for user in users:
            user.model_dump = lambda u=user: {
                "user_id": u.user_id,
                "username": u.username,
            }
        for roster in rosters:
            roster.model_dump = lambda r=roster: {
                "roster_id": r.roster_id,
                "owner_id": r.owner_id,
                "league_id": r.league_id,
                "settings": r.settings,
                "starters": r.starters,
            }
        draft.model_dump = lambda: {
            "draft_id": draft.draft_id,
            "league_id": draft.league_id,
            "season": draft.season,
            "slots": draft.slots,
            "picks": draft.picks,
        }
        trade_tx.model_dump = lambda: {
            "transaction_id": trade_tx.transaction_id,
            "type": trade_tx.type,
            "status": trade_tx.status,
            "status_updated": trade_tx.status_updated,
            "adds": trade_tx.adds,
            "drops": trade_tx.drops,
            "waiver_budget": trade_tx.waiver_budget,
            "draft_picks": trade_tx.draft_picks,
        }
