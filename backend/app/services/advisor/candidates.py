import logging
from collections import defaultdict

from app.api.deps import ContextDep
from app.crud.sleeper.league import get_league_with_rosters
from app.crud.sleeper.player import get_player_map_for_ids
from app.crud.sleeper.trade import (
    get_trade_signals,
    get_user_meta_map,
)
from app.crud.sleeper.user import get_userid_by_username
from app.schemas.advisor import (
    AdvisorDossier,
    AdvisorPlayerRef,
    AdvisorProposal,
    AdvisorRosterContext,
    AdvisorSignalSummary,
)
from app.schemas.personal_values import PersonalValuePoolItem
from app.services.personal_values import get_personal_value_pool
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)

logger = logging.getLogger(__name__)

MAX_LEAGUES = 6
ANCHOR_POOL_SIZE = 5
MAX_PROPOSALS_PER_LEAGUE = 2
KTC_MATCH_MIN_RATIO = 0.65
KTC_MATCH_MAX_RATIO = 1.55
SIGNAL_SUMMARY_LIMIT = 15


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
        ktc_value=item.player.ktc_value,
        personal_war=_personal_war(item),
        market_war=_market_war(item),
        delta_war=_delta_war(item),
    )


async def build_advisor_dossier(
    ctx: ContextDep,
    username: str,
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
        (item for item in my_items if item.player.ktc_value),
        key=lambda i: _delta_war(i) or 0.0,
    )[:ANCHOR_POOL_SIZE]

    buy_pool = sorted(
        (
            item
            for pid, item in items_by_player_id.items()
            if pid not in my_player_ids and item.player.ktc_value
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

    made_for_this_league = 0
    used_sell_ids: set[str] = set()

    for target in buy_pool:
        if made_for_this_league >= MAX_PROPOSALS_PER_LEAGUE:
            break

        owner_id = _find_owner_of_player(
            league_rosters,
            target.player.player_id,
            exclude_owner=my_roster.owner_id,
        )

        if owner_id is None:
            continue

        package = _match_package(
            sell_pool,
            target_ktc=target.player.ktc_value,
            used_player_ids=used_sell_ids,
        )

        if package is None:
            continue

        used_sell_ids.update(
            item.player.player_id for item in package
        )

        counterparty_name = owner_names.get(owner_id, {}).get(
            "name",
            "Unknown",
        )

        proposals.append(
            AdvisorProposal(
                league_id=league.league_id,
                league_name=pool.context.league_name,
                counterparty_id=owner_id,
                counterparty_name=counterparty_name,
                send=[_to_ref(i) for i in package],
                receive=[_to_ref(target)],
                market_send_total=_sum_ktc(package),
                market_receive_total=float(target.player.ktc_value),
                personal_send_total=_sum_or_none(
                    package,
                    _personal_war,
                ),
                personal_receive_total=_personal_war(target),
            ),
        )
        made_for_this_league += 1


def _find_owner_of_player(
    league_rosters,
    player_id: str,
    *,
    exclude_owner: str | None,
) -> str | None:
    for _, roster in league_rosters:
        if roster.owner_id == exclude_owner:
            continue

        if player_id in (roster.players or []):
            return roster.owner_id

    return None


def _match_package(
    sell_pool: list[PersonalValuePoolItem],
    *,
    target_ktc: float,
    used_player_ids: set[str] | None = None,
):
    used_player_ids = used_player_ids or set()
    candidates = [
        item
        for item in sell_pool
        if item.player.player_id not in used_player_ids
    ]
    if not candidates:
        return None

    best_single = None
    best_gap = None

    for item in candidates:
        gap = abs(float(item.player.ktc_value) - target_ktc)
        ratio = float(item.player.ktc_value) / target_ktc

        if not (
            KTC_MATCH_MIN_RATIO <= ratio <= KTC_MATCH_MAX_RATIO
        ):
            continue

        if best_gap is None or gap < best_gap:
            best_gap = gap
            best_single = [item]

    if best_single is not None:
        return best_single

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            pair_total = float(
                candidates[i].player.ktc_value
            ) + float(candidates[j].player.ktc_value)

            ratio = pair_total / target_ktc

            if (
                KTC_MATCH_MIN_RATIO
                <= ratio
                <= KTC_MATCH_MAX_RATIO
            ):
                return [candidates[i], candidates[j]]

    return None


def _sum_ktc(items: list[PersonalValuePoolItem]) -> float:
    return sum(
        float(item.player.ktc_value or 0)
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
