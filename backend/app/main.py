import os, logging, debugpy
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.integrations.http.manager import HTTPClientManager
from app.integrations.redis.manager import RedisManager
from app.core.logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = await HTTPClientManager.get()
    app.state.redis = await RedisManager.get()

    yield

    await HTTPClientManager.close()
    await RedisManager.close()

app = FastAPI(title="Dynasty Database", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    logger.error(f"HTTP {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception("Unhandled server error")

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )

if os.getenv("DEBUG_MODE") == "true":
    try:
        debugpy.listen(("0.0.0.0", 5678))
        print("Debugger listening on port 5678")
    except RuntimeError as e:
        if "Address already in use" in str(e):
            print("Debugger already running, skipping.")
        else:
            raise