from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from database import Base

class League(Base):
    __tablename__ = "leagues"
    rosters = relationship("Roster", back_populates="league")
    transactions = relationship("Transaction", back_populates="league")
    drafts = relationship("Draft", back_populates="league")
    league_id = Column(String, primary_key=True)
    name = Column(String)
    total_rosters = Column(Integer)
    draft_id = Column(String, unique=True, nullable=True, index=True)
    avatar = Column(String)
    season = Column(String)
    best_ball = Column(Boolean)
    trade_deadline = Column(Integer)
    bonus_rec_te = Column(Integer)
    rec = Column(Integer)
    pass_td = Column(Integer)
    roster_positions = Column(ARRAY(String), nullable=True)

class Roster(Base):
    __tablename__ = "rosters"
    league = relationship("League", back_populates="rosters")
    users = relationship("User", back_populates="rosters")
    id = Column(Integer, primary_key=True)
    roster_id = Column(Integer, index=True)
    owner_id = Column(String, ForeignKey("users.user_id"), index=True, nullable=True) # also known as user_id
    league_id = Column(String, ForeignKey("leagues.league_id"), index=True)
    players = Column(ARRAY(String), nullable=True)
    fpts = Column(Integer, default=0)
    fpts_against = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    losses = Column(Integer, default=0)

class User(Base):
    __tablename__ = "users"
    rosters = relationship("Roster", back_populates="users")
    user_id = Column(String, primary_key=True)
    display_name = Column(String)
    avatar = Column(String)
    is_owner = Column(Boolean)
    
class Transaction(Base):
    __tablename__ = "transactions"
    league = relationship("League", back_populates="transactions")
    movements = relationship("Movement", back_populates="transactions")
    draft_picks = relationship("TradedPick", back_populates="transactions")
    waiver_budget = relationship("WaiverBudget", back_populates="transactions")
    transaction_id = Column(String, primary_key=True)
    type = Column(String)
    time_ms = Column(BigInteger)
    league_id = Column(String, ForeignKey("leagues.league_id"), nullable=False, index=True)

class Draft(Base):
    __tablename__ = "drafts"
    league = relationship("League", back_populates="drafts")
    draft_id = Column(String, primary_key=True) 
    league_id = Column(String, ForeignKey("leagues.league_id"), index=True) 
    draft_order = Column(JSONB, nullable=True, default={})
    slot_to_roster_id = Column(JSONB, nullable=True, default={})

class Movement(Base):
    __tablename__ = "movements"
    transactions = relationship("Transaction", back_populates="movements")
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True)
    player_id = Column(String)
    roster_id = Column(Integer)
    action = Column(String)

class WaiverBudget(Base):
    __tablename__ = "waiver_transfers"
    transactions = relationship("Transaction", back_populates="waiver_budget")
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True)
    sender = Column(Integer)
    receiver = Column(Integer)
    amount = Column(Integer)

class TradedPick(Base):
    __tablename__ = "traded_picks"
    transactions = relationship("Transaction", back_populates="draft_picks")
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    season = Column(String)
    round = Column(Integer)
    new_owner_id = Column(Integer)
    old_owner_id = Column(Integer)