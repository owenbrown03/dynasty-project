from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, get_db
import os, models, crud, service

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.post("/sync/{username}")
async def create_user_endpoint(username: str, db: Session = Depends(get_db)):
    try:
        user_ct, leauge_ct, roster_ct, trade_ct, draft_ct = await service.create_user_data(db, username)
        await service.create_lm_lgs(db)
        return f"Successfully synced {user_ct} users(s), {roster_ct} roster(s), {trade_ct} trades(s), and {draft_ct} draft(s) in {leauge_ct} leagues for {username}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/admin/db-init")
def re_init_db():
    models.Base.metadata.create_all(bind=engine)
    return {"message": "Tables created (if they didn't exist)"}