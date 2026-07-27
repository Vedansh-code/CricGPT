from typing import List
from fastapi import APIRouter, Query, Path
from api.response import EnvelopeResponse, MetaModel
from api.schemas.player import (
    PlayerSearchItem,
    PlayerProfile,
    PlayerCareer,
    PlayerMatchHistoryItem,
)
from analytics.player import (
    search_players,
    get_player,
    get_player_career,
    get_player_match_history,
    get_player_last_n_matches,
)

router = APIRouter()


@router.get("/search", response_model=EnvelopeResponse[List[PlayerSearchItem]])
def search(q: str = Query(..., min_length=1, description="Search query for player names")):
    res = search_players(q)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res))
    )


@router.get("/{player_name}/profile", response_model=EnvelopeResponse[PlayerProfile])
def profile(player_name: str = Path(..., min_length=1, description="The name of the player")):
    res = get_player(player_name)
    return EnvelopeResponse(data=res)


@router.get("/{player_name}/career", response_model=EnvelopeResponse[PlayerCareer])
def career(player_name: str = Path(..., min_length=1, description="The name of the player")):
    res = get_player_career(player_name)
    return EnvelopeResponse(data=res)


@router.get("/{player_name}/recent-matches", response_model=EnvelopeResponse[List[PlayerMatchHistoryItem]])
def recent_matches(
    player_name: str = Path(..., min_length=1, description="The name of the player"),
    limit: int = Query(5, gt=0, le=100, description="Number of recent matches to return"),
):
    res = get_player_last_n_matches(player_name, limit)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res), limit=limit)
    )


@router.get("/{player_name}/matches", response_model=EnvelopeResponse[List[PlayerMatchHistoryItem]])
def matches(player_name: str = Path(..., min_length=1, description="The name of the player")):
    res = get_player_match_history(player_name)
    return EnvelopeResponse(
        data=res,
        meta=MetaModel(count=len(res))
    )
