"""FantasyCalc-style waiver adjustment for uneven trades.

When one side of a trade ships more PLAYERS than it receives, it
opens bench spots that will be refilled from waivers. Following
FantasyCalc's documented model: the first replacement is roughly
the worst rostered player in the league (the waiver cutline), and
each additional spot lost assumes a slightly better replacement.
"""

# How far up the ranking each additional lost bench slot moves the
# assumed replacement player. FantasyCalc reports ~300th for the
# first slot and ~290th for two slots in an average league.
_SLOT_STEP = 10

# FantasyCalc's documented anchor: the implicit waiver replacement
# for the first lost bench spot is the ~300th best player, stepping
# up the ranking per additional spot lost. Empirically confirmed:
# ranks 300 + 290 = 248 + 277 = 525, matching FC's displayed +525
# for a picks-for-player trade in a 12-team SF league.
_REFERENCE_RANK = 300

_MAX_EXTRA_SPOTS = 4


def build_waiver_credit_ladder(
    *,
    values_by_rank: dict[int, float],
) -> list[float]:
    """Builds cumulative credit for 1..N extra bench spots lost.

    values_by_rank maps FantasyCalc's own overall_rank to value.
    Keying by published rank (instead of positional sort order) keeps
    the cutline honest even when some players fail name-match during
    sync. The cutline anchors at FC's documented ~300th-best player.
    """
    cutline = _REFERENCE_RANK

    ladder: list[float] = []
    running = 0.0

    for slot in range(_MAX_EXTRA_SPOTS):
        target_rank = cutline - slot * _SLOT_STEP

        # Nearest synced rank at or below the target tolerates
        # small gaps in the ranking map.
        value = next(
            (
                values_by_rank[r]
                for r in range(target_rank, 0, -1)
                if r in values_by_rank
            ),
            None,
        )

        if value is None:
            break

        running += value
        ladder.append(running)

    return ladder


async def load_waiver_ladder(
    db,
    *,
    total_rosters: int,
    num_qbs: int = 2,
    ppr: int = 1,
) -> list[float]:
    """Loads the FC ranking at league shape and builds the ladder."""
    from sqlalchemy import select

    from app.models.db.fc.models import FantasyCalcValue

    depth = _REFERENCE_RANK + 100
    result = await db.execute(
        select(
            FantasyCalcValue.overall_rank,
            FantasyCalcValue.value,
        ).where(
            FantasyCalcValue.is_dynasty == True,  # noqa: E712
            FantasyCalcValue.num_qbs == num_qbs,
            FantasyCalcValue.num_teams == total_rosters,
            FantasyCalcValue.ppr == ppr,
            FantasyCalcValue.overall_rank.isnot(None),
        )
        .order_by(FantasyCalcValue.overall_rank)
        .limit(depth)
    )
    values_by_rank = {
        int(rank): float(value)
        for rank, value in result.all()
    }

    return build_waiver_credit_ladder(
        values_by_rank=values_by_rank,
    )


def waiver_credit_for(
    *,
    players_sent: int,
    players_received: int,
    ladder: list[float],
) -> float | None:
    """Credit owed to the side that ships more players.

    Returns None for even or receiving-side trades - no bench
    spot opens, so no adjustment applies.
    """
    extra = players_sent - players_received

    if extra <= 0 or not ladder:
        return None

    index = min(extra, len(ladder)) - 1
    credit = ladder[index]

    return credit if credit > 0 else None


def split_waiver_credits(
    *,
    my_players_out: int,
    their_players_out: int,
    ladder: list[float],
) -> tuple[float | None, float | None]:
    """Returns (my_credit, their_credit) for a trade."""
    mine = waiver_credit_for(
        players_sent=my_players_out,
        players_received=their_players_out,
        ladder=ladder,
    )
    theirs = waiver_credit_for(
        players_sent=their_players_out,
        players_received=my_players_out,
        ladder=ladder,
    )
    return mine, theirs


async def get_waiver_adjustment(
    db,
    *,
    total_rosters: int,
    num_qbs: int,
    ppr: int,
    my_players_out: int,
    their_players_out: int,
) -> tuple[float | None, float | None]:
    """Ladder-backed waiver credits for the manual calculator.

    Uses FantasyCalc's own overall_rank at league shape so the
    cutline player matches the ranking managers see.
    """
    ladder = await load_waiver_ladder(
        db,
        total_rosters=total_rosters,
        num_qbs=num_qbs,
        ppr=ppr,
    )

    return split_waiver_credits(
        my_players_out=my_players_out,
        their_players_out=their_players_out,
        ladder=ladder,
    )
