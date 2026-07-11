import asyncio
from types import SimpleNamespace

from app.services.leagues import overview as overview_service


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

    async def fake_get_user_leagues(db, username):
        return [
            (league_one, object()),
            (league_one, object()),
            (league_two, object()),
        ]

    monkeypatch.setattr(
        overview_service,
        "get_user_leagues",
        fake_get_user_leagues,
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
        },
        {
            "league_id": "league-2",
            "league_name": "League Two",
            "season": "2026",
            "total_rosters": 10,
        },
    ]
