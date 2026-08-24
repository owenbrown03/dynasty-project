import logging
import random
from collections import defaultdict
from dataclasses import dataclass

from app.api.deps import ContextDep
from app.crud.fc.picks import get_fantasycalc_pick_values
from app.crud.sleeper.league import get_league_with_rosters
from app.crud.sleeper.player import get_player_map_for_ids
from app.crud.sleeper.trade import (
    get_trade_signals,
    get_user_meta_map,
)
from app.crud.sleeper.user import get_userid_by_username
from app.schemas.advisor import (
    AdvisorDossier,
    AdvisorPickRef,
    AdvisorPlayerRef,
    AdvisorProposal,
    AdvisorRosterContext,
    AdvisorSignalSummary,
)
from app.schemas.draft import DraftPickAsset
from app.schemas.personal_values import PersonalValuePoolItem
from app.services.draft.values import (
    resolve_fantasycalc_pick_value,
)
from app.services.personal_values import get_personal_value_pool
from app.services.advisor.strategy import (
    BASIS_ACTUAL_POINTS,
    is_season_altering_injury,
    BASIS_PROJECTED_WAR,
    COMPETE,
    HOARD_PICKS,
    REBUILD,
    WIN_NOW,
    LeagueStrategy,
    detect_strategy,
    strategy_from_manager_note,
)
from app.services.trades.waiver import build_waiver_credit_ladder
from app.services.advisor.trade_block import (
    get_trade_block_snapshot,
)
from app.services.trades.waiver import (
    load_waiver_ladder,
    split_waiver_credits,
)
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)

logger = logging.getLogger(__name__)

MAX_LEAGUES = 6
# Bumped whenever candidate-engine semantics change in a way that
# should invalidate cached syntheses (value bases, constraint math,
# package shapes). The synthesis cache identity includes this.
ADVISOR_ENGINE_VERSION = 7

# How many of my top market-value players count as "stars" for the
# contender-lost-a-star injury directive.
CONTENDER_STAR_POOL = 3
ANCHOR_POOL_SIZE = 8  # kept for sell-pool context sizing
TARGET_POOL_SIZE = 60
MAX_PROPOSALS_PER_LEAGUE = 6
# Market value is FantasyCalc: unlike KTC it has no imbalance adder,
# so multi-asset package totals stay additive. A proposal must be
# convincing for the COUNTERPARTY: we always send at least even
# market value, ideally more, so the other manager has a reason to
# accept. Our edge comes solely from the personal value system (see
# _passes_value_constraints).
COUNTERPARTY_MARKET_MIN_RATIO = 1.0
COUNTERPARTY_MARKET_MAX_RATIO = 2.0
PERSONAL_EDGE_TOLERANCE = 1e-9
SIGNAL_SUMMARY_LIMIT = 15
PICK_ROUNDS = 4
PICK_SEASON_WINDOW = 3


@dataclass
class PickAsset:
    """One original draft pick with its current owner and value.

    value is the FantasyCalc market price; war_value is the same
    pick on the personal-WAR scale so picks can be compared with
    players inside personal totals.
    """

    season: str
    round: int
    og_roster_id: int
    owner_roster_id: int
    value: float | None = None
    war_value: float | None = None
    on_block: bool = False

    @property
    def key(self) -> tuple[int, str, int]:
        return (self.round, self.season, self.og_roster_id)


def _market_value(
    item: PersonalValuePoolItem,
) -> float | None:
    value = item.player.fc_value

    if value is None:
        return None

    return float(value)


def _delta_war(item: PersonalValuePoolItem) -> float | None:
    metrics = item.delta_values.dynasty_roster_war

    if metrics is None:
        return item.delta_values.redraft_roster_war

    return metrics


def _personal_war(item: PersonalValuePoolItem) -> float | None:
    war = item.custom_values.dynasty_roster_war

    if war is None:
        return item.custom_values.redraft_roster_war

    return war


def _market_war(item: PersonalValuePoolItem) -> float | None:
    war = item.market_values.dynasty_roster_war

    if war is None:
        return item.market_values.redraft_roster_war

    return war


def _to_ref(
    item: PersonalValuePoolItem,
    *,
    on_block: bool = False,
) -> AdvisorPlayerRef:
    return AdvisorPlayerRef(
        player_id=item.player.player_id,
        name=item.player.name,
        position=item.player.position,
        team=item.player.team,
        age=item.player.age,
        injury_status=item.player.injury_status,
        market_value=_market_value(item),
        personal_war=_personal_war(item),
        market_war=_market_war(item),
        delta_war=_delta_war(item),
        on_block=on_block,
    )


