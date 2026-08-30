import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.commissioner.cutdowns import (
    get_commissioner_cutdown_violations,
    execute_cutdown_action,
)
from app.schemas.commissioner import CommissionerCutdownActionRequest

@pytest.mark.anyio
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

@pytest.mark.anyio
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


@pytest.mark.anyio
async def test_get_commissioner_cutdown_violations_over_limit_uses_ktc_values():
    from app.models.db.sleeper.api import League, Roster
    from app.services.leagues.selection import OwnedLeagueRow
    from app.schemas.personal_values import (
        PersonalValuePoolResponse,
        PersonalValuePoolGroup,
        PersonalValuePoolItem,
        PersonalValuePlayer,
    )

    ctx = MagicMock()
    ctx.site_user = MagicMock(id="user_123")
    ctx.connection = MagicMock(sleeper_user_id="sleeper_123")
    ctx.db = AsyncMock()

    league = League(
        league_id="league_1",
        name="Some Dynasty League",
        season="2026",
        type="dynasty",
        total_rosters=12,
        draft_id="draft_1",
        roster_positions=["WR"],
        settings={"type": 2, "best_ball": 0},
    )
    # 1 roster slot, 2 players -> 1 over the limit.
    roster = Roster(
        roster_id=1,
        owner_id="owner_1",
        league_id="league_1",
        players=["player_1", "player_2"],
        starters=[],
    )
    row = OwnedLeagueRow(league=league, roster=roster)

    owner = MagicMock()
    owner.display_name = "Owner One"
    owner.avatar = "avatar_url"

    pool = PersonalValuePoolResponse(
        context={"league_id": "league_1", "league_name": "Some Dynasty League", "season": 2026, "total_rosters": 12},
        groups=[
            PersonalValuePoolGroup(
                position="WR",
                players=[
                    PersonalValuePoolItem(
                        player=PersonalValuePlayer(
                            player_id="player_1",
                            name="Cheap Player",
                            position="WR",
                            team="TEN",
                            ktc_value=5.0,
                        ),
                        market_values=MagicMock(),
                        custom_values=MagicMock(),
                        delta_values=MagicMock(),
                    ),
                    PersonalValuePoolItem(
                        player=PersonalValuePlayer(
                            player_id="player_2",
                            name="Valuable Player",
                            position="WR",
                            team="CIN",
                            ktc_value=90.0,
                        ),
                        market_values=MagicMock(),
                        custom_values=MagicMock(),
                        delta_values=MagicMock(),
                    ),
                ],
            )
        ],
    )

    with patch("app.services.commissioner.cutdowns.get_visible_owned_league_rows_by_sleeper_user_id", new_callable=AsyncMock) as mock_leagues, \
         patch("app.services.commissioner.cutdowns.get_all_rosters_by_league", new_callable=AsyncMock) as mock_rosters, \
         patch("app.services.commissioner.cutdowns.get_users", new_callable=AsyncMock) as mock_users, \
         patch("app.services.commissioner.cutdowns.get_personal_value_pool", new_callable=AsyncMock) as mock_pool:

        mock_leagues.return_value = [row]
        mock_rosters.return_value = {"league_1": [roster]}
        mock_users.return_value = {"owner_1": owner}
        mock_pool.return_value = pool

        result = await get_commissioner_cutdown_violations(ctx)

        assert len(result) == 1
        assert result[0].league_id == "league_1"
        assert len(result[0].violations) == 1

        violation = result[0].violations[0]
        assert violation.roster_id == 1
        assert violation.owner_name == "Owner One"
        assert violation.over_limit_count == 1
        assert violation.max_roster_size == 1

        assert len(violation.proposed_drops) == 1
        drop = violation.proposed_drops[0]
        assert drop.player_id == "player_1"
        assert drop.ktc_value == 5.0
