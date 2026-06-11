from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints.sleeper import auth as sleeper_auth
from app.api.v1.endpoints.sleeper import connection, players, trades, users, write

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sleeper_auth.router, prefix="/sleeper/auth", tags=["sleeper auth"])
api_router.include_router(connection.router, prefix="/sleeper/connection", tags=["connection"])
api_router.include_router(players.router, prefix="/sleeper/players", tags=["players"])
api_router.include_router(trades.router, prefix="/sleeper/trades", tags=["trades"])
api_router.include_router(users.router, prefix="/sleeper/users", tags=["users"])
api_router.include_router(write.router, prefix="/sleeper/write", tags=["write"])
