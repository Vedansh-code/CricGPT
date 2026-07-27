from typing import List
from fastapi import APIRouter, Query, Path
from api.response import EnvelopeResponse, MetaModel
from api.schemas.batting import (
    TopRunScorerItem,
    HighestIndividualScoreItem,
    PlayerBattingAverage,
    PlayerStrikeRate,
    PlayerBoundaryPercentage,
)
from analytics.batting import (
    top_run_scorers,
    highest_individual_scores,
    batting_average,
    strike_rate,
    boundary_percentage,
)

router = APIRouter()


@router.get("/top-run-scorers", response_model=EnvelopeResponse[List[TopRunScorerItem]])
def get_top_run_scorers(
    limit: int = Query(10, gt=0, le=100, description="Number of top scorers to retrieve")
):
    res = top_run_scorers(limit)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res), limit=limit)
    )


@router.get("/highest-scores", response_model=EnvelopeResponse[List[HighestIndividualScoreItem]])
def get_highest_scores(
    limit: int = Query(10, gt=0, le=100, description="Number of top individual scores to retrieve")
):
    res = highest_individual_scores(limit)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res), limit=limit)
    )


@router.get("/{player_name}/average", response_model=EnvelopeResponse[PlayerBattingAverage])
def get_batting_average(
    player_name: str = Path(..., min_length=1, description="The name of the player")
):
    res = batting_average(player_name)
    return EnvelopeResponse(data=res)


@router.get("/{player_name}/strike-rate", response_model=EnvelopeResponse[PlayerStrikeRate])
def get_strike_rate(
    player_name: str = Path(..., min_length=1, description="The name of the player")
):
    res = strike_rate(player_name)
    return EnvelopeResponse(data=res)


@router.get("/{player_name}/boundary-percentage", response_model=EnvelopeResponse[PlayerBoundaryPercentage])
def get_boundary_percentage(
    player_name: str = Path(..., min_length=1, description="The name of the player")
):
    res = boundary_percentage(player_name)
    return EnvelopeResponse(data=res)
