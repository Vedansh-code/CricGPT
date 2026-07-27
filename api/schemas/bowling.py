from typing import Optional
from pydantic import BaseModel

class TopWicketTakerItem(BaseModel):
    player_id: str
    player_name: str
    wickets: int
    matches: int
    runs_conceded: int
    total_balls: int
    overs: float
    economy_rate: float
    bowling_average: Optional[float] = None
    strike_rate: Optional[float] = None

class PlayerEconomyRate(BaseModel):
    player_name: str
    runs_conceded: int
    balls_bowled: int
    overs: float
    innings: int
    economy_rate: float

class BestBowlingFiguresItem(BaseModel):
    match_id: int
    overs: str
    maidens: int
    runs: int
    wickets: int
    economy: float
    player_name: str
    bowling_team: str
    batting_team: str
    date: str
    season: str
