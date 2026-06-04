from .mutations import MUTATIONS
from .exceptions import SleeperUnknownOperationError, SleeperValidationError

class SleeperWrite:
    def __init__(self, transport):
        self.transport = transport

    async def execute(self, operation: str, league_id: str, variables: dict):
        if operation not in MUTATIONS:
            raise SleeperUnknownOperationError(operation)

        if not league_id:
            raise SleeperValidationError("league_id is required")

        payload = {
            **variables,
            "league_id": league_id,
        }

        return await self.transport.post(
            query=MUTATIONS[operation],
            variables=payload,
            extra_headers={
                "X-Sleeper-GraphQL-Op": operation,
            },
        )

    async def propose_trade(self, league_id: str, variables: dict):
        return await self.execute("propose_trade", league_id, variables)

    async def submit_waiver_claim(self, league_id: str, variables: dict):
        return await self.execute("submit_waiver_claim", league_id, variables)