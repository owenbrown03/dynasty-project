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
from app.services.advisor.strategy import (
    BASIS_ACTUAL_POINTS,
    BASIS_PROJECTED_WAR,
    HOARD_PICKS,
    REBUILD,
    WIN_NOW,
    LeagueStrategy,
    detect_strategy,
)
from app.services.advisor.trade_block import (
    get_trade_block_snapshot,
)
from app.services.trades.waiver import (
    build_waiver_credit_ladder,
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
ADVISOR_ENGINE_VERSION = 4
ANCHOR_POOL_SIZE = 8
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

    strategy = await _detect_league_strategy(
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
    sell_pool = sell_pool[:ANCHOR_POOL_SIZE]
    buy_pool = buy_pool[:ANCHOR_POOL_SIZE]

    if not sell_pool or not buy_pool:
        return

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
    waiver_ladder = build_waiver_credit_ladder(
        sorted(
            (
                float(i.player.fc_value)
                for i in items_by_player_id.values()
                if i.player.fc_value is not None
            ),
            reverse=True,
        ),
        num_teams=pool.context.total_rosters,
        roster_slots=max(
            len(league.roster_positions or []) or 10, 1
        ),
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

        my_credit, their_credit = split_waiver_credits(
            my_players_out=len(package_players),
            their_players_out=1,
            ladder=waiver_ladder,
        )

        if not _passes_value_constraints(
            market_send_total=market_send_total
            + (my_credit or 0.0),
            market_receive_total=market_receive_total
            + (their_credit or 0.0),
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
                my_waiver_credit=my_credit,
                their_waiver_credit=their_credit,
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
) -> LeagueStrategy:
    basis, _phase = await _season_phase(ctx.sleeper)

    starters = max(
        len(league.roster_positions or []) or 10,
        1,
    )

    if basis == BASIS_PROJECTED_WAR:
        # Preseason/offseason: rank every roster by its best
        # starters-sized slice of current-year projected WAR.
        def strength(roster) -> float:
            return _projected_roster_strength(
                set(roster.players or []),
                items_by_player_id,
                starters,
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

    return detect_strategy(
        my_strength=my_strength,
        all_strengths=all_strengths,
        basis=basis,
        my_wins=my_roster.wins or 0,
        my_losses=my_roster.losses or 0,
        my_ties=my_roster.ties or 0,
        my_starter_age=_starter_ages(my_items),
        league_starter_age=league_starter_age,
        my_pick_count=len(
            chests.get(my_roster.roster_id, [])
        ),
        league_avg_pick_count=(
            sum(len(v) for v in chests.values())
            / max(len(chests), 1)
        ),
    )


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
