import asyncio
from types import SimpleNamespace

from app.services.leagues import overview as overview_service
from app.services.leagues.selection import (
    OwnedLeagueRow,
    select_latest_owned_league_rows,
)


def test_get_league_overview_deduplicates_leagues(monkeypatch):
    league_one = SimpleNamespace(
        league_id="league-1",
        name="League One",
        season="2026",
        total_rosters=12,
    )
    league_two = SimpleNamespace(
        league_id="league-2",
        name="League Two",
        season="2026",
        total_rosters=10,
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
        return set()

    monkeypatch.setattr(
        overview_service,
        "get_hidden_league_ids",
        fake_get_hidden_league_ids,
    )

    result = asyncio.run(
        overview_service.get_league_overview(
            db=object(),
            username="owen",
        )
    )

    assert [item.model_dump() for item in result] == [
        {
            "league_id": "league-1",
            "league_name": "League One",
            "season": "2026",
            "total_rosters": 12,
            "is_hidden": False,
        },
        {
            "league_id": "league-2",
            "league_name": "League Two",
            "season": "2026",
            "total_rosters": 10,
            "is_hidden": False,
        },
    ]


def test_select_latest_owned_league_rows_limits_to_latest_two_seasons():
    league_2026 = SimpleNamespace(
        league_id="league-2026",
        name="League",
        season="2026",
        previous_league_id="league-2025",
    )
    league_2025 = SimpleNamespace(
        league_id="league-2025",
        name="League",
        season="2025",
        previous_league_id="league-2024",
    )
    league_2024 = SimpleNamespace(
        league_id="league-2024",
        name="League",
        season="2024",
        previous_league_id=None,
    )
    orphan_2025 = SimpleNamespace(
        league_id="orphan-2025",
        name="Orphan 2025",
        season="2025",
        previous_league_id=None,
    )
    old_2022 = SimpleNamespace(
        league_id="old-2022",
        name="Old 2022",
        season="2022",
        previous_league_id=None,
    )

    rows = [
        OwnedLeagueRow(league=league_2024, roster=object()),
        OwnedLeagueRow(league=league_2025, roster=object()),
        OwnedLeagueRow(league=league_2026, roster=object()),
        OwnedLeagueRow(league=orphan_2025, roster=object()),
        OwnedLeagueRow(league=old_2022, roster=object()),
    ]

    result = select_latest_owned_league_rows(
        rows,
    )

    assert [row.league.league_id for row in result] == [
        "league-2026",
        "orphan-2025",
    ]


def test_select_latest_owned_league_rows_excludes_hidden_leagues():
    visible_league = SimpleNamespace(
        league_id="visible-league",
        name="Visible League",
        season="2026",
        previous_league_id=None,
    )
    hidden_league = SimpleNamespace(
        league_id="hidden-league",
        name="Hidden League",
        season="2025",
        previous_league_id=None,
    )

    rows = [
        OwnedLeagueRow(league=visible_league, roster=object()),
        OwnedLeagueRow(league=hidden_league, roster=object()),
    ]

    result = select_latest_owned_league_rows(
        rows,
        hidden_league_ids={"hidden-league"},
    )

    assert [row.league.league_id for row in result] == [
        "visible-league",
    ]
