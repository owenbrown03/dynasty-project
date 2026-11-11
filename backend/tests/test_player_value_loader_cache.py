import pytest
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace

from app.analytics.war.redraft.loader import PlayerValueLoader


@pytest.mark.anyio
async def test_player_value_loader_caches_season_stats():
    loader = PlayerValueLoader(ttl_seconds=300)
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_row = SimpleNamespace(player_id="123", season=2024, season_type="regular")
    mock_result.scalars.return_value.all.return_value = [mock_row]
    mock_db.execute.return_value = mock_result

    # First call: executes query
    result1 = await loader.get_season_stats(mock_db, 2024, season_type="regular")
    assert result1 == [mock_row]
    assert mock_db.execute.call_count == 1

    # Second call: returns cached data without calling db.execute
    result2 = await loader.get_season_stats(mock_db, 2024, season_type="regular")
    assert result2 == [mock_row]
    assert mock_db.execute.call_count == 1

    # Different season: executes query
    await loader.get_season_stats(mock_db, 2023, season_type="regular")
    assert mock_db.execute.call_count == 2

    # Clear cache: re-executes
    loader.clear_cache()
    await loader.get_season_stats(mock_db, 2024, season_type="regular")
    assert mock_db.execute.call_count == 3


@pytest.mark.anyio
async def test_player_value_loader_caches_players():
    loader = PlayerValueLoader(ttl_seconds=300)
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_player = SimpleNamespace(player_id="player_1", full_name="Test Player")
    mock_result.scalars.return_value = [mock_player]
    mock_db.execute.return_value = mock_result

    # First call: executes query
    res1 = await loader.get_players(mock_db)
    assert res1 == {"player_1": mock_player}
    assert mock_db.execute.call_count == 1

    # Second call: returns cached
    res2 = await loader.get_players(mock_db)
    assert res2 == {"player_1": mock_player}
    assert mock_db.execute.call_count == 1

    # Clear cache: re-executes
    loader.clear_cache()
    await loader.get_players(mock_db)
    assert mock_db.execute.call_count == 2


@pytest.mark.anyio
async def test_player_value_loader_caches_projections():
    loader = PlayerValueLoader(ttl_seconds=300)
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_proj = SimpleNamespace(player_id="proj_1", season=2024)
    mock_result.scalars.return_value.all.return_value = [mock_proj]
    mock_db.execute.return_value = mock_result

    # First call: executes query
    res1 = await loader.get_projections(mock_db, 2024)
    assert res1 == [mock_proj]
    assert mock_db.execute.call_count == 1

    # Second call: returns cached
    res2 = await loader.get_projections(mock_db, 2024)
    assert res2 == [mock_proj]
    assert mock_db.execute.call_count == 1

    # Clear cache: re-executes
    loader.clear_cache()
    await loader.get_projections(mock_db, 2024)
    assert mock_db.execute.call_count == 2


@pytest.mark.anyio
async def test_hydrate_personal_player_values_uses_preloaded_data():
    from unittest.mock import patch
    from app.services.personal_values import hydrate_personal_player_values
    from app.models.db.sleeper.api import League
    from app.schemas.player import PlayerValue

    mock_db = AsyncMock()
    league = League(
        league_id="12345",
        season="2024",
        status="in_season",
        total_rosters=12,
        roster_positions=["QB", "RB", "WR", "TE"],
        scoring_settings={"rec": 1.0},
    )
    player = PlayerValue(
        player_id="p1",
        name="Test QB",
        position="QB",
        team="KC",
    )
    preloaded_projections = [
        SimpleNamespace(id=1, player_id="p1", season=2024, position="QB", is_customized=True)
    ]
    preloaded_outcomes = {1: []}
    curve_cache = {"some_fp": {}}

    with patch("app.services.personal_values.get_personal_projections_for_site_user", new_callable=AsyncMock) as mock_get_projs, \
         patch("app.services.personal_values.get_personal_projection_outcomes", new_callable=AsyncMock) as mock_get_outcomes, \
         patch("app.services.personal_values._ensure_personal_rank_curve", new_callable=AsyncMock) as mock_curve:
        mock_curve.return_value = {}

        result = await hydrate_personal_player_values(
            db=mock_db,
            site_user_id="site_user_1",
            league=league,
            player_values=[player],
            saved_projections=preloaded_projections,
            outcomes_by_projection_id=preloaded_outcomes,
            curve_cache=curve_cache,
        )

        assert len(result) == 1
        # DB queries for projections and outcomes must NOT be called when preloaded
        assert mock_get_projs.call_count == 0
        assert mock_get_outcomes.call_count == 0
        # curve_cache is forwarded to _ensure_personal_rank_curve
        assert mock_curve.call_args.kwargs["curve_cache"] is curve_cache

