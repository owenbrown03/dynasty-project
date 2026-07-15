import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.commissioner import CommissionerOrphansResponse
from app.schemas.commissioner import CommissionerPlayerAsset
from app.services.commissioner.orphans import (
    build_mock_lineup,
    build_settings_badges,
    get_commissioner_orphans,
    get_average_age,
    is_slot_eligible,
)
from app.services.commissioner import orphans as orphan_service
from app.services.commissioner import workspace as workspace_service
from app.services.leagues.selection import OwnedLeagueRow


def test_build_settings_badges_includes_expected_league_summary():
    league = SimpleNamespace(
        total_rosters=12,
        roster_positions=[
            "QB",
            "RB",
            "RB",
            "WR",
            "WR",
            "TE",
            "FLEX",
            "SUPER_FLEX",
            "BN",
            "BN",
        ],
        settings={
            "best_ball": 1,
            "reserve_slots": 2,
            "taxi_slots": 3,
        },
        scoring_settings={
            "rec": 1.5,
            "pass_td": 6,
            "bonus_rec_te": 0.75,
        },
    )

    badges = build_settings_badges(league)

    assert badges == [
        "Best Ball",
        "12 Team",
        "Start 8",
        "15 Roster",
        "SF",
        "1.5 PPR",
        "6 PPTD",
        "0.75 TEP",
    ]


def test_slot_eligibility_supports_dynasty_flex_slots():
    assert is_slot_eligible(slot="SUPER_FLEX", position="QB") is True
    assert is_slot_eligible(slot="FLEX", position="TE") is True
    assert is_slot_eligible(slot="FLEX", position="QB") is False
    assert is_slot_eligible(slot="WR", position="WR") is True
    assert is_slot_eligible(slot="WR", position="RB") is False


def test_build_mock_lineup_assigns_best_player_to_each_starter_slot():
    players = [
        CommissionerPlayerAsset(
            player_id="qb-1",
            name="Elite QB",
            position="QB",
            selected_value=95,
        ),
        CommissionerPlayerAsset(
            player_id="wr-1",
            name="Top WR",
            position="WR",
            selected_value=90,
        ),
        CommissionerPlayerAsset(
            player_id="rb-1",
            name="Top RB",
            position="RB",
            selected_value=80,
        ),
        CommissionerPlayerAsset(
            player_id="te-1",
            name="Top TE",
            position="TE",
            selected_value=70,
        ),
        CommissionerPlayerAsset(
            player_id="wr-2",
            name="Bench WR",
            position="WR",
            selected_value=60,
        ),
    ]

    lineup, bench = build_mock_lineup(
        roster_positions=["QB", "WR", "FLEX", "SUPER_FLEX", "BN"],
        players=players,
    )

    assert [slot.slot for slot in lineup] == [
        "QB",
        "WR",
        "FLEX",
        "SFLEX",
    ]
    assert [slot.player.name if slot.player else None for slot in lineup] == [
        "Elite QB",
        "Top WR",
        "Top RB",
        "Top TE",
    ]
    assert [player.name for player in bench] == [
        "Bench WR",
    ]


def test_get_average_age_rounds_to_one_decimal():
    players = [
        CommissionerPlayerAsset(
            player_id="1",
            name="One",
            age=24.1,
        ),
        CommissionerPlayerAsset(
            player_id="2",
            name="Two",
            age=25.2,
        ),
        CommissionerPlayerAsset(
            player_id="3",
            name="Three",
            age=None,
        ),
    ]

    assert get_average_age(players) == 24.6
    assert get_average_age([]) is None


