from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, get_db
import os, models, crud, service

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
    
# @app.post("/sync/{username}")
# async def sync_user_endpoint(username: str, db: Session = Depends(get_db)):
#     try:
#         await service.sync_user(db, username)
#         return "Sucess!"
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/{username}")
async def sync_user_endpoint(username: str, db: Session = Depends(get_db)):
    try:
        leauge_ct, roster_ct, trade_ct, draft_ct = await service.sync_user_data(db, username)
        return f"Successfully synced {roster_ct} roster(s), {trade_ct} trades(s), and {draft_ct} draft(s) in {leauge_ct} leagues for {username}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))