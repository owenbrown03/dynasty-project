import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services.commissioner import workspace as workspace_service
from app.services.leagues.selection import OwnedLeagueRow


async def _run_workspace_with_mocks(monkeypatch, league, rosters, traded_picks):
    # monkeypatch external dependencies used by the workspace service
    async def fake_get_visible_owned_league_rows_by_sleeper_user_id(*, db, sleeper_user_id, site_user_id, include_hidden=False):
        # return the league as owned
        return [OwnedLeagueRow(league=league, roster=rosters[0])]

    async def fake_notes_by_league_id(**kwargs):
        return {}

    async def fake_finance_entries_by_key(**kwargs):
        return {}

    async def fake_dues_by_key(**kwargs):
        return {}

    async def fake_rosters_by_league(*, db, league_ids):
        return {league.league_id: rosters}

    async def fake_traded_picks_by_league_ids(db, league_ids):
        return {league.league_id: [(tp, None) for tp in traded_picks]}

    async def fake_get_users(*args, **kwargs):
        return {}

    monkeypatch.setattr(workspace_service, "get_visible_owned_league_rows_by_sleeper_user_id", fake_get_visible_owned_league_rows_by_sleeper_user_id)
    monkeypatch.setattr(workspace_service, "get_commissioner_notes_by_league_id", fake_notes_by_league_id)
    monkeypatch.setattr(workspace_service, "get_finance_entries_by_key", fake_finance_entries_by_key)
    monkeypatch.setattr(workspace_service, "get_commissioner_dues_by_key", fake_dues_by_key)
    monkeypatch.setattr(workspace_service, "get_all_rosters_by_league", fake_rosters_by_league)
    monkeypatch.setattr(workspace_service, "get_traded_picks_by_league_ids", fake_traded_picks_by_league_ids)
    monkeypatch.setattr(workspace_service, "get_users", fake_get_users)

    ctx = SimpleNamespace(db=object(), site_user=SimpleNamespace(id=uuid4()), connection=SimpleNamespace(sleeper_user_id="sleeper-1"))
    return await workspace_service.get_commissioner_workspace(ctx)


def test_only_counts_picks_sold_by_original_owner(monkeypatch):
    # Setup a league where season is older so 2027 picks are considered future
    league = SimpleNamespace(league_id="L1", name="Test League", season="2025")

    # rosters: roster_id mapped to some owners (owner ids not used for filtering by original-owner rule)
    rosters = [
        SimpleNamespace(roster_id=3, owner_id="owner-3", league_id=league.league_id, roster_metadata={}),
        SimpleNamespace(roster_id=11, owner_id="owner-11", league_id=league.league_id, roster_metadata={}),
    ]

    # traded picks: include several picks in future season 2027 where some picks have old==og and some don't
    tp1 = SimpleNamespace(id=1, transaction_id="t1", old_roster_id=11, og_roster_id=11, season="2027", round=1, new_roster_id=1)
    tp2 = SimpleNamespace(id=2, transaction_id="t2", old_roster_id=10, og_roster_id=11, season="2027", round=1, new_roster_id=1)
    tp3 = SimpleNamespace(id=3, transaction_id="t3", old_roster_id=11, og_roster_id=11, season="2027", round=2, new_roster_id=2)
    tp4 = SimpleNamespace(id=4, transaction_id="t4", old_roster_id=3, og_roster_id=3, season="2027", round=1, new_roster_id=1)
    tp5 = SimpleNamespace(id=5, transaction_id="t5", old_roster_id=11, og_roster_id=10, season="2027", round=3, new_roster_id=2)

    traded_picks = [tp1, tp2, tp3, tp4, tp5]

    result = asyncio.run(_run_workspace_with_mocks(monkeypatch, league, rosters, traded_picks))

    # Find our league in the response
    leagues = {l.league_id: l for l in result.leagues}
    assert "L1" in leagues
    dues = leagues["L1"].dues

    # Build a map of (roster_id, season) -> traded_pick_count
    counts = {(d.roster_id, d.season): d.traded_pick_count for d in dues}

    # tp1 and tp3 should be counted under og_roster_id 11 for season 2027 (old==og)
    assert counts.get((11, "2027")) == 2

    # tp2 and tp5 should NOT be counted because old != og
    assert (10, "2027") not in counts
    assert (11, "2027") in counts

    # tp4 should be counted under roster 3
    assert counts.get((3, "2027")) == 1
