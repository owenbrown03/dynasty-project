from app.analytics.war.dynasty.aging import AgingCurve
from app.analytics.war.dynasty.discount import DiscountCurve
from app.analytics.war.dynasty.expected_games import (
    ExpectedGamesRemainingService,
)
from app.analytics.war.dynasty.merger import ProjectionMerger
from app.analytics.war.dynasty.projector import WARProjector
from app.analytics.war.dynasty.service import DynastyWARService


def build_dynasty_war_service() -> DynastyWARService:
    return DynastyWARService(
        projector=WARProjector(
            expected_games_service=ExpectedGamesRemainingService(),
            aging_curve=AgingCurve(),
            discount_curve=DiscountCurve(),
        ),
        merger=ProjectionMerger(),
    )