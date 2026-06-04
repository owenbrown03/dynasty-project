import os, logging, debugpy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.integrations.sleeper.client import SleeperClientManager
from app.core.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sleeper = SleeperClientManager.get()
    yield
    await app.state.sleeper.close()

app = FastAPI(title="Dynasty Database", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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