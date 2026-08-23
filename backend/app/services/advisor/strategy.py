import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

REBUILD = "rebuild"
WIN_NOW = "win_now"
HOARD_PICKS = "hoard_picks"
COMPETE = "compete"


@dataclass
class LeagueStrategy:
    strategy: str
    reason: str


def detect_strategy(
    *,
    my_points_for: float | None,
    all_points_for: list[float],
    my_wins: int,
    my_losses: int,
    my_ties: int = 0,
    my_starter_age: float | None,
    league_starter_age: float | None,
    my_pick_count: int,
    league_avg_pick_count: float,
) -> LeagueStrategy:
    """Classifies the roster direction for one league.

    Signals, in order of decision weight:
      - standing: points-for rank vs the rest of the league
      - age curve: my starter-weighted average age vs the league's
      - draft capital: picks held vs the league average

    The three classic dynasty postures fall out directly:
      - outside contention with picks in hand -> rebuild
      - contending with an old core -> win now
      - mid-table but rich in picks -> keep hoarding
      - everything else -> compete as constructed
    """
    games = my_wins + my_losses + my_ties
    win_pct = my_wins / games if games else 0.5

    ranked = sorted(
        (p for p in all_points_for if p is not None),
        reverse=True,
    )
    n_teams = max(len(ranked), 1)

    if my_points_for is None or not ranked:
        pf_rank = n_teams // 2
    else:
        pf_rank = 1 + sum(
            1 for p in ranked if p > my_points_for
        )

    contending = pf_rank <= max(1, round(n_teams / 3))
    bottom_feeding = (
        pf_rank > n_teams - max(1, round(n_teams / 3))
    )

    older_than_league = (
        my_starter_age is not None
        and league_starter_age is not None
        and my_starter_age - league_starter_age >= 0.5
    )
    younger_than_league = (
        my_starter_age is not None
        and league_starter_age is not None
        and league_starter_age - my_starter_age >= 0.5
    )
    pick_rich = (
        my_pick_count
        >= max(2.0, league_avg_pick_count * 1.25)
    )

    if bottom_feeding or (not contending and win_pct < 0.45):
        if pick_rich:
            return LeagueStrategy(
                REBUILD,
                (
                    f"Outside the top third in scoring "
                    f"(rank {pf_rank} of {n_teams}) while holding "
                    f"{my_pick_count} picks — sell veterans for "
                    f"youth and keep stacking capital."
                ),
            )

        return LeagueStrategy(
            REBUILD,
            (
                f"Outside the top third in scoring "
                f"(rank {pf_rank} of {n_teams}, "
                f"{my_wins}-{my_losses}) — the competitive window "
                f"is closed, so prioritize future value."
            ),
        )

    if contending and older_than_league:
        return LeagueStrategy(
            WIN_NOW,
            (
                f"Top-third offense (rank {pf_rank} of {n_teams}) "
                f"with an older core "
                f"(avg {my_starter_age:.1f} vs league "
                f"{league_starter_age:.1f}) — the window is open "
                f"now; trade youth and picks for proven production."
            ),
        )

    if pick_rich:
        return LeagueStrategy(
            HOARD_PICKS,
            (
                f"Holding {my_pick_count} picks against a league "
                f"average of {league_avg_pick_count:.1f} — keep "
                f"accumulating draft capital rather than spending it."
            ),
        )

    parts = [
        f"Scoring rank {pf_rank} of {n_teams}",
    ]

    if younger_than_league:
        parts.append(
            f"young core (avg {my_starter_age:.1f})"
        )
    elif my_starter_age is not None:
        parts.append(f"avg age {my_starter_age:.1f}")

    return LeagueStrategy(
        COMPETE,
        (
            ", ".join(parts)
            + " — competitive as constructed; improve the roster "
            "without mortgaging either the present or the future."
        ),
    )
