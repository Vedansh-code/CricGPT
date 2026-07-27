from typing import List
from fastapi import APIRouter, Query, Path
from api.response import EnvelopeResponse, MetaModel
from api.schemas.bowling import (
    TopWicketTakerItem,
    PlayerEconomyRate,
    BestBowlingFiguresItem,
)
from analytics.bowling import (
    top_wicket_takers,
    economy_rate,
    best_bowling_figures,
)

router = APIRouter()


@router.get("/top-wicket-takers", response_model=EnvelopeResponse[List[TopWicketTakerItem]])
def get_top_wicket_takers(
    limit: int = Query(10, gt=0, le=100, description="Number of top wicket takers to retrieve")
):
    res = top_wicket_takers(limit)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res), limit=limit)
    )


@router.get("/best-figures", response_model=EnvelopeResponse[List[BestBowlingFiguresItem]])
def get_best_figures(
    limit: int = Query(10, gt=0, le=100, description="Number of best bowling figures to retrieve")
):
    res = best_bowling_figures(limit)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res), limit=limit)
    )


@router.get("/{player_name}/economy", response_model=EnvelopeResponse[PlayerEconomyRate])
def get_economy_rate(
    player_name: str = Path(..., min_length=1, description="The name of the player")
):
    res = economy_rate(player_name)
    return EnvelopeResponse(data=res)
