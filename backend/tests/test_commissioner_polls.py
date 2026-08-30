import pytest
from unittest.mock import AsyncMock, MagicMock
from app.schemas.commissioner import CommissionerPollBroadcastRequest
from app.services.commissioner.polls import broadcast_commissioner_poll
from app.core.context import Context
from types import SimpleNamespace
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_broadcast_commissioner_poll_success(monkeypatch):
    mock_db = AsyncMock()
    
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.auth.is_authenticated = MagicMock(return_value=True)
    mock_sleeper_write.create_poll.return_value = "poll_123"
    mock_sleeper_write.set_poll_expiration.return_value = True
    mock_sleeper_write.send_poll_message.return_value = {}

    ctx = Context(
        db=mock_db,
        redis=None,
        session_token="token",
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_user_id"),
        sleeper_write=mock_sleeper_write,
        sleeper=None,
        underdog=None,
    )
    
    # Mock get_visible_owned_league_rows_by_sleeper_user_id
    mock_owned_rows = [
        SimpleNamespace(league=SimpleNamespace(league_id="league1", name="League One")),
        SimpleNamespace(league=SimpleNamespace(league_id="league2", name="League Two")),
    ]
    monkeypatch.setattr(
        "app.services.commissioner.polls.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=mock_owned_rows)
    )

    request = CommissionerPollBroadcastRequest(
        prompt="Test poll",
        choices=["Option 1", "Option 2"],
        league_ids=["league1", "league3"], # league3 should fail as it's not owned
    )

    response = await broadcast_commissioner_poll(request, ctx)

    assert response.total_leagues == 2
    assert response.successful_leagues == 1
    
    results = response.results
    assert len(results) == 2
    
    assert results[0].league_id == "league1"
    assert results[0].success == True
    assert results[0].poll_id == "poll_123"

    assert results[1].league_id == "league3"
    assert results[1].success == False
    assert "Not an owned league" in results[1].error
