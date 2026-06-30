from typing import Optional
from pydantic import BaseModel


class FantasyCalcPlayer(BaseModel):
    id: int
    name: str
    sleeperId: Optional[str] = None
    position: Optional[str] = None
    maybeTeam: Optional[str] = None
    maybeAge: Optional[float] = None
    maybeYoe: Optional[int] = None


class FantasyCalcValue(BaseModel):
    player: FantasyCalcPlayer

    value: int
    overallRank: int
    positionRank: int

    trend30Day: Optional[int] = None

    redraftValue: Optional[int] = None
    combinedValue: Optional[int] = None

    maybeTier: Optional[int] = None
    maybeAdp: Optional[float] = None