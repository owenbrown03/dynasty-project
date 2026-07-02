from dataclasses import dataclass


POSITIONS = ("QB", "RB", "WR", "TE")


@dataclass
class RosterConstructionOptimizer:
    total_roster_spots: int
    starting_requirements: dict[str, int]

    def calculate(
        self,
        players,
    ) -> dict[str, int]:

        players_by_position = {
            position: sorted(
                (
                    p
                    for p in players
                    if p.position == position
                ),
                key=lambda p: p.projected_points,
                reverse=True,
            )
            for position in POSITIONS
        }

        roster_counts = {
            position: self.starting_requirements.get(position, 0)
            for position in POSITIONS
        }

        indices = roster_counts.copy()

        selected = sum(roster_counts.values())

        while selected < self.total_roster_spots:

            best_position = None
            best_gain = float("-inf")

            for position in POSITIONS:

                idx = indices[position]

                if idx >= len(players_by_position[position]):
                    continue

                gain = self._marginal_gain(
                    players_by_position[position],
                    idx,
                )

                if gain > best_gain:
                    best_gain = gain
                    best_position = position

            if best_position is None:
                break

            roster_counts[best_position] += 1
            indices[best_position] += 1
            selected += 1

        return roster_counts

    def _marginal_gain(
        self,
        players,
        index,
    ) -> float:

        return players[index].projected_points