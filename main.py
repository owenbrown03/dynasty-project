from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, get_db
import logger as log_config
import httpx, logging, service, sleeper, models

log_config.setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    sleeper.client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    yield
    await sleeper.client.aclose()

app = FastAPI(lifespan=lifespan)
models.Base.metadata.create_all(bind=engine)

@app.post("/sync/{username}")
async def create_user_endpoint(username: str, db: Session = Depends(get_db)):
    try:
        #user_ct, leauge_ct, roster_ct, trade_ct, draft_ct = 
        await service.create_user_data(db, username)
        #await service.create_lm_rosters(db)
        return "Successfully synced"
        #return f"Successfully synced {user_ct} users(s), {roster_ct} roster(s), {trade_ct} trades(s), and {draft_ct} draft(s) in {leauge_ct} leagues for {username}"
    except Exception as e:
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
    
    # Update the library loggers dynamically
    logging.getLogger("httpx").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(level)
    
    msg = f"Debug mode {'enabled' if status else 'disabled'}"
    logger.info(msg)
    return {"message": msg}