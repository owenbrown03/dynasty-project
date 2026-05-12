from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

## postgresql://[username]:[password]@[service]:[port]/[dbname]
SQLALCHEMY_DATABASE_URL = 'postgresql://admin:password123@db:5432/leaguemate_db'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()