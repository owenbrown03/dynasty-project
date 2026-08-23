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

# Safety margin above the rostered cutline so the assumed waiver
# pickup sits just past the worst rostered player, not on it.
_CUTLINE_PAD = 2


def build_waiver_credit_ladder(
    ranked_fc_values: list[float],
    *,
    num_teams: int,
    roster_slots: int,
) -> list[float]:
    """Builds cumulative credit for 1..N extra bench spots lost.

    ranked_fc_values must be every poolable player's FC value,
    best first. Index cutline-ish approximates the worst rostered
    player; entries past it are true free agents.
    """
    cutline = min(
        num_teams * roster_slots + _CUTLINE_PAD,
        max(len(ranked_fc_values) - 1, 0),
    )

    ladder: list[float] = []
    running = 0.0

    for slot in range(_MAX_EXTRA_SPOTS):
        index = cutline - slot * _SLOT_STEP

        if index < 0:
            break

        running += (
            ranked_fc_values[index]
            if index < len(ranked_fc_values)
            else 0.0
        )
        ladder.append(running)

    return ladder


_MAX_EXTRA_SPOTS = 4


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
    roster_slots: int,
    my_players_out: int,
    their_players_out: int,
) -> tuple[float | None, float | None]:
    """Ladder-backed waiver credits for the manual calculator.

    Uses FantasyCalc's own overall_rank at league shape so the
    cutline player matches the ranking managers see.
    """
    from collections.abc import Sequence

    from sqlalchemy import desc
    from sqlmodel import select

    from app.models.db.fc.models import FantasyCalcValue

    depth = total_rosters * roster_slots + 100
    result = await db.execute(
        select(FantasyCalcValue.value)
        .where(
            FantasyCalcValue.is_dynasty == True,  # noqa: E712
            FantasyCalcValue.num_qbs == num_qbs,
            FantasyCalcValue.num_teams == total_rosters,
            FantasyCalcValue.ppr == ppr,
        )
        .order_by(
            FantasyCalcValue.value.desc(),
        )
        .limit(depth)
    )
    ranked: Sequence[float] = [
        float(v) for v in result.scalars().all()
    ]

    ladder = build_waiver_credit_ladder(
        list(ranked),
        num_teams=total_rosters,
        roster_slots=roster_slots,
    )

    return split_waiver_credits(
        my_players_out=my_players_out,
        their_players_out=their_players_out,
        ladder=ladder,
    )