async def build_advisor_dossier(
    ctx: ContextDep,
    username: str,
    league_id: str | None = None,
    force: bool = False,
) -> AdvisorDossier:
    main_user_id = await get_userid_by_username(
        ctx.db,
        ctx.sleeper,
        username,
    )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=main_user_id,
        site_user_id=ctx.site_user.id if ctx.site_user else None,
        include_hidden=False,
    )

    if league_id is not None:
        owned_rows = [
            row
            for row in owned_rows
            if row.league.league_id == league_id
        ]

    selected = owned_rows[:MAX_LEAGUES]

    league_notes: dict[str, str] = {}
    if ctx.site_user is not None:
        try:
            from app.crud.sleeper.personal import (
                get_user_notes_by_league_id,
            )

            notes = await get_user_notes_by_league_id(
                db=ctx.db,
                site_user_id=ctx.site_user.id,
                league_ids=[
                    row.league.league_id for row in selected
                ],
            )
            league_notes = {
                league_id: note.note
                for league_id, note in notes.items()
                if note.note
            }
        except Exception:
            logger.exception(
                "Advisor league-notes fetch failed",
            )

    proposals: list[AdvisorProposal] = []
    roster_contexts: list[AdvisorRosterContext] = []

    for row in selected:
        league = row.league
        my_roster = row.roster
        try:
            await _build_league_candidates(
                ctx,
                league=league,
                my_roster=my_roster,
                manager_note=league_notes.get(
                    league.league_id,
                ),
                proposals=proposals,
                roster_contexts=roster_contexts,
                force=force,
            )
        except Exception:
            logger.exception(
                "Advisor candidate build failed "
                "league=%s",
                league.league_id,
            )
            continue

    signals = await _summarize_signals(ctx, username)

    return AdvisorDossier(
        username=username,
        proposals=proposals,
        roster_contexts=roster_contexts,
        signals=signals,
        scope_league_id=league_id,
    )


