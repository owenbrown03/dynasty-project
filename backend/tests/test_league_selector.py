import asyncio
from types import SimpleNamespace

from app.services.leagues import overview as overview_service
from app.services.leagues.selection import OwnedLeagueRow


def test_get_league_selector_options_returns_minimal_payload(monkeypatch):
    league_one = SimpleNamespace(
        league_id="league-1",
        name="League One",
        season="2026",
    )
    league_two = SimpleNamespace(
        league_id="league-2",
        name="League Two",
        season="2025",
    )

    async def fake_get_visible_owned_league_rows_by_username(
        *,
        db,
        username,
        site_user_id=None,
        include_hidden=False,
    ):
        return [
            OwnedLeagueRow(
                league=league_one,
                roster=object(),
            ),
            OwnedLeagueRow(
                league=league_two,
                roster=object(),
            ),
        ]

    monkeypatch.setattr(
        overview_service,
        "get_visible_owned_league_rows_by_username",
        fake_get_visible_owned_league_rows_by_username,
    )

    async def fake_get_hidden_league_ids(**kwargs):
        return {"league-1"}

    monkeypatch.setattr(
        overview_service,
        "get_hidden_league_ids",
        fake_get_hidden_league_ids,
    )

    async def fake_get_focused_league_ids(**kwargs):
        return {"league-2"}

    monkeypatch.setattr(
        overview_service,
        "get_focused_league_ids",
        fake_get_focused_league_ids,
    )

    result = asyncio.run(
        overview_service.get_league_selector_options(
            db=object(),
            username="owen",
            site_user_id="user-id",
        )
    )

    assert [item.model_dump() for item in result] == [
        {
            "league_id": "league-1",
            "league_name": "League One",
            "season": "2026",
            "is_hidden": True,
            "is_focused": False,
        },
        {
            "league_id": "league-2",
            "league_name": "League Two",
            "season": "2025",
            "is_hidden": False,
            "is_focused": True,
        },
    ]


def test_get_league_selector_options_returns_empty_when_no_leagues(monkeypatch):
    async def fake_get_visible_owned_league_rows_by_username(
        *,
        db,
        username,
        site_user_id=None,
        include_hidden=False,
    ):
        return []

    monkeypatch.setattr(
        overview_service,
        "get_visible_owned_league_rows_by_username",
        fake_get_visible_owned_league_rows_by_username,
    )

    result = asyncio.run(
        overview_service.get_league_selector_options(
            db=object(),
            username="owen",
        )
    )

    assert result == []


def test_get_league_selector_options_without_site_user(monkeypatch):
    league_one = SimpleNamespace(
        league_id="league-1",
        name="League One",
        season="2026",
    )

    async def fake_get_visible_owned_league_rows_by_username(
        *,
        db,
        username,
        site_user_id=None,
        include_hidden=False,
    ):
        assert site_user_id is None
        assert include_hidden is False
        return [
            OwnedLeagueRow(
                league=league_one,
                roster=object(),
            ),
        ]

    monkeypatch.setattr(
        overview_service,
        "get_visible_owned_league_rows_by_username",
        fake_get_visible_owned_league_rows_by_username,
    )

    result = asyncio.run(
        overview_service.get_league_selector_options(
            db=object(),
            username="owen",
            site_user_id=None,
        )
    )

    assert len(result) == 1
    assert result[0].league_id == "league-1"
    assert result[0].is_hidden is False
    assert result[0].is_focused is False


def test_get_league_selector_options_passes_include_hidden(monkeypatch):
    league_one = SimpleNamespace(
        league_id="league-1",
        name="League One",
        season="2026",
    )

    async def fake_get_visible_owned_league_rows_by_username(
        *,
        db,
        username,
        site_user_id=None,
        include_hidden=False,
    ):
        assert include_hidden is True
        return [
            OwnedLeagueRow(
                league=league_one,
                roster=object(),
            ),
        ]

    monkeypatch.setattr(
        overview_service,
        "get_visible_owned_league_rows_by_username",
        fake_get_visible_owned_league_rows_by_username,
    )

    result = asyncio.run(
        overview_service.get_league_selector_options(
            db=object(),
            username="owen",
            include_hidden=True,
        )
    )

    assert len(result) == 1
    assert result[0].league_id == "league-1"