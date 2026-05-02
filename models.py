from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from dataclasses import dataclass
from database import Base
from typing import Set, Tuple
import schemas

@dataclass
class Info:
    main_user: schemas.SleeperUser
    state: schemas.NFLState
    player_map: schemas.PlayerMap
    lms: Set[str]
    db_leagues: Set[str]
    db_users: Set[str]
    db_rosters: Set[Tuple[str, str]] # roster_id, owner_id
    db_txs: Set[str]
    db_drafts: Set[str]

class InternalState(Base):
    __tablename__ = "internal_state"
    key = Column(String, primary_key=True)
    value = Column(String)

class League(Base):
    __tablename__ = "leagues"
    rosters = relationship("Roster", back_populates="league", lazy="selectin")
    transactions = relationship("Transaction", back_populates="league", lazy="selectin")
    drafts = relationship("Draft", back_populates="league", lazy="joined")
    league_id = Column(String, primary_key=True)
    name = Column(String)
    total_rosters = Column(Integer)
    draft_id = Column(String, unique=True, nullable=True, index=True)
    avatar = Column(String)
    season = Column(String)
    dynasty = Column(Boolean)
    best_ball = Column(Boolean)
    trade_deadline = Column(Integer)
    bonus_rec_te = Column(Integer)
    rec = Column(Integer)
    pass_td = Column(Integer)
    roster_positions = Column(ARRAY(String), nullable=True)

class Roster(Base):
    __tablename__ = "rosters"
    league = relationship("League", back_populates="rosters", lazy="joined")
    users = relationship("User", back_populates="rosters", lazy="selectin")
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
    rosters = relationship("Roster", back_populates="users", lazy="joined")
    user_id = Column(String, primary_key=True)
    display_name = Column(String)
    avatar = Column(String)
    is_owner = Column(Boolean)
    
class Transaction(Base):
    __tablename__ = "transactions"
    league = relationship("League", back_populates="transactions", lazy="joined")
    movements = relationship("Movement", back_populates="transactions", lazy="selectin")
    draft_picks = relationship("TradedPick", back_populates="transactions", lazy="selectin")
    waiver_budget = relationship("WaiverBudget", back_populates="transactions", lazy="selectin")
    transaction_id = Column(String, primary_key=True)
    type = Column(String, index=True)
    time_ms = Column(BigInteger)
    league_id = Column(String, ForeignKey("leagues.league_id"), nullable=False, index=True)

class Draft(Base):
    __tablename__ = "drafts"
    league = relationship("League", back_populates="drafts", lazy="joined")
    draft_id = Column(String, primary_key=True) 
    league_id = Column(String, ForeignKey("leagues.league_id"), index=True) 
    draft_order = Column(JSONB, nullable=True, default={})
    slot_to_roster_id = Column(JSONB, nullable=True, default={})

class Movement(Base):
    __tablename__ = "movements"
    transactions = relationship("Transaction", back_populates="movements", lazy="joined")
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True)
    player_id = Column(String, index=True)
    roster_id = Column(Integer, index=True)
    action = Column(String, index=True)

class WaiverBudget(Base):
    __tablename__ = "waiver_transfers"
    transactions = relationship("Transaction", back_populates="waiver_budget", lazy="joined")
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True)
    sender = Column(Integer, index=True)
    receiver = Column(Integer, index=True)
    amount = Column(Integer)

class TradedPick(Base):
    __tablename__ = "traded_picks"
    transactions = relationship("Transaction", back_populates="draft_picks", lazy="joined")
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), index=True)
    season = Column(String, index=True)
    round = Column(Integer, index=True)
    new_owner_id = Column(Integer, index=True)
    old_owner_id = Column(Integer, index=True)

class Player(Base):
    __tablename__ = "players"
    player_id = Column(String, primary_key=True)
    position = Column(String, index=True)
    team = Column(String, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    age = Column(Integer, index=True)
    years_exp = Column(Integer, index=True)