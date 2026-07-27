from typing import List, Optional
from pydantic import BaseModel

class MatchVenueInfo(BaseModel):
    venue_id: Optional[int] = None
    venue_name: Optional[str] = None
    city: Optional[str] = None

class MatchTeamInfo(BaseModel):
    team_id: int
    team_name: str

class MatchTossInfo(BaseModel):
    winner: Optional[MatchTeamInfo] = None
    decision: Optional[str] = None

class MatchResultInfo(BaseModel):
    winner: Optional[MatchTeamInfo] = None
    result_type: Optional[str] = None
    margin: Optional[int] = None
    winning_margin_text: str

class MatchPlayerOfMatchInfo(BaseModel):
    player_id: str
    player_name: str

class InningsBriefSummary(BaseModel):
    innings_no: int
    batting_team: str
    bowling_team: str
    runs: int
    wickets: int
    overs: Optional[str] = None
    score: str
    run_rate: float

class MatchSummaryResponse(BaseModel):
    match_id: int
    season: str
    date: str
    match_type: str
    venue: MatchVenueInfo
    team1: MatchTeamInfo
    team2: MatchTeamInfo
    toss: MatchTossInfo
    result: MatchResultInfo
    player_of_match: Optional[MatchPlayerOfMatchInfo] = None
    overs: Optional[str] = None
    event_name: Optional[str] = None
    gender: Optional[str] = None
    innings: List[InningsBriefSummary]

class BatterScorecardItem(BaseModel):
    batter_name: str
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: Optional[float] = None
    dismissal: str
    dismissed_by: Optional[str] = None
    fielders: List[str]

class BowlerScorecardItem(BaseModel):
    bowler_name: str
    overs: Optional[str] = None
    maidens: int
    runs: int
    wickets: int
    economy: Optional[float] = None

class ScorecardExtras(BaseModel):
    total: int
    wides: int
    no_balls: int
    byes: int
    leg_byes: int

class InningsDetailedCard(BaseModel):
    innings_no: int
    batting_team: str
    bowling_team: str
    batting_card: List[BatterScorecardItem]
    bowling_card: List[BowlerScorecardItem]
    total_runs: int
    total_wickets: int
    total_overs: Optional[str] = None
    score: str
    run_rate: float
    extras: ScorecardExtras

class MatchScorecardResponse(BaseModel):
    match_id: int
    innings: List[InningsDetailedCard]