async def _build_league_candidates(
    ctx: ContextDep,
    *,
    league,
    my_roster,
    manager_note: str | None = None,
    proposals: list[AdvisorProposal],
    roster_contexts: list[AdvisorRosterContext],
    force: bool = False,
) -> None:
    pool = await get_personal_value_pool(
        ctx=ctx,
        league_id=league.league_id,
    )

    my_player_ids = set(my_roster.players or [])
    if not my_player_ids:
        return

    items_by_player_id: dict[str, PersonalValuePoolItem] = {}
    for group in pool.groups:
        for item in group.players:
            items_by_player_id[item.player.player_id] = item

    my_items = [
        items_by_player_id[pid]
        for pid in my_player_ids
        if pid in items_by_player_id
    ]

    league_rosters = await get_league_with_rosters(
        ctx.db,
        league.league_id,
    )
    owner_names = await get_user_meta_map(ctx.db)

    try:
        snapshot = await get_trade_block_snapshot(
            ctx,
            league.league_id,
        )
    except Exception:
        logger.exception(
            "Advisor trade-block fetch failed league=%s",
            league.league_id,
        )
        from app.services.advisor.trade_block import (
            TradeBlockSnapshot,
        )

        snapshot = TradeBlockSnapshot()

    chests = await _build_pick_chests(
        ctx,
        league=league,
        season=pool.context.season,
        total_rosters=pool.context.total_rosters,
        league_rosters=league_rosters,
        blocked_pick_keys=set(snapshot.picks.keys()),
    )

    # An explicit direction in the manager's note is ground truth;
    # numeric detection only runs when the note declares nothing.
    strategy = strategy_from_manager_note(manager_note)
    strategies_by_roster_id: dict[int, LeagueStrategy] = {}

    if strategy is None:
        (
            strategy,
            strategies_by_roster_id,
        ) = await _detect_league_strategy(
            ctx,
            league=league,
            my_roster=my_roster,
            league_rosters=league_rosters,
            my_items=my_items,
            items_by_player_id=items_by_player_id,
            chests=chests,
        )

    roster_contexts.append(
        await _build_roster_context(
            ctx,
            league=league,
            my_roster=my_roster,
            pool_context=pool.context,
            my_items=my_items,
            strategy=strategy,
            manager_note=manager_note,
        ),
    )

    # Trade-block signal first: a leaguemate explicitly shopping an
    # asset is the strongest availability marker we have. Strategy
    # then reshapes both pools (see _apply_strategy_ordering).
    buy_pool = [
        i
        for p, i in items_by_player_id.items()
        if p not in my_player_ids and _market_value(i)
    ]
    sell_pool_full = [
        item
        for item in my_items
        if _market_value(item)
    ]
    sell_pool, buy_pool = _apply_strategy_ordering(
        strategy=strategy.strategy if strategy else None,
        sell=sell_pool_full,
        buy=buy_pool,
        blocked_ids=set(snapshot.player_ids),
    )

    # Contender lost a star: a top asset with a season-altering injury
    # is dead roster weight for a win-now push; surface packages that
    # convert it into usable production first. Stable sort preserves
    # the strategy ordering within each band.
    if strategy is not None and strategy.strategy == WIN_NOW:
        injured_star_ids = {
            item.player.player_id
            for item in sorted(
                my_items,
                key=lambda i: -(_market_value(i) or 0.0),
            )[:CONTENDER_STAR_POOL]
            if is_season_altering_injury(item.player.injury_status)
        }

        if injured_star_ids:
            sell_pool.sort(
                key=lambda i: (
                    0
                    if i.player.player_id in injured_star_ids
                    else 1
                ),
            )

    # Rebuilder buy-low: season-altering injuries crater market prices
    # on players whose dynasty value survives the year. Surface those
    # discounted upside targets first when we are selling the present.
    if strategy is not None and strategy.strategy == REBUILD:
        injured_buy_ids = {
            item.player.player_id
            for item in buy_pool
            if is_season_altering_injury(
                item.player.injury_status,
            )
        }

        if injured_buy_ids:
            buy_pool.sort(
                key=lambda i: (
                    0
                    if i.player.player_id in injured_buy_ids
                    else 1
                ),
            )

    if not sell_pool or not buy_pool:
        return

    # Search every rostered non-mine player as a potential target.
    # The loop is pure local math (WAR/value constraints, no API
    # calls) so there is no cost to being exhaustive. The token
    # budget is controlled by MAX_PROPOSALS_PER_LEAGUE which caps
    # how many proposals actually reach Gemini.
    #
    # On forced regeneration, shuffle the full buy_pool so a
    # different ordering explores candidates in a different sequence,
    # producing genuinely different proposals instead of the same
    # top-ranked set reworded with a hotter temperature.
    targets = list(buy_pool)
    if force:
        random.shuffle(targets)

    # Soft counterparty-fit ranking: complement directions first so
    # scarce proposal slots go to realistic partners. Stable sort keeps
    # market-value ordering inside each band.
    roster_by_id = {r.roster_id: r for _, r in league_rosters}
    strategy_by_target = {}

    for item in targets:
        owner_roster = _find_roster_of_player(
            league_rosters,
            item.player.player_id,
            exclude_owner=my_roster.owner_id,
        )
        strategy_by_target[item.player.player_id] = (
            strategies_by_roster_id.get(owner_roster.roster_id)
            if owner_roster is not None
            else None
        )

    targets.sort(
        key=lambda i: _counterparty_rank(
            strategy_by_target.get(i.player.player_id),
            strategy,
        ),
    )


    my_picks = sorted(
        (
            p
            for p in chests.get(my_roster.roster_id, [])
            if p.value is not None
        ),
        key=lambda p: p.value or 0.0,
    )

    # Pick-hoarding never ships its own draft capital.
    if strategy and strategy.strategy == HOARD_PICKS:
        my_picks = []

    # Waiver-adjustment ladder: FC-style credit for the bench spot
    # a side loses when it ships more players than it receives.
    try:
        waiver_ladder = await load_waiver_ladder(
            ctx.db,
            total_rosters=pool.context.total_rosters,
            num_qbs=_league_num_qbs(league),
            ppr=_league_ppr(league),
            roster_slots=league.roster_size,
        )
    except Exception:
        logger.exception(
            "Advisor waiver-ladder load failed league=%s",
            league.league_id,
        )
        waiver_ladder = []

    war_ladder = _build_war_waiver_ladder(
        items=list(items_by_player_id.values()),
        total_rosters=pool.context.total_rosters,
        roster_slots=league.roster_size,
    )


    made_for_this_league = 0
    seen_target_ids: set[str] = set()

    for target in targets:
        if made_for_this_league >= MAX_PROPOSALS_PER_LEAGUE:
            break

        if target.player.player_id in seen_target_ids:
            continue

        seen_target_ids.add(target.player.player_id)

        target_roster = _find_roster_of_player(
            league_rosters,
            target.player.player_id,
            exclude_owner=my_roster.owner_id,
        )

        if target_roster is None:
            continue

        target_market = _market_value(target)

        if target_market is None:
            continue

        owner_id = target_roster.owner_id
        their_picks = [
            p
            for p in chests.get(target_roster.roster_id, [])
            if p.value is not None
        ]

        package_players, package_picks = _match_package(
            sell_pool,
            my_picks,
            target_market=_market_value(target),
        )

        if package_players is None:
            continue

        market_send_total = _sum_market(package_players) + sum(
            p.value or 0.0 for p in package_picks
        )
        personal_send_total = _personal_total_with_picks(
            package_players,
            package_picks,
        )
        market_receive_total = float(target_market)
        personal_receive_total = _personal_war(target)

        counterparty_strategy = strategies_by_roster_id.get(
            target_roster.roster_id,
        )

        # Rebuilders hoard draft capital; asking them to ship picks
        # produces dead-on-arrival offers regardless of market math.
        # Exception: bottom-ranked teams with an old, unsold core
        # behave like contenders — their firsts are fair game.
        rebuild_picks_locked = (
            counterparty_strategy is not None
            and counterparty_strategy.strategy == REBUILD
            and not _rebuilder_behaves_like_contender(
                strategy=counterparty_strategy,
                target_roster=target_roster,
                items_by_player_id=items_by_player_id,
                blocked_ids=set(snapshot.player_ids),
            )
        )

        if counterparty_strategy is not None and (
            counterparty_strategy.strategy == REBUILD
        ):
            requestable_their_picks = (
                [] if rebuild_picks_locked else their_picks
            )
        elif counterparty_strategy is not None and (
            counterparty_strategy.strategy == WIN_NOW
        ):
            # Real contenders rarely move firsts (and theirs are
            # late). Soft downrank: skip pick-fixups against them;
            # base all-player packages still proceed.
            requestable_their_picks = []
        else:
            requestable_their_picks = their_picks

        extra_receive_pick = _fix_with_extra_receive_pick(
            their_picks=requestable_their_picks,
            market_send_total=market_send_total,
            market_receive_total=market_receive_total,
            personal_send_total=personal_send_total,
            personal_receive_total=personal_receive_total,
        )

        if extra_receive_pick is not None:
            market_receive_total += (
                extra_receive_pick.value or 0.0
            )
            personal_receive_total = (
                personal_receive_total
                + (extra_receive_pick.value or 0.0)
                if personal_receive_total is not None
                else None
            )

        my_credit, their_credit = split_waiver_credits(
            my_players_out=len(package_players),
            their_players_out=1,
            ladder=waiver_ladder,
        )

        my_credit_war, their_credit_war = split_waiver_credits(
            my_players_out=len(package_players),
            their_players_out=1,
            ladder=war_ladder,
        )

        if not _passes_value_constraints(
            market_send_total=market_send_total
            + (my_credit or 0.0),
            market_receive_total=market_receive_total
            + (their_credit or 0.0),
            personal_send_total=personal_send_total,
            personal_receive_total=personal_receive_total,
            my_waiver_credit_war=my_credit_war,
        ):
            continue


        counterparty_name = owner_names.get(owner_id, {}).get(
            "name",
            "Unknown",
        )

        target_on_block = (
            target.player.player_id in snapshot.player_ids
        )

        receive_refs = [
            _to_ref(target, on_block=target_on_block)
        ]

        proposals.append(
            AdvisorProposal(
                league_id=league.league_id,
                league_name=pool.context.league_name,
                counterparty_id=owner_id,
                counterparty_name=counterparty_name,
                send=[
                    _to_ref(i) for i in package_players
                ],
                receive=receive_refs,
                send_picks=[
                    _to_pick_ref(p) for p in package_picks
                ],
                receive_picks=(
                    [_to_pick_ref(extra_receive_pick)]
                    if extra_receive_pick is not None
                    else []
                ),
                market_send_total=market_send_total,
                market_receive_total=market_receive_total,
                personal_send_total=personal_send_total,
                personal_receive_total=personal_receive_total,
                your_roster_id=my_roster.roster_id,
                counterparty_roster_id=target_roster.roster_id,
                strategy=(
                    strategy.strategy if strategy else None
                ),
                counterparty_strategy=(
                    counterparty_strategy.strategy
                    if counterparty_strategy
                    else None
                ),
                counterparty_strategy_reason=(
                    counterparty_strategy.reason
                    if counterparty_strategy
                    else None
                ),
                counterparty_fringe=bool(
                    counterparty_strategy
                    and counterparty_strategy.fringe
                ),
                my_waiver_credit=my_credit,
                their_waiver_credit=their_credit,
                my_waiver_credit_war=my_credit_war,
                their_waiver_credit_war=their_credit_war,
            ),
        )
        made_for_this_league += 1


