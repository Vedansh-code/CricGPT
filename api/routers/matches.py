from fastapi import APIRouter, Path
from api.response import EnvelopeResponse
from api.schemas.match import MatchSummaryResponse, MatchScorecardResponse
from analytics.match import get_match_summary, get_scorecard

router = APIRouter()


@router.get("/{match_id}/summary", response_model=EnvelopeResponse[MatchSummaryResponse])
def get_summary(
    match_id: int = Path(..., gt=0, description="The match ID")
):
    res = get_match_summary(match_id)
    return EnvelopeResponse(data=res)


@router.get("/{match_id}/scorecard", response_model=EnvelopeResponse[MatchScorecardResponse])
def get_match_scorecard(
    match_id: int = Path(..., gt=0, description="The match ID")
):
    res = get_scorecard(match_id)
    return EnvelopeResponse(data=res)
