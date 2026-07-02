import logging

from .replacement import (
    ReplacementCalculator,
    ReplacementRosterBuilder,
    BenchReplacementCalculator,
)

logger = logging.getLogger(__name__)


class ReplacementService:

    def __init__(self):

        self.starter = ReplacementCalculator()

        self.roster_builder = (
            ReplacementRosterBuilder()
        )

        self.bench = (
            BenchReplacementCalculator()
        )


    def calculate(
        self,
        players,
        roster_positions,
        total_rosters,
    ):

        starter_replacement = (
            self.starter.calculate(
                players=players,
                roster_positions=roster_positions,
                total_rosters=total_rosters,
            )
        )


        replacement_roster = (
            self.roster_builder.build(
                players=players,
                roster_positions=roster_positions,
                total_rosters=total_rosters,
            )
        )


        logger.info(
            f"Replacement roster size: {len(replacement_roster)}"
        )


        roster_replacement = (
            self.bench.calculate(
                players=players,
                replacement_roster=replacement_roster,
            )
        )


        return (
            starter_replacement,
            roster_replacement,
        )