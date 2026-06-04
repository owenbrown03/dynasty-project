from fastapi import APIRouter, Depends

from app.integrations.sleeper import types
from app.integrations.sleeper.client import SleeperClient
from app.api.deps import get_user_sleeper_client

router = APIRouter()

@router.post("/trades/propose")
async def propose_trade(
    body: types.TradeRequest,
    sleeper: SleeperClient = Depends(get_user_sleeper_client),
):
    return await sleeper.write.propose_trade(
        league_id=body.league_id,
        variables=body.model_dump(exclude={"league_id"})
    )

@router.post("/waivers/claim")
async def submit_waiver_claim(
    body: types.WaiverRequest,
    sleeper: SleeperClient = Depends(get_user_sleeper_client),
):
    return await sleeper.write.submit_waiver_claim(
        league_id=body.league_id,
        variables=body.model_dump(exclude={"league_id"})
    )