from .merger import ProjectionMerger
from .models import DynastyPlayerInput, DynastyProjection
from .projector import WARProjector


class DynastyWARService:

    def __init__(
        self,
        projector: WARProjector,
        merger: ProjectionMerger,
    ):
        self.projector = projector
        self.merger = merger

    def project_player(
        self,
        player: DynastyPlayerInput,
    ) -> DynastyProjection:

        starter_projection = self.projector.project(
            war=player.starter_war,
            age=player.age,
            position=player.position,
        )

        roster_projection = self.projector.project(
            war=player.roster_war,
            age=player.age,
            position=player.position,
        )

        return self.merger.merge(
            player=player,
            starter=starter_projection,
            roster=roster_projection,
        )