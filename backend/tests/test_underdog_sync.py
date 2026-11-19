from unittest.mock import AsyncMock, MagicMock
import pytest

from app.integrations.underdog.read import UnderdogRead
from app.integrations.underdog.schemas import (
    UnderdogSlate,
    UnderdogContestStyle,
    UnderdogAppearance,
    UnderdogProjection,
)
from app.crud.underdog.sync import sync_underdog_adp


def _make_fake_slate(
    id: str = "slate-1",
    title: str = "2026 Season",
    best_ball: bool = True,
    lobby_hidden: bool = False,
    contest_style_ids: list[str] | None = None,
) -> UnderdogSlate:
    return UnderdogSlate(
        id=id,
        title=title,
        description="NFL Best Ball",
        sport_id="NFL",
        best_ball=best_ball,
        lobby_hidden=lobby_hidden,
        rank=1,
        contest_style_ids=contest_style_ids or ["style-1"],
        cutoff_at="2026-09-10T00:00:00Z",
        start_at="2026-09-10T00:00:00Z",
    )


@pytest.mark.anyio
async def test_get_nfl_adp_returns_empty_when_no_active_slates():
    transport = MagicMock()
    read = UnderdogRead(transport=transport)
    read.get_active_nfl_best_ball_slates = AsyncMock(return_value=[])

    result = await read.get_nfl_adp()
    assert result == []


@pytest.mark.anyio
async def test_get_nfl_adp_returns_empty_when_no_matching_contest_style():
    transport = MagicMock()
    read = UnderdogRead(transport=transport)
    fake_slate = _make_fake_slate(contest_style_ids=["style-unknown"])
    read.get_active_nfl_best_ball_slates = AsyncMock(return_value=[fake_slate])
    read.get_nfl_best_ball_contest_styles = AsyncMock(return_value=[])

    result = await read.get_nfl_adp()
    assert result == []


@pytest.mark.anyio
async def test_get_nfl_adp_returns_empty_when_superflex_requested_but_not_present():
    transport = MagicMock()
    read = UnderdogRead(transport=transport)
    fake_slate = _make_fake_slate(title="Standard 1QB Season")
    read.get_active_nfl_best_ball_slates = AsyncMock(return_value=[fake_slate])

    result = await read.get_nfl_adp(superflex=True)
    assert result == []


@pytest.mark.anyio
async def test_get_nfl_adp_success():
    transport = MagicMock()
    read = UnderdogRead(transport=transport)
    fake_slate = _make_fake_slate(title="2026 Season Best Ball")
    fake_style = UnderdogContestStyle(
        id="style-1",
        name="NFL Best Ball",
        sport_id="NFL",
        best_ball=True,
        status="active",
        scoring_type_id="score-1",
        rounds=18,
    )
    read.get_active_nfl_best_ball_slates = AsyncMock(return_value=[fake_slate])
    read.get_nfl_best_ball_contest_styles = AsyncMock(return_value=[fake_style])
    read.get_enriched_appearances = AsyncMock(return_value=[MagicMock()])

    result = await read.get_nfl_adp()
    assert len(result) == 1
    read.get_enriched_appearances.assert_awaited_once_with("slate-1", "score-1")


@pytest.mark.anyio
async def test_sync_underdog_adp_skips_cleanly_when_no_appearances():
    db = AsyncMock()
    client = MagicMock()
    client.read.get_nfl_adp = AsyncMock(return_value=[])

    result = await sync_underdog_adp(db=db, underdog=client)

    assert result["status"] == "skipped"
    assert result["reason"] == "no_active_slates"
    assert result["fetched"] == 0
    # DB execute should not have been called to query players or existing maps
    assert db.execute.call_count == 0


@pytest.mark.anyio
async def test_sync_underdog_adp_handles_exception_cleanly():
    db = AsyncMock()
    client = MagicMock()
    client.read.get_nfl_adp = AsyncMock(side_effect=Exception("API connection timeout"))

    result = await sync_underdog_adp(db=db, underdog=client)

    assert result["status"] == "skipped"
    assert "API connection timeout" in result["reason"]
    assert result["fetched"] == 0
    assert db.execute.call_count == 0


@pytest.mark.anyio
async def test_sync_underdog_adp_skips_when_all_appearances_have_zero_adp():
    db = AsyncMock()
    client = MagicMock()
    appearance_zero = UnderdogAppearance(
        id="app-1",
        player_id="p-1",
        team_id=None,
        match_id=101,
        match_type="Season",
        position_id="pos-1",
        projection=UnderdogProjection(
            id=1,
            adp=0.0,
            position_rank="1",
            scoring_type_id="score-1",
        ),
    )
    client.read.get_nfl_adp = AsyncMock(return_value=[appearance_zero])

    result = await sync_underdog_adp(db=db, underdog=client)

    assert result["status"] == "skipped"
    assert result["reason"] == "no_active_slates"
    assert db.execute.call_count == 0
