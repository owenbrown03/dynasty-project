from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, trades, players

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(players.router, prefix="/players", tags=["players"])