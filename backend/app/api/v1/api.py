from fastapi import APIRouter
from app.api.v1.endpoints import auth, bootstrap, sync, test
from app.api.v1.endpoints.sleeper import auth as sleeper_auth
from app.api.v1.endpoints.sleeper import connection, leagues, players, trades, users, waivers, write

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(bootstrap.router, prefix="/bootstrap", tags=["bootstrap"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(sleeper_auth.router, prefix="/sleeper/auth", tags=["sleeper auth"])
api_router.include_router(connection.router, prefix="/sleeper/connection", tags=["connection"])
api_router.include_router(leagues.router, prefix="/sleeper/leagues", tags=["leagues"])
api_router.include_router(players.router, prefix="/sleeper/players", tags=["players"])
api_router.include_router(trades.router, prefix="/sleeper/trades", tags=["trades"])
api_router.include_router(users.router, prefix="/sleeper/users", tags=["users"])
api_router.include_router(waivers.router, prefix="/sleeper/waivers", tags=["waivers"])
#api_router.include_router(write.router, prefix="/sleeper/write", tags=["write"])

api_router.include_router(test.router, prefix="/test", tags=["test"])
