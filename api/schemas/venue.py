from typing import Optional
from pydantic import BaseModel

class VenueSummaryResponse(BaseModel):
    venue_name: str
    city: Optional[str] = None
    matches_played: int
    avg_first_innings_score: float
    avg_second_innings_score: float
    highest_score: int
    lowest_score: int
    successful_chases: int
    bat_first_wins: int
    bowl_first_wins: int
