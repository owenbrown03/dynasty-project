from pydantic import BaseModel


class DashboardOwner(BaseModel):

    user_id: str
    display_name: str
    avatar: str | None = None



class DashboardPlayer(BaseModel):

    player_id: str

    name: str
    position: str
    team: str | None = None

    age: float | None = None

    ktc_value: int | None = None
    fc_value: int | None = None
    underdog_position_rank: str | None = None

    starter_war: float | None = None
    roster_war: float | None = None



class DashboardRoster(BaseModel):

    roster_id: int

    owner: DashboardOwner

    rank: int | None = None

    total_starter_war: float
    total_roster_war: float

    players: list[DashboardPlayer]



class DashboardLeague(BaseModel):

    league_id: str
    league_name: str

    rosters: list[DashboardRoster]