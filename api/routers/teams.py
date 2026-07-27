from fastapi import APIRouter, Query, Path
from api.response import EnvelopeResponse
from api.schemas.team import TeamRecordResponse, TeamHeadToHeadResponse
from analytics.team import get_team_record, head_to_head

router = APIRouter()


@router.get("/head-to-head", response_model=EnvelopeResponse[TeamHeadToHeadResponse])
def get_head_to_head(
    team1: str = Query(..., min_length=1, description="The first team name or abbreviation"),
    team2: str = Query(..., min_length=1, description="The second team name or abbreviation"),
):
    res = head_to_head(team1, team2)
    return EnvelopeResponse(data=res)


@router.get("/{team_name}/record", response_model=EnvelopeResponse[TeamRecordResponse])
def get_record(
    team_name: str = Path(..., min_length=1, description="The team name or abbreviation")
):
    res = get_team_record(team_name)
    return EnvelopeResponse(data=res)
