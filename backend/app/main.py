import logging
import os
from contextlib import asynccontextmanager

import debugpy
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.infrastructure.http.manager import HTTPClientManager
from app.infrastructure.redis.manager import RedisManager
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
    allow_origins=settings.cors_origins,
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
        logger.info("Debugger listening on port 5678")
    except RuntimeError as e:
        if "Address already in use" in str(e):
            logger.info("Debugger already running, skipping.")
        else:
            raise
