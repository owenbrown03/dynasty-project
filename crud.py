from sqlalchemy import inspect
from sqlalchemy.orm import Session
import models

# -- GENERIC --
def create(db: Session, model):
    try:
        db_entry = db.merge(model)
        db.commit()
        db.refresh(db_entry)
        return db_entry
    except Exception as e:
        db.rollback()   
        try:
            pk_columns = inspect(model.__class__).primary_key
            pk_values = [getattr(model, col.name) for col in pk_columns]
            pk_display = ", ".join(map(str, pk_values))
        except Exception:
            pk_display = "Unknown PK"
        print(f"--- [SYNC ERROR] ---")
        print(f"Model: {model.__class__.__name__}")
        print(f"PK Value: {pk_display}")
        print(f"Error: {e}")
        return None

def read_all(db: Session, model):
    return db.query(model).all()

# -- LEAGUE --
def get_league(db: Session, league_id: str):
    return db.query(models.League).filter(models.League.league_id == league_id).first()

def get_rosters_by_league(db: Session, league_id: str):
    return db.query(models.Roster).filter(models.Roster.league_id == league_id).all()

def delete_league(db: Session, league_id: str):
    db_league = db.query(models.League).filter(models.League.league_id == league_id).first()
    if db_league:
        try:
            db.delete(db_league)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting league {league_id}: {e}")
            raise e
    return False