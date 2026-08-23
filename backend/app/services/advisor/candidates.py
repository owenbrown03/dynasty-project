import logging
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
from app.services.advisor.trade_block import (
    get_trade_block_snapshot,
)
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)

logger = logging.getLogger(__name__)

MAX_LEAGUES = 6
ANCHOR_POOL_SIZE = 5
MAX_PROPOSALS_PER_LEAGUE = 4
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
    """One original draft pick with its current owner and value."""

    season: str
    round: int
    og_roster_id: int
    owner_roster_id: int
    value: float | None = None
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


def _to_ref(item: PersonalValuePoolItem) -> AdvisorPlayerRef:
    return AdvisorPlayerRef(
        player_id=item.player.player_id,
        name=item.player.name,
        position=item.player.position,
        team=item.player.team,
        age=item.player.age,
        market_value=_market_value(item),
        personal_war=_personal_war(item),
        market_war=_market_war(item),
        delta_war=_delta_war(item),
    )


async def build_advisor_dossier(
    ctx: ContextDep,
    username: str,
    league_id: str | None = None,
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
                proposals=proposals,
                roster_contexts=roster_contexts,
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
    proposals: list[AdvisorProposal],
    roster_contexts: list[AdvisorRosterContext],
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

    roster_contexts.append(
        await _build_roster_context(
            ctx,
            league=league,
            my_roster=my_roster,
            pool_context=pool.context,
            my_items=my_items,
        ),
    )

    sell_pool = sorted(
        (item for item in my_items if _market_value(item)),
        key=lambda i: _delta_war(i) or 0.0,
    )[:ANCHOR_POOL_SIZE]

    buy_pool = sorted(
        (
            item
            for pid, item in items_by_player_id.items()
            if pid not in my_player_ids and _market_value(item)
        ),
        key=lambda i: _delta_war(i) or 0.0,
        reverse=True,
    )[:ANCHOR_POOL_SIZE]

    if not sell_pool or not buy_pool:
        return

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

    # Trade-block signal first: a leaguemate explicitly shopping an
    # asset is the strongest availability marker we have.
    buy_pool = sorted(
        buy_pool,
        key=lambda i: (
            i.player.player_id not in snapshot.player_ids,
            -(_delta_war(i) or 0.0),
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
    used_pick_keys: set[tuple[int, str, int]] = set()

    made_for_this_league = 0
    used_sell_ids: set[str] = set()

    for target in buy_pool:
        if made_for_this_league >= MAX_PROPOSALS_PER_LEAGUE:
            break

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
            and p.key not in used_pick_keys
        ]

        package_players, package_picks = _match_package(
            sell_pool,
            my_picks,
            target_market=_market_value(target),
            used_player_ids=used_sell_ids,
            used_pick_keys=used_pick_keys,
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

        extra_receive_pick = _fix_with_extra_receive_pick(
            their_picks=their_picks,
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

        if not _passes_value_constraints(
            market_send_total=market_send_total,
            market_receive_total=market_receive_total,
            personal_send_total=personal_send_total,
            personal_receive_total=personal_receive_total,
        ):
            used_sell_ids.update(
                item.player.player_id for item in package_players
            )
            used_pick_keys.update(
                p.key for p in package_picks
            )
            continue

        used_sell_ids.update(
            item.player.player_id for item in package_players
        )
        used_pick_keys.update(p.key for p in package_picks)

        if extra_receive_pick is not None:
            used_pick_keys.add(extra_receive_pick.key)

        counterparty_name = owner_names.get(owner_id, {}).get(
            "name",
            "Unknown",
        )

        target_on_block = (
            target.player.player_id in snapshot.player_ids
        )

        receive_refs = [_to_ref(target)]
        if target_on_block:
            receive_refs[0].on_block = True

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

    return dict(chests)


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
    """Personal totals treat picks as worth their market value."""
    player_total = _sum_or_none(players, _personal_war)

    if player_total is None:
        return None

    return player_total + sum(
        p.value or 0.0 for p in picks
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
        key=lambda p: p.value or 0.0,
    ):
        value = pick.value or 0.0

        if value < deficit:
            continue

        new_receive = market_receive_total + value

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
) -> bool:
    """Enforces the two-sided acceptance rules from the advisor spec.

    1. Counterparty-convincing: they receive at least even market value.
    2. We win or tie on OUR value system (never lose personally).
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

    return (
        personal_receive_total
        >= personal_send_total - PERSONAL_EDGE_TOLERANCE
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
) -> AdvisorRosterContext:
    player_ids = list(my_roster.players or [])
    player_map = await get_player_map_for_ids(
        ctx.db,
        player_ids,
    )

    position_counts: dict[str, int] = defaultdict(int)
    for pid in player_ids:
        meta = player_map.get(pid)

        if meta:
            position_counts[meta.get("position", "?")] += 1

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
        avg_age=None,
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
