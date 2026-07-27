from fastapi import APIRouter, Query
from api.response import EnvelopeResponse
from api.schemas.matchup import BatterVsBowlerMatchup
from analytics.matchup import get_batter_vs_bowler

router = APIRouter()


@router.get("/batter-vs-bowler", response_model=EnvelopeResponse[BatterVsBowlerMatchup])
def batter_vs_bowler(
    batter: str = Query(..., min_length=1, description="The name of the batter"),
    bowler: str = Query(..., min_length=1, description="The name of the bowler"),
):
    res = get_batter_vs_bowler(batter_name=batter, bowler_name=bowler)
    return EnvelopeResponse(data=res)
