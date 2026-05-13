# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx, logging, os, debugpy
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.services import sleeper
from app.core.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    sleeper.client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))
    yield
    await sleeper.client.aclose()

app = FastAPI(title="Dynasty Database", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("DEBUG_MODE") == "true":
    debugpy.listen(("0.0.0.0", 5678))