import pytest
from unittest.mock import AsyncMock, MagicMock
from app.schemas.commissioner import CommissionerFaabResetRequest
from app.services.commissioner.faab import get_commissioner_faab_overview, reset_commissioner_faab
from app.models.db.sleeper.api import League as SleeperLeague
from app.models.db.sleeper.api import Roster as SleeperRoster

@pytest.mark.anyio
async def test_get_commissioner_faab_overview_empty():
    ctx = MagicMock()
    ctx.user_id = "user_1"
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = []
    mock_db.execute.return_value = mock_result
    ctx.db = mock_db
    
    res = await get_commissioner_faab_overview(ctx)
    assert res == []

@pytest.mark.anyio
async def test_reset_commissioner_faab_calls_sleeper_write():
    ctx = MagicMock()
    ctx.user_id = "user_1"
    ctx.sleeper = MagicMock()
    ctx.sleeper.write.reset_roster_faab = AsyncMock()
    
    roster = SleeperRoster(roster_id=1, settings={"waiver_budget_used": 10})
    league = SleeperLeague(league_id="league_1", name="League 1", is_commissioner=True, owner_id="user_1", settings={"waiver_budget": 100})
    league.rosters = [roster]
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = [league]
    mock_db.execute.return_value = mock_result
    ctx.db = mock_db
    
    req = CommissionerFaabResetRequest(league_ids=["league_1"], target_budget=100)
    res = await reset_commissioner_faab(ctx, req)
    
    assert res.total_leagues == 1
    assert res.successful_leagues == 1
    assert res.results[0].success == True
    assert res.results[0].rosters_reset == 1
    
    ctx.sleeper.write.reset_roster_faab.assert_called_once_with(
        league_id="league_1",
        roster_id=1,
        target_budget=0
    )
    assert roster.settings["waiver_budget_used"] == 0
