from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.analytics.war.dynasty.factory import build_dynasty_war_service
from app.analytics.war.redraft.singleton import war_service
from app.crud.sleeper.draft import (
    get_drafts_by_league_ids,
    get_traded_picks_by_league_ids,
)
from app.crud.sleeper.league import get_league_with_rosters
from app.crud.sleeper.user import get_users
from app.crud.value import get_player_values
from app.models.db.fc.models import FantasyCalcValue
from app.services.draft.picks import (
    build_owned_pick_assets_by_roster_id,
    build_roster_name_by_id,
)
from app.services.draft.values import get_resolved_pick_values_by_key
from app.services.leagues.models import (
    LeagueDetailsResponse,
    LeagueOwner,
    LeaguePick,
    LeaguePlayer,
    LeagueRoster,
    LeagueSettingsDetail,
)
from app.services.values.basis import ValueBasis
from app.services.waivers.dynasty import build_dynasty_projection


def build_settings_badges(league) -> list[str]:
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


def build_settings_details(league) -> list[LeagueSettingsDetail]:
    settings = league.settings or {}
    scoring = league.scoring_settings or {}
    roster_positions = league.roster_positions or []

    starter_count = sum(
        slot not in {"BN", "IR", "TAXI"}
        for slot in roster_positions
    )

    roster_size = (
        len(roster_positions)
        + int(settings.get("reserve_slots", 0) or 0)
        + int(settings.get("taxi_slots", 0) or 0)
    )

    details = [
        ("Season", str(league.season)),
        ("Format", "Superflex" if "SUPER_FLEX" in roster_positions else "1QB"),
        ("Lineup", "Best Ball" if settings.get("best_ball") == 1 else "Managed"),
        ("Teams", str(league.total_rosters)),
        ("Starters", str(starter_count)),
        ("Roster Size", str(roster_size)),
        ("Draft Rounds", str(int(settings.get("draft_rounds", 4) or 4))),
        ("Playoff Teams", str(int(settings.get("playoff_teams", 6) or 6))),
        ("FAAB", str(int(settings.get("waiver_budget", 100) or 100))),
        ("Taxi", str(int(settings.get("taxi_slots", 0) or 0))),
        ("Reserve", str(int(settings.get("reserve_slots", 0) or 0))),
        ("PPR", str(scoring.get("rec", 0) or 0)),
        ("Pass TD", str(scoring.get("pass_td", 4) or 4)),
    ]

    tep = scoring.get("bonus_rec_te", 0)
    if tep and tep > 0:
        details.append(("TE Premium", str(tep)))

    trade_deadline = settings.get("trade_deadline")
    if trade_deadline:
        details.append(("Trade Deadline", str(trade_deadline)))

    return [
        LeagueSettingsDetail(label=label, value=value)
        for label, value in details
    ]


def is_slot_eligible(slot: str, position: str | None) -> bool:
    if position is None:
        return False
    if slot == "SUPER_FLEX":
        return position in {"QB", "RB", "WR", "TE"}
    if slot == "FLEX":
        return position in {"RB", "WR", "TE"}
    return position == slot


def calculate_projected_starter_points(
    *,
    roster_positions: list[str],
    players: list[LeaguePlayer],
) -> float:
    starters = [
        slot
        for slot in roster_positions
        if slot not in {"BN", "IR", "TAXI"}
    ]

    remaining = sorted(
        players,
        key=lambda player: (
            player.projected_points
            if player.projected_points is not None
            else float("-inf")
        ),
        reverse=True,
    )

    total = 0.0

    for slot in starters:
        match = next(
            (
                player
                for player in remaining
                if is_slot_eligible(
                    slot,
                    player.position,
                )
            ),
            None,
        )

        if match is None:
            continue

        remaining.remove(match)
        total += match.projected_points or 0.0

    return round(total, 2)


def calculate_average_age(
    players: list[LeaguePlayer],
) -> float | None:
    ages = [
        player.age
        for player in players
        if player.age is not None
    ]

    if not ages:
        return None

    return round(sum(ages) / len(ages), 1)


