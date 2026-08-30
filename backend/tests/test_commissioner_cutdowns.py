import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.commissioner.cutdowns import (
    get_commissioner_cutdown_violations,
    execute_cutdown_action,
)
from app.schemas.commissioner import CommissionerCutdownActionRequest

@pytest.mark.asyncio
async def test_get_commissioner_cutdown_violations():
    ctx = MagicMock()
    ctx.site_user = MagicMock(id="user_123")
    ctx.connection = MagicMock(sleeper_user_id="sleeper_123")
    ctx.db = AsyncMock()
    
    with patch("app.services.commissioner.cutdowns.get_visible_owned_league_rows_by_sleeper_user_id", new_callable=AsyncMock) as mock_leagues, \
         patch("app.services.commissioner.cutdowns.get_all_rosters_by_league", new_callable=AsyncMock) as mock_rosters, \
         patch("app.services.commissioner.cutdowns.get_users", new_callable=AsyncMock) as mock_users, \
         patch("app.services.commissioner.cutdowns.get_personal_value_pool", new_callable=AsyncMock) as mock_pool:
         
        mock_leagues.return_value = []
        mock_rosters.return_value = []
        mock_users.return_value = []
        
        result = await get_commissioner_cutdown_violations(ctx)
        assert result == []

@pytest.mark.asyncio
async def test_execute_cutdown_action():
    ctx = MagicMock()
    ctx.site_user = MagicMock(id="user_123")
    ctx.connection = MagicMock(sleeper_user_id="sleeper_123")
    ctx.db = AsyncMock()
    
    req = CommissionerCutdownActionRequest(
        league_ids=["league_1"],
        action_type="message"
    )
    
    result = await execute_cutdown_action(req, ctx)
    assert len(result.results) == 1
    assert result.results[0].league_id == "league_1"
    assert result.results[0].success is True
