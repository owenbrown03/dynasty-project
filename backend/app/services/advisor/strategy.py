import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

REBUILD = "rebuild"
WIN_NOW = "win_now"
HOARD_PICKS = "hoard_picks"
COMPETE = "compete"

BASIS_ACTUAL_POINTS = "actual_points"
BASIS_PROJECTED_WAR = "projected_war"


@dataclass
class LeagueStrategy:
    strategy: str
    reason: str
    source: str = "detected"
    # Middle band by strength rank (not top-third contending, not
    # bottom-third): these managers often believe their window is
    # opening and pay up for proven production.
    fringe: bool = False


# Explicit direction declarations a manager can write in their league
# note. When one matches, it is treated as ground truth and overrides
# the numeric strategy detection instead of merely informing the prompt.
_NOTE_DIRECTION_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        WIN_NOW,
        [
            "win now",
            "win-now",
            "all-in",
            "all in",
            "going for it",
            "championship or bust",
            "contending window",
        ],
    ),
    (
        REBUILD,
        [
            "rebuild",
            "rebuilding",
            "retool",
            "tanking",
            "tank for",
            "sell everything",
            "tear it down",
            "reset roster",
        ],
    ),
    (
        HOARD_PICKS,
        [
            "hoard picks",
            "stockpile picks",
            "stockpiling picks",
            "collect picks",
            "accumulate picks",
            "draft capital",
        ],
    ),
]


def strategy_from_manager_note(
    note: str | None,
) -> LeagueStrategy | None:
    """Pins strategy to an explicit direction declared in the note.

    Scans all keyword groups and returns the match that appears
    earliest in the text so mixed notes honor the manager's first
    stated intent.
    """
    if not note:
        return None

    text = note.lower()

    best: tuple[int, str] | None = None
    for strategy, keywords in _NOTE_DIRECTION_KEYWORDS:
        for keyword in keywords:
            index = text.find(keyword)
            if index == -1:
                continue
            if best is None or index < best[0]:
                best = (index, strategy)

    if best is None:
        return None

    return LeagueStrategy(
        strategy=best[1],
        reason=(
            "Pinned from your league note, overriding numeric "
            "signals."
        ),
        source="manager_note",
    )


def detect_strategy(
    *,
    my_strength: float | None,
    all_strengths: list[float | None],
    basis: str,
    my_wins: int,
    my_losses: int,
    my_ties: int = 0,
    my_starter_age: float | None,
    league_starter_age: float | None,
    my_pick_count: int,
    league_avg_pick_count: float,
) -> LeagueStrategy:
    """Classifies the roster direction for one league.

    Team strength is season-phase aware: actual points once real
    games have been played, projected starter WAR before that.
    `basis` names which one fed the ranking so reasons never claim
    a standing the data cannot support (e.g. "rank 1" off zero
    points in the preseason).

    Signals, in order of decision weight:
      - standing: strength rank vs the rest of the league
      - age curve: my starter-weighted average age vs the league's
      - draft capital: picks held vs the league average

    The three classic dynasty postures fall out directly:
      - outside contention with picks in hand -> rebuild
      - contending with an old core -> win now
      - mid-table but rich in picks -> keep hoarding
      - everything else -> compete as constructed
    """
    games = my_wins + my_losses + my_ties

    ranked = sorted(
        (s for s in all_strengths if s is not None),
        reverse=True,
    )
    n_teams = max(len(ranked), 1)

    if my_strength is None or not ranked:
        pf_rank = n_teams // 2
    else:
        pf_rank = 1 + sum(
            1 for s in ranked if s > my_strength
        )

    contending = pf_rank <= max(1, round(n_teams / 3))
    bottom_feeding = (
        pf_rank > n_teams - max(1, round(n_teams / 3))
    )

    # Before enough games are played a win-loss record says nothing
    # about team quality; only trust it once it can mean something.
    record_is_meaningful = games >= 3

    older_than_league = (
        my_starter_age is not None
        and league_starter_age is not None
        and my_starter_age - league_starter_age >= 0.5
    )
    pick_rich = (
        my_pick_count
        >= max(2.0, league_avg_pick_count * 1.25)
    )

    strength_label = (
        "points scored"
        if basis == BASIS_ACTUAL_POINTS
        else "projected starter WAR"
    )

    middle_band = not contending and not bottom_feeding

    if bottom_feeding and (
        basis == BASIS_PROJECTED_WAR or record_is_meaningful
    ):
        if pick_rich:
            return LeagueStrategy(
                REBUILD,
                fringe=False,
                reason=(
                    f"Rank {pf_rank} of {n_teams} in "
                    f"{strength_label} while holding "
                    f"{my_pick_count} picks — sell veterans for "
                    f"youth and keep stacking draft capital."
                ),
            )

        return LeagueStrategy(
            REBUILD,
            fringe=False,
            reason=(
                f"Rank {pf_rank} of {n_teams} in "
                f"{strength_label}"
                + (
                    f" ({my_wins}-{my_losses})"
                    if record_is_meaningful
                    else ""
                )
                + " — the competitive window is closed, so "
                "prioritize future value."
            ),
        )

    if contending and older_than_league:
        window = (
            f"{my_wins}-{my_losses}, "
            if record_is_meaningful
            else ""
        )
        return LeagueStrategy(
            WIN_NOW,
            fringe=False,
            reason=(
                f"Top third in {strength_label} "
                f"(rank {pf_rank} of {n_teams}; {window}"
                f"older core avg {my_starter_age:.1f} vs league "
                f"{league_starter_age:.1f}) — push chips in for "
                f"proven production."
            ),
        )

    if not contending and pick_rich:
        return LeagueStrategy(
            HOARD_PICKS,
            fringe=True,
            reason=(
                f"Mid-table in {strength_label} "
                f"(rank {pf_rank} of {n_teams}) while holding "
                f"{my_pick_count} picks vs a league average of "
                f"{league_avg_pick_count:.1f} — keep accumulating "
                f"draft capital."
            ),
        )

    parts = [
        f"{strength_label.capitalize()} rank "
        f"{pf_rank} of {n_teams}",
    ]

    if older_than_league:
        parts.append(f"aging core (avg {my_starter_age:.1f})")
    elif my_starter_age is not None:
        parts.append(f"avg age {my_starter_age:.1f}")

    return LeagueStrategy(
        COMPETE,
        fringe=middle_band,
        reason=", ".join(parts)
        + " — competitive as constructed; improve the roster "
        "without mortgaging either the present or the future.",
    )


# Explicit Sleeper injury-status mapping. Season-altering designations
# remove a player from the lineup for the rest of the year (or
# indefinitely); weekly designations (Q/D/DNR) are day-to-day noise
# and deliberately NOT treated as season-altering.
SEASON_ALTERING_INJURY_STATUSES = {
    "ir",
    "injured reserve",
    "ir-r",
    "o",
    "out",
    "pup",
    "nfi",
}

WEEKLY_INJURY_STATUSES = {
    "q",
    "questionable",
    "d",
    "doubtful",
    "dnr",
}


def is_season_altering_injury(status: str | None) -> bool:
    if not status:
        return False

    return (
        status.strip().casefold()
        in SEASON_ALTERING_INJURY_STATUSES
    )