def _league_num_qbs(league) -> int:
    return (
        2
        if "SUPER_FLEX" in (league.roster_positions or [])
        else 1
    )


def _league_ppr(league) -> int:
    return int(
        round(
            float(
                (league.scoring_settings or {}).get(
                    "rec",
                    1,
                )
                or 1
            )
        )
    )


async def _build_pick_chests(
    ctx: ContextDep,
    *,
    league,
    season: int,
    total_rosters: int,
    league_rosters,
    blocked_pick_keys: set[tuple[int, str, int]],
) -> dict[int, list[PickAsset]]:
    """Derives every roster's tradable future-pick chest.

    Ownership model mirrors the bulk-trade send path: baseline is
    each roster owning its own original picks for the next
    PICK_SEASON_WINDOW seasons and PICK_ROUNDS rounds, overridden by
    Sleeper's live traded_picks state. Values are FantasyCalc pick
    values at the league's shape; picks without a value are kept but
    unusable in packages.
    """
    seasons = [str(season + i) for i in range(1, PICK_SEASON_WINDOW + 1)]
    rounds = list(range(1, PICK_ROUNDS + 1))

    owners: dict[tuple[int, str, int], int] = {
        (roster.roster_id, season_str, round_): roster.roster_id
        for _, roster in league_rosters
        for season_str in seasons
        for round_ in rounds
    }

    try:
        traded = await ctx.sleeper.read.get_traded_picks(
            league.league_id,
        )
    except Exception:
        logger.exception(
            "Advisor pick-chest fetch failed league=%s",
            league.league_id,
        )
        return {}

    for row in traded or []:
        key = (
            int(row.roster_id),
            str(row.season),
            int(row.round),
        )

        if key in owners and row.owner_id is not None:
            owners[key] = int(row.owner_id)

    fc_rows = await get_fantasycalc_pick_values(
        ctx.db,
        is_dynasty=True,
        num_qbs=_league_num_qbs(league),
        num_teams=total_rosters,
        ppr=_league_ppr(league),
        seasons=seasons,
        rounds=rounds,
    )

    chests: dict[int, list[PickAsset]] = defaultdict(list)

    for (og_roster_id, season_str, round_), owner_id in owners.items():
        pick = DraftPickAsset(
            season=season_str,
            round=round_,
            og_roster_id=og_roster_id,
            current_owner_roster_id=owner_id,
            label="",
        )
        resolved = resolve_fantasycalc_pick_value(
            pick=pick,
            rows=fc_rows.get((season_str, round_), []),
        )
        chests[owner_id].append(
            PickAsset(
                season=season_str,
                round=round_,
                og_roster_id=og_roster_id,
                owner_roster_id=owner_id,
                value=resolved.value,
                on_block=(
                    (round_, season_str, og_roster_id)
                    in blocked_pick_keys
                ),
            ),
        )

    # Personal-side values: picks must enter personal totals on the
    # WAR scale players use, not their FC price scale.
    try:
        from app.services.draft.rookie_war import (
            get_rookie_pick_war_values_by_key,
        )

        all_picks = [
            DraftPickAsset(
                season=p.season,
                round=p.round,
                og_roster_id=p.og_roster_id,
                current_owner_roster_id=p.owner_roster_id,
                label="",
            )
            for picks in chests.values()
            for p in picks
        ]
        war_values = await get_rookie_pick_war_values_by_key(
            ctx.db,
            picks=all_picks,
            league_total_rosters=total_rosters,
            league_scoring_settings=(
                league.scoring_settings or {}
            ),
            league_roster_positions=(
                league.roster_positions or []
            ),
            redis=ctx.redis,
        )

        for picks in chests.values():
            for p in picks:
                aggregate = war_values.get(
                    (p.season, p.round, p.og_roster_id),
                )
                if aggregate is not None:
                    p.war_value = aggregate.roster_war
    except Exception:
        logger.exception(
            "Advisor rookie-WAR pick valuation failed "
            "league=%s",
            league.league_id,
        )

    return dict(chests)


