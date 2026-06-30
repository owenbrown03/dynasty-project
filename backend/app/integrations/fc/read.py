from .transport import FantasyCalcTransport
from .schemas import FantasyCalcValue


class FantasyCalcRead:

    def __init__(
        self,
        transport: FantasyCalcTransport,
    ):
        self.transport = transport


    async def get_current_values(
        self,
        *,
        is_dynasty: bool = True,
        num_qbs: int = 2,
        num_teams: int = 12,
        ppr: int = 1,
    ) -> list[FantasyCalcValue]:

        data = await self.transport.get(
            "/values/current",
            params={
                "isDynasty": str(is_dynasty).lower(),
                "numQbs": num_qbs,
                "numTeams": num_teams,
                "ppr": ppr,
            },
        )

        return [
            FantasyCalcValue.model_validate(player)
            for player in data
        ]