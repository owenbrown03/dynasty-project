from app.analytics.war.service import WARService
from app.analytics.war.models import PlayerProjectionValue


def test_war():

    players = [

        PlayerProjectionValue(
            player_id="1",
            name="Elite RB",
            position="RB",
            team="ATL",
            projected_points=300,
            projected_ppg=17.6,
        ),

        PlayerProjectionValue(
            player_id="2",
            name="Replacement RB",
            position="RB",
            team=None,
            projected_points=150,
            projected_ppg=8.8,
        ),

    ]


    war = WARService().calculate(players)

    assert war[0].war > 0