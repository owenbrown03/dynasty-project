# from fastapi import APIRouter, Depends

# from app.integrations.sleeper import types
# from app.core.context import Context
# from app.api.deps import get_context

# router = APIRouter()

# @router.post("/trades/propose")
# async def propose_trade(
#     body: types.TradeRequest,
#     ctx: Context = Depends(get_context),
# ):
#     return await ctx.sleeper.write.propose_trade(
#         league_id=body.league_id,
#         **body.to_variables()
#     )

# @router.post("/waivers/claim")
# async def submit_waiver_claim(
#     body: types.WaiverRequest,
#     ctx: Context = Depends(get_context),
# ):
#     return await ctx.sleeper.write.submit_waiver_claim(
#         league_id=body.league_id,
#         **body.to_variables()
#     )