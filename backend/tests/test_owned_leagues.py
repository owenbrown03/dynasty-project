import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.crud.sleeper.league import get_owned_leagues_by_sleeper_user_id


def test_get_owned_leagues_by_sleeper_user_id_filters_only_by_owner_id():
    mock_db = MagicMock()
    mock_execute = AsyncMock()
    mock_db.execute = mock_execute

    mock_result = MagicMock()
    mock_result.all.return_value = [("league_obj", "roster_obj")]
    mock_execute.return_value = mock_result

    result = asyncio.run(get_owned_leagues_by_sleeper_user_id(mock_db, "user_123"))
    assert result == [("league_obj", "roster_obj")]

    call_args = mock_execute.call_args[0]
    query = call_args[0]
    where_sql = str(query.whereclause)
    assert "roster.owner_id" in where_sql
    assert "is_owner" not in where_sql
