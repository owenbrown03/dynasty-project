from __future__ import annotations

from collections import defaultdict

from app.analytics.war.dynasty.factory import (
    build_dynasty_war_service,
)
from app.analytics.war.redraft.singleton import war_service
from app.crud.sleeper.draft import (
    get_drafts_by_league_ids,
    get_traded_picks_by_league_ids,
)
from app.crud.sleeper.league import get_user_leagues
from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_users
from app.crud.value import get_player_values
from app.schemas.commissioner import (
    CommissionerLineupSlot,
    CommissionerOrphanRoster,
    CommissionerOrphansResponse,
    CommissionerPlayerAsset,
)
from app.schemas.player import PlayerValue
from app.services.draft.picks import (
    build_owned_pick_assets_by_roster_id,
    build_roster_name_by_id,
)
from app.services.draft.values import (
    get_resolved_pick_values_by_key,
)
from app.services.values.basis import (
    ValueBasis,
    get_player_value,
    get_value_label,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
    build_dynasty_projection,
)


def build_settings_badges(
    league,
) -> list[str]:
    roster_positions = league.roster_positions or []
    settings = league.settings or {}
    scoring = league.scoring_settings or {}

    starter_count = sum(
        slot not in {"BN", "IR", "TAXI"}
        for slot in roster_positions
    )

    roster_size = (
        len(roster_positions)
        + int(settings.get("reserve_slots", 0) or 0)
        + int(settings.get("taxi_slots", 0) or 0)
    )

    badges = [
        "Best Ball" if settings.get("best_ball") == 1 else "Lineup",
        f"{league.total_rosters} Team",
        f"Start {starter_count}",
        f"{roster_size} Roster",
        "SF" if "SUPER_FLEX" in roster_positions else "1QB",
        f"{scoring.get('rec', 0)} PPR",
        f"{scoring.get('pass_td', 4)} PPTD",
    ]

    tep = scoring.get("bonus_rec_te", 0)

    if tep and tep > 0:
        badges.append(f"{tep} TEP")

    return badges


def to_commissioner_player(
    player: PlayerValue,
    value_basis: ValueBasis,
) -> CommissionerPlayerAsset:
    selected_value = get_player_value(
        player,
        value_basis,
    )

    return CommissionerPlayerAsset(
        player_id=player.player_id,
        name=player.name,
        position=player.position,
        team=player.team,
        age=player.age,
        selected_value=selected_value,
    )


def is_slot_eligible(
    *,
    slot: str,
    position: str | None,
) -> bool:
    if position is None:
        return False

    if slot == "SUPER_FLEX":
        return position in DYNASTY_FANTASY_POSITIONS

    if slot == "FLEX":
        return position in {"RB", "WR", "TE"}

    return position == slot


def build_mock_lineup(
    *,
    roster_positions: list[str],
    players: list[CommissionerPlayerAsset],
) -> tuple[list[CommissionerLineupSlot], list[CommissionerPlayerAsset]]:
    starters = [
        slot
        for slot in roster_positions
        if slot not in {"BN", "IR", "TAXI"}
    ]

    remaining = sorted(
        players,
        key=lambda player: (
            player.selected_value
            if player.selected_value is not None
            else float("-inf")
        ),
        reverse=True,
    )

    lineup: list[CommissionerLineupSlot] = []

    for slot in starters:
        match = next(
            (
                player
                for player in remaining
                if is_slot_eligible(
                    slot=slot,
                    position=player.position,
                )
            ),
            None,
        )

        if match is not None:
            remaining.remove(match)

        lineup.append(
            CommissionerLineupSlot(
                slot=slot.replace(
                    "SUPER_FLEX",
                    "SFLEX",
                ),
                player=match,
            )
        )

    return lineup, remaining


def get_average_age(
    players: list[CommissionerPlayerAsset],
) -> float | None:
    ages = [
        player.age
        for player in players
        if player.age is not None
    ]

    if not ages:
        return None

    return round(
        sum(ages) / len(ages),
        1,
    )


async def build_league_player_values(
    *,
    db,
    league,
    player_ids: list[str],
    value_basis: ValueBasis,
) -> list[PlayerValue]:
    unique_player_ids = list(
        dict.fromkeys(player_ids),
    )

    if value_basis in {
        ValueBasis.KTC,
        ValueBasis.FANTASYCALC,
    }:
        return await get_player_values(
            db,
            player_ids=unique_player_ids,
            redraft_war_players=[],
            dynasty_war_by_player_id={},
        )

    shared = await war_service.load_shared_data(
        db,
        int(league.season),
    )

    war_players = await war_service.calculate_with_data(
        league=league,
        shared=shared,
    )

    dynasty_war_by_player_id = {}

    if value_basis in {
        ValueBasis.DYNASTY_STARTER_WAR,
        ValueBasis.DYNASTY_ROSTER_WAR,
    }:
        dynasty_service = build_dynasty_war_service()

        for player in war_players:
            if player.player_id in dynasty_war_by_player_id:
                continue

            projection = build_dynasty_projection(
                player_war=player,
                dynasty_service=dynasty_service,
            )

            if projection is not None:
                dynasty_war_by_player_id[
                    player.player_id
                ] = projection

    return await get_player_values(
        db,
        player_ids=[player.player_id for player in war_players],
        redraft_war_players=war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )


