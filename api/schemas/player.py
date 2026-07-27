from typing import Optional
from pydantic import BaseModel

class PlayerSearchItem(BaseModel):
    player_id: str
    registry_id: str
    player_name: str

class PlayerProfile(BaseModel):
    player_id: str
    registry_id: str
    player_name: str

class PlayerCareer(BaseModel):
    player_id: str
    player_name: str
    matches: int
    batting_innings: int
    batting_runs: int
    batting_balls: int
    fours: int
    sixes: int
    hundreds: int
    fifties: int
    batting_average: float
    batting_strike_rate: float
    wickets: int
    bowling_runs: int
    bowling_balls: int
    bowling_average: Optional[float] = None
    bowling_economy: float
    bowling_strike_rate: Optional[float] = None
    catches: int
    run_outs: int

class PlayerMatchHistoryItem(BaseModel):
    match_id: int
    season: str
    date: str
    match_type: str
    venue_name: Optional[str] = None
    city: Optional[str] = None
    player_team: Optional[str] = None
    opponent_team: Optional[str] = None
    winner_team: Optional[str] = None
    result: Optional[str] = None
    result_margin: Optional[int] = None
    is_captain: bool
    is_keeper: bool