def _starter_ages(
    items: list[PersonalValuePoolItem],
) -> float | None:
    """Average age over each player's most valuable slice.

    Uses the top half of the roster by personal WAR as a proxy for
    the core that actually decides whether a team is contending.
    """
    valued = [
        (item, _personal_war(item) or 0.0)
        for item in items
        if item.player.age is not None
    ]

    if not valued:
        return None

    valued.sort(key=lambda pair: pair[1], reverse=True)
    core = valued[: max(1, len(valued) // 2)]

    return sum(
        item.player.age for item, _ in core
    ) / len(core)


def _starter_war(item: PersonalValuePoolItem) -> float | None:
    """Current-year projected strength for one player.

    Redraft starter WAR is the same current-season projection the
    dashboard's financial predictions use; dynasty starter WAR is
    the fallback when redraft has not been computed.
    """
    metrics = item.market_values

    war = metrics.redraft_starter_war
    if war is None:
        war = metrics.dynasty_starter_war

    if war is None:
        custom = item.custom_values
        war = (
            custom.redraft_starter_war
            if custom.redraft_starter_war is not None
            else custom.dynasty_starter_war
        )

    return war


async def _season_phase(sleeper) -> tuple[str, str]:
    """Returns (basis, label) for team-strength measurement.

    Actual points only mean something once real games have been
    played; before that we rank by projected starter WAR so the
    advisor never declares "rank 1 with 0 points" nonsense.
    """
    try:
        state = await sleeper.read.get_nfl_state()
        season_type = (state.season_type or "").lower()
        week = int(state.week or 0)

        if season_type == "regular" and week >= 1:
            return (
                BASIS_ACTUAL_POINTS,
                f"week {week}",
            )
    except Exception:
        logger.exception(
            "NFL state fetch failed; defaulting to "
            "projected strength",
        )

    return (
        BASIS_PROJECTED_WAR,
        "preseason",
    )


def _projected_roster_strength(
    player_ids: set[str],
    items_by_player_id: dict[str, PersonalValuePoolItem],
    starters: int,
) -> float:
    """Sums the best starters-sized slice of current-year WAR."""
    wars = sorted(
        (
            war
            for pid in player_ids
            if (item := items_by_player_id.get(pid))
            and (war := _starter_war(item)) is not None
        ),
        reverse=True,
    )
    return sum(wars[:starters])


async def _detect_league_strategy(
    ctx: ContextDep,
    *,
    league,
    my_roster,
    league_rosters,
    my_items: list[PersonalValuePoolItem],
    items_by_player_id: dict[str, PersonalValuePoolItem],
    chests: dict[int, list[PickAsset]],
) -> tuple[
    LeagueStrategy | None,
    dict[int, LeagueStrategy],
]:
    basis, _phase = await _season_phase(ctx.sleeper)

    starters = max(league.starter_slots, 1)

    if basis == BASIS_PROJECTED_WAR:
        # Preseason/offseason: no real production yet, so contention
        # follows the manager's redraft projection setting - total
        # redraft market value per roster (#165 phase 3).
        from app.crud.auth.session import (
            get_session_redraft_value_preference,
        )
        from app.crud.auth.user import get_redraft_value_preference
        from app.services.draft.projection import (
            build_redraft_value_by_roster_id,
        )

        if ctx.site_user is not None:
            redraft_basis = get_redraft_value_preference(
                ctx.site_user,
            ).value
        else:
            redraft_basis = get_session_redraft_value_preference(
                ctx.session,
            ).value

        redraft_value_by_roster_id = (
            await build_redraft_value_by_roster_id(
                ctx.db,
                [roster for _, roster in league_rosters],
                basis=redraft_basis,
            )
        )

        def strength(roster) -> float:
            return redraft_value_by_roster_id.get(
                roster.roster_id,
                0.0,
            )

    else:
        # In-season: actual points, ignoring rosters still at zero
        # so an empty column can't read as dominance.
        def strength(roster) -> float | None:
            if roster.fpts is None:
                return None

            value = float(roster.fpts)
            return value if value > 0 else None

    all_strengths = [
        strength(roster) for _, roster in league_rosters
    ]
    my_strength = next(
        (
            s
            for (_, roster), s in zip(
                league_rosters,
                all_strengths,
            )
            if roster.roster_id == my_roster.roster_id
        ),
        None,
    )

    league_items = list(items_by_player_id.values())
    league_starter_age = _starter_ages(league_items)
    league_avg_pick_count = (
        sum(len(v) for v in chests.values())
        / max(len(chests), 1)
    )

    items_by_roster_id = {
        roster.roster_id: [
            items_by_player_id[pid]
            for pid in (roster.players or [])
            if pid in items_by_player_id
        ]
        for _, roster in league_rosters
    }

    strategies_by_roster_id = {
        roster.roster_id: detect_strategy(
            my_strength=strength(roster),
            all_strengths=all_strengths,
            basis=basis,
            my_wins=roster.wins or 0,
            my_losses=roster.losses or 0,
            my_ties=roster.ties or 0,
            my_starter_age=_starter_ages(
                items_by_roster_id[roster.roster_id],
            ),
            league_starter_age=league_starter_age,
            my_pick_count=len(chests.get(roster.roster_id, [])),
            league_avg_pick_count=league_avg_pick_count,
        )
        for _, roster in league_rosters
    }

    return (
        strategies_by_roster_id.get(my_roster.roster_id),
        strategies_by_roster_id,
    )


def _rebuilder_behaves_like_contender(
    *,
    strategy: LeagueStrategy,
    target_roster,
    items_by_player_id: dict[str, PersonalValuePoolItem],
    blocked_ids: set[str],
) -> bool:
    """Bottom-ranked team with an OLD core that is NOT for sale.

    They think they can still compete because they are not selling,
    so their firsts are fair game despite the rebuild label.
    """
    if not strategy.bottom_two:
        return False

    starter_items = [
        items_by_player_id[pid]
        for pid in (target_roster.starters or [])
        if pid in items_by_player_id
    ]

    ages = [
        item.player.age
        for item in starter_items
        if item.player.age is not None
    ]
    if not ages or sum(ages) / len(ages) < 28.0:
        return False

    top_ids = {
        item.player.player_id
        for item in sorted(
            starter_items,
            key=lambda i: -(_market_value(i) or 0.0),
        )[:3]
    }

    # Unsold core: none of their top assets are on the block.
    return not (top_ids & blocked_ids)



def _counterparty_rank(
    their: LeagueStrategy | None,
    mine: LeagueStrategy | None,
) -> tuple[int, int]:
    """Soft preference order for trade targets.

    Lower sorts first. Complements our direction:
      - we are win_now -> rebuilders/hoarders sell us picks and youth;
        fringe teams sell us proven producers.
      - we are rebuilding -> contenders and fringe teams pay for our
        aging veterans.
      - otherwise neutral, fringe slightly ahead.
    """
    their_strategy = their.strategy if their else None
    fringe = bool(their and their.fringe)

    if mine is not None and mine.strategy == WIN_NOW:
        base = {
            REBUILD: 0,
            HOARD_PICKS: 1,
            COMPETE: 2,
            WIN_NOW: 3,
        }.get(their_strategy, 2)
    elif mine is not None and mine.strategy == REBUILD:
        base = {
            WIN_NOW: 0,
            COMPETE: 1,
            HOARD_PICKS: 2,
            REBUILD: 3,
        }.get(their_strategy, 2)
    else:
        base = 1

    return base, 0 if fringe else 1


def _apply_strategy_ordering(
    *,
    strategy: str | None,
    sell: list[PersonalValuePoolItem],
    buy: list[PersonalValuePoolItem],
    blocked_ids: set[str],
):
    """Reshapes candidate pools to serve the detected strategy.

    rebuild: shed the oldest market-valued assets; target blocked
      players first, then the youngest upside.
    win_now: move young depth; target proven older producers whose
      current WAR is real.
    hoard_picks/compete: keep the delta-WAR logic with trade-block
      priority on the buy side.
    """
    def age_or(item, default):
        return (
            item.player.age
            if item.player.age is not None
            else default
        )

    if strategy == REBUILD:
        sell.sort(
            key=lambda i: (
                -age_or(i, 0.0),
                -(_market_value(i) or 0.0),
            ),
        )
        buy.sort(
            key=lambda i: (
                i.player.player_id not in blocked_ids,
                age_or(i, 99.0),
                -(_delta_war(i) or 0.0),
            ),
        )
    elif strategy == WIN_NOW:
        sell.sort(
            key=lambda i: (
                age_or(i, 99.0),
                -(_delta_war(i) or 0.0),
            ),
        )
        buy.sort(
            key=lambda i: (
                -age_or(i, 0.0),
                i.player.player_id not in blocked_ids,
                -(max(_personal_war(i) or 0.0, 0.0)),
            ),
        )
    else:
        sell.sort(key=lambda i: _delta_war(i) or 0.0)
        buy.sort(
            key=lambda i: (
                i.player.player_id not in blocked_ids,
                -(_delta_war(i) or 0.0),
            ),
        )

    return sell, buy


def _find_roster_of_player(
    league_rosters,
    player_id: str,
    *,
    exclude_owner: str | None,
):
    for _, roster in league_rosters:
        if roster.owner_id == exclude_owner:
            continue

        if player_id in (roster.players or []):
            return roster

    return None


def _to_pick_ref(pick: PickAsset) -> AdvisorPickRef:
    return AdvisorPickRef(
        season=pick.season,
        round=pick.round,
        og_roster_id=pick.og_roster_id,
        market_value=pick.value,
        on_block=pick.on_block,
    )


def _personal_total_with_picks(
    players: list[PersonalValuePoolItem],
    picks: list[PickAsset],
) -> float | None:
    """Personal totals: players on WAR scale, picks on their
    rookie-WAR valuation so the two are commensurable."""
    player_total = _sum_or_none(players, _personal_war)

    if player_total is None:
        return None

    return player_total + sum(
        p.war_value or 0.0 for p in picks
    )


def _fix_with_extra_receive_pick(
    *,
    their_picks: list[PickAsset],
    market_send_total: float,
    market_receive_total: float,
    personal_send_total: float | None,
    personal_receive_total: float | None,
) -> PickAsset | None:
    """Crafty-shape fallback: sweeten OUR receive side.

    When a package would leave us personally underwater, adding one
    small pick from the counterparty can flip it into a personal win
    while still keeping their KTC gain inside the convincing band.
    """
    if (
        personal_send_total is None
        or personal_receive_total is None
    ):
        return None

    deficit = (
        personal_send_total
        - PERSONAL_EDGE_TOLERANCE
        - personal_receive_total
    )

    if deficit <= 0:
        return None

    for pick in sorted(
        their_picks,
        key=lambda p: p.war_value or 0.0,
    ):
        # The personal deficit closes on the WAR scale while the
        # counterparty's ratio band stays on the FC market scale.
        war_gain = pick.war_value or 0.0

        if war_gain < deficit:
            continue

        new_receive = market_receive_total + (
            pick.value or 0.0
        )

        ratio = market_send_total / new_receive

        if (
            COUNTERPARTY_MARKET_MIN_RATIO
            <= ratio
            <= COUNTERPARTY_MARKET_MAX_RATIO
        ):
            return pick

    return None


def _match_package(
    sell_pool: list[PersonalValuePoolItem],
    my_picks: list[PickAsset],
    *,
    target_market: float,
    used_player_ids: set[str] | None = None,
    used_pick_keys: set[tuple[int, str, int]] | None = None,
):
    """Picks our send package for a target player.

    Tiers, from most to least conventional: player single, player
    pair, player+pick, and pick-only. Within a tier the KTC total
    must land in [COUNTERPARTY_MARKET_MIN_RATIO, COUNTERPARTY_MARKET_MAX_RATIO]
    of the target's KTC and we prefer the SMALLEST qualifying ratio —
    convincing without reckless overpay.
    """
    used_player_ids = used_player_ids or set()
    used_pick_keys = used_pick_keys or set()

    players = [
        item
        for item in sell_pool
        if item.player.player_id not in used_player_ids
    ]
    picks = [
        p
        for p in my_picks
        if p.key not in used_pick_keys
        and p.value is not None
    ]

    best: tuple[float, list, list] | None = None

    def consider(
        candidate_players: list,
        candidate_picks: list,
    ) -> None:
        nonlocal best

        total = _sum_market(candidate_players) + sum(
            p.value or 0.0 for p in candidate_picks
        )
        ratio = total / target_market

        if not (
            COUNTERPARTY_MARKET_MIN_RATIO
            <= ratio
            <= COUNTERPARTY_MARKET_MAX_RATIO
        ):
            return

        if best is None or ratio < best[0]:
            best = (ratio, candidate_players, candidate_picks)

    for item in players:
        consider([item], [])

    if best is not None:
        return best[1], best[2]

    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            consider([players[i], players[j]], [])

    if best is not None:
        return best[1], best[2]

    for item in players:
        for pick in picks:
            consider([item], [pick])

        for i in range(len(picks)):
            for j in range(i + 1, len(picks)):
                consider([item], [picks[i], picks[j]])

    if best is not None:
        return best[1], best[2]

    for pick in picks:
        consider([], [pick])

    for i in range(len(picks)):
        for j in range(i + 1, len(picks)):
            consider([], [picks[i], picks[j]])

    if best is not None:
        return best[1], best[2]

    return None, []


def _passes_value_constraints(
    *,
    market_send_total: float,
    market_receive_total: float,
    personal_send_total: float | None,
    personal_receive_total: float | None,
    my_waiver_credit_war: float | None = None,
) -> bool:
    """Enforces the two-sided acceptance rules from the advisor spec.

    1. Counterparty-convincing: they receive at least even market value.
    2. We win or tie on OUR value system (never lose personally),
       counting the bench-spot refill credit from our own value ladder.
    """
    if (
        market_send_total
        < market_receive_total - PERSONAL_EDGE_TOLERANCE
    ):
        return False

    if (
        personal_send_total is None
        or personal_receive_total is None
    ):
        return False

    personal_receive_adjusted = personal_receive_total + (
        my_waiver_credit_war or 0.0
    )

    return (
        personal_receive_adjusted
        >= personal_send_total - PERSONAL_EDGE_TOLERANCE
    )


def _build_war_waiver_ladder(
    *,
    items: list[PersonalValuePoolItem],
    total_rosters: int,
    roster_slots: int,
) -> list[float]:
    """Waiver ladder denominated in the manager's own value system.

    Same cutline and step semantics as the FC ladder, but ranks come
    from personal-WAR ordering of the league's value pool instead of
    FantasyCalc's published ranking.
    """
    values_by_rank: dict[int, float] = {}

    ranked_items = sorted(
        (
            item
            for item in items
            if _personal_war(item) is not None
        ),
        key=lambda i: -(_personal_war(i) or 0.0),
    )

    for rank, item in enumerate(ranked_items, start=1):
        values_by_rank[rank] = _personal_war(item)

    return build_waiver_credit_ladder(
        values_by_rank=values_by_rank,
        cutline=total_rosters * roster_slots,
    )


def _sum_market(items: list[PersonalValuePoolItem]) -> float:
    return sum(
        _market_value(item) or 0.0
        for item in items
    )


def _sum_or_none(items, getter) -> float | None:
    values = [getter(item) for item in items]

    if any(v is None for v in values):
        return None

    return sum(values)


async def _build_roster_context(
    ctx: ContextDep,
    *,
    league,
    my_roster,
    pool_context,
    my_items: list[PersonalValuePoolItem],
    strategy: LeagueStrategy | None = None,
    manager_note: str | None = None,
) -> AdvisorRosterContext:
    player_ids = list(my_roster.players or [])
    player_map = await get_player_map_for_ids(
        ctx.db,
        player_ids,
    )

    position_counts: dict[str, int] = defaultdict(int)
    ages: list[float] = []
    for pid in player_ids:
        meta = player_map.get(pid)

        if meta:
            position_counts[meta.get("position", "?")] += 1

            if meta.get("age") is not None:
                ages.append(float(meta["age"]))

    return AdvisorRosterContext(
        league_id=league.league_id,
        league_name=pool_context.league_name,
        season=pool_context.season,
        total_rosters=pool_context.total_rosters,
        wins=my_roster.wins,
        losses=my_roster.losses,
        ties=my_roster.ties,
        points_for=(
            float(my_roster.fpts)
            if my_roster.fpts is not None
            else None
        ),
        position_counts=dict(position_counts),
        avg_age=(
            sum(ages) / len(ages) if ages else None
        ),
        strategy=strategy.strategy if strategy else None,
        strategy_reason=(
            strategy.reason if strategy else None
        ),
        strategy_source=(
            strategy.source if strategy else None
        ),
        manager_note=manager_note,
    )


async def _summarize_signals(
    ctx: ContextDep,
    username: str,
) -> AdvisorSignalSummary:
    try:
        trades = await get_trade_signals(
            ctx.db,
            ctx.sleeper,
            username,
            site_user_id=ctx.site_user.id if ctx.site_user else None,
            redis=ctx.redis,
        )
    except Exception:
        logger.exception("Trade signals fetch failed for advisor")
        return AdvisorSignalSummary()

    buys: list[str] = []
    sells: list[str] = []

    for tx in trades:
        for user in tx.users:
            for movement in user.adds:
                if movement.signal.startswith("Buy opportunity"):
                    buys.append(movement.name)

            for movement in user.drops:
                if movement.signal.startswith("Sell opportunity"):
                    sells.append(movement.name)

    def dedupe(values: list[str]) -> list[str]:
        seen = dict.fromkeys(values)
        return list(seen)[:SIGNAL_SUMMARY_LIMIT]

    return AdvisorSignalSummary(
        buy_targets=dedupe(buys),
        sell_candidates=dedupe(sells),
    )
