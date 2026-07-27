from typing import Optional
from pydantic import BaseModel

class TopRunScorerItem(BaseModel):
    player_id: str
    player_name: str
    runs: int
    matches: int
    innings: int
    balls: int
    fours: int
    sixes: int
    dismissals: int
    average: float
    strike_rate: float

class HighestIndividualScoreItem(BaseModel):
    match_id: int
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: float
    dismissal_type: str
    player_name: str
    batting_team: str
    bowling_team: str
    date: str
    season: str

class PlayerBattingAverage(BaseModel):
    player_name: str
    runs: int
    innings: int
    dismissals: int
    batting_average: float

class PlayerStrikeRate(BaseModel):
    player_name: str
    runs: int
    balls: int
    innings: int
    strike_rate: float

class PlayerBoundaryPercentage(BaseModel):
    player_name: str
    runs: int
    balls: int
    innings: int
    fours: int
    sixes: int
    boundary_runs: int
    boundary_runs_percentage: float
    boundary_balls_percentage: float
