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

    if bottom_feeding and (
        basis == BASIS_PROJECTED_WAR or record_is_meaningful
    ):
        if pick_rich:
            return LeagueStrategy(
                REBUILD,
                (
                    f"Rank {pf_rank} of {n_teams} in "
                    f"{strength_label} while holding "
                    f"{my_pick_count} picks — sell veterans for "
                    f"youth and keep stacking draft capital."
                ),
            )

        return LeagueStrategy(
            REBUILD,
            (
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
            (
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
            (
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
        ", ".join(parts)
        + " — competitive as constructed; improve the roster "
        "without mortgaging either the present or the future.",
    )
