from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, get_db
import logger as log_config
import httpx, logging, service, sleeper, models, traceback

log_config.setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    sleeper.client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))
    yield
    await sleeper.client.aclose()

app = FastAPI(lifespan=lifespan)
models.Base.metadata.create_all(bind=engine)

@app.post("/users/{username}/sync")
async def create_user_endpoint(username: str, db: Session = Depends(get_db)):
    try:
        info = await service.info_sync(db, username)
        await service.create_lm_data(db, info)
        return "Successfully synced user"
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/players/sync")
async def sync_players_endpoint(db: Session = Depends(get_db)):
    try:
        await service.sync_players(db)
        return "Successfully synced players"
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/db-init")
def re_init_db():
    models.Base.metadata.create_all(bind=engine)
    msg = "Tables created (if they didn't exist)"
    logger.info(msg)
    return msg

@app.get("/admin/set-debug/{status}")
def set_debug_mode(status: bool):
    level = logging.INFO if status else logging.WARNING
    logging.getLogger("httpx").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(level)
    msg = f"Debug mode {'enabled' if status else 'disabled'}"
    logger.info(msg)
    return {"message": msg}