class LeagueDetails:
    def __init__(self):
        self.war_service = war_service

    async def get_league_details(
        self,
        db: AsyncSession,
        redis,
        league_id: str,
    ):
        leagues = await get_league_with_rosters(
            db,
            league_id,
        )

        if not leagues:
            return None

        league = leagues[0][0]
        roster_rows = [roster for _, roster in leagues]

        shared = await self.war_service.load_shared_data(
            db,
            int(league.season),
        )

        war_players = await self.war_service.calculate_with_data(
            league=league,
            shared=shared,
        )

        war_lookup = {
            player.player_id: player
            for player in war_players
        }

        dynasty_service = build_dynasty_war_service()
        dynasty_war_by_player_id = {}

        for war_player in war_players:
            if war_player.player_id in dynasty_war_by_player_id:
                continue

            projection = build_dynasty_projection(
                player_war=war_player,
                dynasty_service=dynasty_service,
            )

            if projection is not None:
                dynasty_war_by_player_id[
                    war_player.player_id
                ] = projection

        player_ids = set()
        owner_ids = set()

        for roster in roster_rows:
            player_ids.update(roster.players or [])
            if roster.owner_id:
                owner_ids.add(roster.owner_id)

        users = await get_users(
            db,
            owner_ids,
        )

        player_values = await get_player_values(
            db,
            player_ids,
            war_players,
            dynasty_war_by_player_id=dynasty_war_by_player_id,
        )

        player_map = {
            player.player_id: player
            for player in player_values
        }

        num_qbs = (
            2
            if "SUPER_FLEX" in (league.roster_positions or [])
            else 1
        )
        ppr = int(
            round(
                float(
                    (league.scoring_settings or {}).get(
                        "rec",
                        1,
                    ) or 1
                )
            )
        )

        fantasycalc_rows = await db.execute(
            select(FantasyCalcValue).where(
                FantasyCalcValue.player_id.in_(player_ids),
                FantasyCalcValue.is_dynasty == True,
                FantasyCalcValue.num_qbs == num_qbs,
                FantasyCalcValue.num_teams == league.total_rosters,
                FantasyCalcValue.ppr == ppr,
            )
        )

        fantasycalc_by_player_id = {
            row.player_id: row
            for row in fantasycalc_rows.scalars().all()
        }

        roster_name_by_id = build_roster_name_by_id(
            rosters=roster_rows,
            users_by_id=users,
        )

        drafts_by_league_id = await get_drafts_by_league_ids(
            db,
            [league_id],
        )
        traded_picks_by_league_id = await get_traded_picks_by_league_ids(
            db,
            [league_id],
        )

        raw_pick_assets_by_roster_id = build_owned_pick_assets_by_roster_id(
            league=league,
            rosters=roster_rows,
            drafts=drafts_by_league_id.get(league_id, []),
            traded_picks=traded_picks_by_league_id.get(league_id, []),
            roster_name_by_id=roster_name_by_id,
        )

        all_pick_assets = [
            pick
            for picks in raw_pick_assets_by_roster_id.values()
            for pick in picks
        ]

        fc_pick_values_by_key = await get_resolved_pick_values_by_key(
            db,
            picks=all_pick_assets,
            value_basis=ValueBasis.FANTASYCALC,
            league_num_qbs=num_qbs,
            league_total_rosters=league.total_rosters,
            league_ppr=ppr,
        )

        ktc_pick_values_by_key = await get_resolved_pick_values_by_key(
            db,
            picks=all_pick_assets,
            value_basis=ValueBasis.KTC,
            league_num_qbs=num_qbs,
            league_total_rosters=league.total_rosters,
            league_ppr=ppr,
        )

        rosters: list[LeagueRoster] = []

        for roster in roster_rows:
            starter_ids = set(roster.starters or [])

            starter_order = {
                player_id: index
                for index, player_id in enumerate(roster.starters or [])
            }

            roster_players: list[LeaguePlayer] = []

            for player_id in roster.players or []:
                player = player_map.get(player_id)
                if player is None:
                    continue

                fc_row = fantasycalc_by_player_id.get(player_id)

                roster_players.append(
                    LeaguePlayer(
                        player_id=player.player_id,
                        name=player.name,
                        position=player.position,
                        team=player.team,
                        age=player.age,
                        underdog_position_rank=player.underdog_position_rank,
                        projected_points=round(
                            war_lookup[player_id].projection,
                            2,
                        ) if player_id in war_lookup else None,
                        ktc_value=player.ktc_value,
                        fc_value=player.fc_value,
                        fc_trend_30_day=(
                            fc_row.trend_30_day
                            if fc_row is not None
                            else None
                        ),
                        redraft_starter_war=player.redraft_starter_war,
                        redraft_roster_war=player.redraft_roster_war,
                        dynasty_starter_war=player.dynasty_starter_war,
                        dynasty_roster_war=player.dynasty_roster_war,
                        is_starter=player_id in starter_ids,
                    )
                )

            roster_players.sort(
                key=lambda player: (
                    0 if player.is_starter else 1,
                    starter_order.get(player.player_id, 999),
                    -(
                        player.projected_points
                        if player.projected_points is not None
                        else -1
                    ),
                    player.name,
                ),
            )

            picks = []
            total_pick_fc_value = 0.0
            total_pick_ktc_value = 0.0

            for pick in raw_pick_assets_by_roster_id.get(
                roster.roster_id,
                [],
            ):
                key = (
                    pick.season,
                    pick.round,
                    pick.og_roster_id,
                )

                fc_pick_value = fc_pick_values_by_key.get(key)
                ktc_pick_value = ktc_pick_values_by_key.get(key)

                fc_value = (
                    fc_pick_value.value
                    if fc_pick_value is not None
                    else None
                )
                ktc_value = (
                    ktc_pick_value.value
                    if ktc_pick_value is not None
                    else None
                )

                total_pick_fc_value += fc_value or 0.0
                total_pick_ktc_value += ktc_value or 0.0

                picks.append(
                    LeaguePick(
                        season=pick.season,
                        round=pick.round,
                        og_roster_id=pick.og_roster_id,
                        current_owner_roster_id=pick.current_owner_roster_id,
                        label=pick.label,
                        slot=pick.slot,
                        fc_value=fc_value,
                        ktc_value=ktc_value,
                    )
                )

            total_ktc_value = round(
                sum(player.ktc_value or 0 for player in roster_players),
                2,
            )
            total_fc_value = round(
                sum(player.fc_value or 0 for player in roster_players),
                2,
            )
            total_redraft_starter_war = round(
                sum(player.redraft_starter_war or 0 for player in roster_players),
                2,
            )
            total_redraft_roster_war = round(
                sum(player.redraft_roster_war or 0 for player in roster_players),
                2,
            )
            total_dynasty_starter_war = round(
                sum(player.dynasty_starter_war or 0 for player in roster_players),
                2,
            )
            total_dynasty_roster_war = round(
                sum(player.dynasty_roster_war or 0 for player in roster_players),
                2,
            )

            owner = users.get(roster.owner_id) if roster.owner_id else None

            rosters.append(
                LeagueRoster(
                    roster_id=roster.roster_id,
                    owner=LeagueOwner(
                        user_id=owner.user_id if owner else None,
                        display_name=(
                            owner.display_name
                            if owner is not None
                            else f"Team {roster.roster_id}"
                        ),
                        avatar=owner.avatar if owner else None,
                    ),
                    rank=0,
                    record=f"{roster.wins}-{roster.losses}" + (
                        f"-{roster.ties}"
                        if roster.ties
                        else ""
                    ),
                    wins=roster.wins,
                    losses=roster.losses,
                    ties=roster.ties,
                    actual_points_for=round(roster.fpts, 2),
                    projected_points=calculate_projected_starter_points(
                        roster_positions=league.roster_positions or [],
                        players=roster_players,
                    ),
                    faab_remaining=roster.faab_remaining(league),
                    waiver_position=roster.waiver_position,
                    total_moves=roster.total_moves,
                    open_roster_spots=roster.open_roster_spots(league),
                    average_age=calculate_average_age(roster_players),
                    total_ktc_value=total_ktc_value,
                    total_fc_value=total_fc_value,
                    total_redraft_starter_war=total_redraft_starter_war,
                    total_redraft_roster_war=total_redraft_roster_war,
                    total_dynasty_starter_war=total_dynasty_starter_war,
                    total_dynasty_roster_war=total_dynasty_roster_war,
                    total_pick_ktc_value=round(total_pick_ktc_value, 2),
                    total_pick_fc_value=round(total_pick_fc_value, 2),
                    total_asset_ktc_value=round(total_ktc_value + total_pick_ktc_value, 2),
                    total_asset_fc_value=round(total_fc_value + total_pick_fc_value, 2),
                    players=roster_players,
                    picks=sorted(
                        picks,
                        key=lambda pick: (
                            int(pick.season),
                            pick.round,
                            pick.slot if pick.slot is not None else 999,
                            pick.og_roster_id,
                        ),
                    ),
                )
            )

        rosters.sort(
            key=lambda roster: (
                roster.total_asset_ktc_value,
                roster.total_asset_fc_value,
                roster.total_dynasty_roster_war,
            ),
            reverse=True,
        )

        for rank, roster in enumerate(rosters, start=1):
            roster.rank = rank

        return LeagueDetailsResponse(
            league_id=league.league_id,
            league_name=league.name,
            season=str(league.season),
            total_rosters=league.total_rosters,
            settings_badges=build_settings_badges(league),
            settings_details=build_settings_details(league),
            rosters=rosters,
        )