async def get_commissioner_orphans(
    *,
    db,
    username: str,
    value_basis: ValueBasis,
) -> CommissionerOrphansResponse:
    user_leagues = await get_user_leagues(
        db,
        username,
    )

    if not user_leagues:
        return CommissionerOrphansResponse(
            username=username,
            value_basis=value_basis,
            value_label=get_value_label(value_basis),
            orphans=[],
        )

    leagues_by_id = {
        league.league_id: league
        for league, _ in user_leagues
    }

    rosters_by_league_id = await get_all_rosters_by_league(
        db=db,
        league_ids=list(leagues_by_id.keys()),
    )

    orphan_league_ids = [
        league_id
        for league_id, rosters in rosters_by_league_id.items()
        if any(
            roster.owner_id is None
            for roster in rosters
        )
    ]

    if not orphan_league_ids:
        return CommissionerOrphansResponse(
            username=username,
            value_basis=value_basis,
            value_label=get_value_label(value_basis),
            orphans=[],
        )

    drafts_by_league_id = await get_drafts_by_league_ids(
        db,
        orphan_league_ids,
    )
    traded_picks_by_league_id = (
        await get_traded_picks_by_league_ids(
            db,
            orphan_league_ids,
        )
    )

    owner_ids = {
        roster.owner_id
        for league_id in orphan_league_ids
        for roster in rosters_by_league_id.get(
            league_id,
            [],
        )
        if roster.owner_id
    }

    users_by_id = await get_users(
        db,
        owner_ids,
    )

    orphan_cards: list[CommissionerOrphanRoster] = []

    for league_id in orphan_league_ids:
        league = leagues_by_id[league_id]
        rosters = rosters_by_league_id.get(
            league_id,
            [],
        )

        all_player_ids = [
            player_id
            for roster in rosters
            for player_id in (roster.players or [])
        ]

        player_values = await build_league_player_values(
            db=db,
            league=league,
            player_ids=all_player_ids,
            value_basis=value_basis,
        )

        player_by_id = {
            player.player_id: player
            for player in player_values
        }

        roster_name_by_id = build_roster_name_by_id(
            rosters=rosters,
            users_by_id=users_by_id,
        )

        unresolved_pick_assets_by_roster_id = (
            build_owned_pick_assets_by_roster_id(
                league=league,
                rosters=rosters,
                drafts=drafts_by_league_id.get(
                    league_id,
                    [],
                ),
                traded_picks=traded_picks_by_league_id.get(
                    league_id,
                    [],
                ),
                roster_name_by_id=roster_name_by_id,
            )
        )

        all_pick_assets = [
            pick
            for picks in unresolved_pick_assets_by_roster_id.values()
            for pick in picks
        ]

        resolved_pick_values_by_key = (
            await get_resolved_pick_values_by_key(
                db,
                picks=all_pick_assets,
                value_basis=value_basis,
                league_num_qbs=(
                    2
                    if "SUPER_FLEX" in (league.roster_positions or [])
                    else 1
                ),
                league_total_rosters=league.total_rosters,
                league_ppr=int(
                    round(
                        float(
                            (league.scoring_settings or {}).get(
                                "rec",
                                1,
                            ) or 1
                        )
                    )
                ),
            )
        )

        pick_assets_by_roster_id = (
            build_owned_pick_assets_by_roster_id(
                league=league,
                rosters=rosters,
                drafts=drafts_by_league_id.get(
                    league_id,
                    [],
                ),
                traded_picks=traded_picks_by_league_id.get(
                    league_id,
                    [],
                ),
                roster_name_by_id=roster_name_by_id,
                resolved_values_by_pick_key=resolved_pick_values_by_key,
            )
        )

        roster_value_totals: dict[int, float] = {}
        orphan_rosters = []

        for roster in rosters:
            commissioner_players = [
                to_commissioner_player(
                    player_by_id[player_id],
                    value_basis,
                )
                for player_id in (roster.players or [])
                if player_id in player_by_id
            ]

            roster_value_totals[roster.roster_id] = round(
                sum(
                    player.selected_value or 0.0
                    for player in commissioner_players
                ),
                2,
            )
            roster_value_totals[roster.roster_id] += round(
                sum(
                    pick.selected_value or 0.0
                    for pick in pick_assets_by_roster_id.get(
                        roster.roster_id,
                        [],
                    )
                ),
                2,
            )

            if roster.owner_id is None:
                orphan_rosters.append(
                    (
                        roster,
                        commissioner_players,
                    )
                )

        league_average_value = round(
            sum(roster_value_totals.values())
            / max(len(roster_value_totals), 1),
            2,
        )

        for roster, commissioner_players in orphan_rosters:
            lineup, bench = build_mock_lineup(
                roster_positions=league.roster_positions or [],
                players=commissioner_players,
            )

            orphan_cards.append(
                CommissionerOrphanRoster(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_season=league.season,
                    roster_id=roster.roster_id,
                    roster_name=f"Team {roster.roster_id}",
                    settings_badges=build_settings_badges(
                        league,
                    ),
                    roster_value=roster_value_totals.get(
                        roster.roster_id,
                        0.0,
                    ),
                    league_average_value=league_average_value,
                    average_age=get_average_age(
                        commissioner_players,
                    ),
                    lineup=lineup,
                    bench=bench,
                    picks=pick_assets_by_roster_id.get(
                        roster.roster_id,
                        [],
                    ),
                )
            )

    orphan_cards.sort(
        key=lambda orphan: orphan.roster_value,
        reverse=True,
    )

    return CommissionerOrphansResponse(
        username=username,
        value_basis=value_basis,
        value_label=get_value_label(value_basis),
        orphans=orphan_cards,
    )
