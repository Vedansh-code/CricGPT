from pydantic import BaseModel

class BatterVsBowlerMatchup(BaseModel):
    batter_name: str
    bowler_name: str
    balls: int
    runs: int
    dots: int
    fours: int
    sixes: int
    dismissals: int
    strike_rate: float
    average: float
