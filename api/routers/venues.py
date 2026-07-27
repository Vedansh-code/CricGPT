from fastapi import APIRouter, Path
from api.response import EnvelopeResponse
from api.schemas.venue import VenueSummaryResponse
from analytics.venue import venue_summary

router = APIRouter()


@router.get("/{venue_name}/summary", response_model=EnvelopeResponse[VenueSummaryResponse])
def get_venue_summary(
    venue_name: str = Path(..., min_length=1, description="The name of the venue")
):
    res = venue_summary(venue_name)
    return EnvelopeResponse(data=res)
