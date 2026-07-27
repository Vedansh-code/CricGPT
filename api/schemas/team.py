from typing import List, Optional
from pydantic import BaseModel

class TeamRecordResponse(BaseModel):
    team_name: str
    matches: int
    wins: int
    losses: int
    ties: int
    win_percentage: float
    avg_score: float
    avg_conceded: float

class HeadToHeadMatchItem(BaseModel):
    match_id: int
    season: str
    date: str
    venue: str
    winner: Optional[str] = None
    result: Optional[str] = None
    margin: Optional[int] = None

class TeamHeadToHeadResponse(BaseModel):
    team1: str
    team2: str
    matches_played: int
    team1_wins: int
    team2_wins: int
    ties_or_no_results: int
    recent_matches: List[HeadToHeadMatchItem]