def test_commissioner_workspace_uses_visible_current_leagues(monkeypatch):
    site_user_id = uuid4()
    league = SimpleNamespace(
        league_id="current-visible",
        name="Current Visible",
        season="2026",
    )
    roster = SimpleNamespace(
        roster_id=1,
        owner_id="sleeper-1",
        league_id="current-visible",
        roster_metadata={},
    )
    selector_calls = []

    async def fake_get_visible_owned_league_rows_by_sleeper_user_id(
        *,
        db,
        sleeper_user_id,
        site_user_id,
        include_hidden=False,
    ):
        selector_calls.append(
            {
                "sleeper_user_id": sleeper_user_id,
                "site_user_id": site_user_id,
                "include_hidden": include_hidden,
            }
        )
        return [
            OwnedLeagueRow(
                league=league,
                roster=roster,
            )
        ]

    async def fake_notes_by_league_id(**kwargs):
        return {}

    async def fake_finance_entries_by_key(**kwargs):
        return {}

    async def fake_dues_by_key(**kwargs):
        return {}

    async def fake_rosters_by_league(**kwargs):
        return {
            "current-visible": [roster],
        }

    async def fake_traded_picks_by_league_ids(*args, **kwargs):
        return {}

    async def fake_get_users(*args, **kwargs):
        return {}

    monkeypatch.setattr(
        workspace_service,
        "get_visible_owned_league_rows_by_sleeper_user_id",
        fake_get_visible_owned_league_rows_by_sleeper_user_id,
    )
    monkeypatch.setattr(
        workspace_service,
        "get_commissioner_notes_by_league_id",
        fake_notes_by_league_id,
    )
    monkeypatch.setattr(
        workspace_service,
        "get_finance_entries_by_key",
        fake_finance_entries_by_key,
    )
    monkeypatch.setattr(
        workspace_service,
        "get_commissioner_dues_by_key",
        fake_dues_by_key,
    )
    monkeypatch.setattr(
        workspace_service,
        "get_all_rosters_by_league",
        fake_rosters_by_league,
    )
    monkeypatch.setattr(
        workspace_service,
        "get_traded_picks_by_league_ids",
        fake_traded_picks_by_league_ids,
    )
    monkeypatch.setattr(
        workspace_service,
        "get_users",
        fake_get_users,
    )

    ctx = SimpleNamespace(
        db=object(),
        site_user=SimpleNamespace(id=site_user_id),
        connection=SimpleNamespace(sleeper_user_id="sleeper-1"),
    )

    result = asyncio.run(
        workspace_service.get_commissioner_workspace(ctx)
    )

    assert selector_calls == [
        {
            "sleeper_user_id": "sleeper-1",
            "site_user_id": site_user_id,
            "include_hidden": False,
        }
    ]
    assert [league.league_id for league in result.leagues] == [
        "current-visible",
    ]


def test_commissioner_orphans_uses_visible_current_leagues(monkeypatch):
    site_user_id = uuid4()
    visible_league = SimpleNamespace(
        league_id="current-visible",
        name="Current Visible",
        season="2026",
        is_dynasty=True,
        status="in_season",
        roster_positions=[],
        settings={},
        scoring_settings={},
        total_rosters=12,
    )
    roster = SimpleNamespace(
        roster_id=4,
        owner_id=None,
        league_id="current-visible",
        players=[],
    )
    selector_calls = []

    async def fake_get_visible_owned_league_rows_by_username(
        *,
        db,
        username,
        site_user_id,
        include_hidden=False,
    ):
        selector_calls.append(
            {
                "username": username,
                "site_user_id": site_user_id,
                "include_hidden": include_hidden,
            }
        )
        return [
            OwnedLeagueRow(league=visible_league, roster=object()),
        ]

    async def fake_get_all_rosters_by_league(*, db, league_ids):
        assert league_ids == ["current-visible"]
        return {
            "current-visible": [roster],
        }

    async def fake_get_drafts_by_league_ids(*args, **kwargs):
        return {}

    async def fake_get_sync_states(*args, **kwargs):
        return {}

    async def fake_get_traded_picks_by_league_ids(*args, **kwargs):
        return {}

    async def fake_get_users(*args, **kwargs):
        return {}

    async def fake_get_war_value_settings_by_user_id(*args, **kwargs):
        return None

    async def fake_get_resolved_pick_values_by_key(*args, **kwargs):
        return {}

    monkeypatch.setattr(
        orphan_service,
        "get_visible_owned_league_rows_by_username",
        fake_get_visible_owned_league_rows_by_username,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_all_rosters_by_league",
        fake_get_all_rosters_by_league,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_drafts_by_league_ids",
        fake_get_drafts_by_league_ids,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_sync_states",
        fake_get_sync_states,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_traded_picks_by_league_ids",
        fake_get_traded_picks_by_league_ids,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_users",
        fake_get_users,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_war_value_settings_by_user_id",
        fake_get_war_value_settings_by_user_id,
    )
    monkeypatch.setattr(
        orphan_service,
        "get_resolved_pick_values_by_key",
        fake_get_resolved_pick_values_by_key,
    )

    result = asyncio.run(
        get_commissioner_orphans(
            db=object(),
            username="browntown333",
            value_basis="ktc",
            site_user_id=site_user_id,
        )
    )

    assert isinstance(result, CommissionerOrphansResponse)
    assert selector_calls == [
        {
            "username": "browntown333",
            "site_user_id": site_user_id,
            "include_hidden": False,
        }
    ]
    assert len(result.orphans) == 1
    assert result.orphans[0].league_id == "current-visible"
    assert result.orphans[0].league_name == "Current Visible"
