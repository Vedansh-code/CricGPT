import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from analytics.utils import (
    PlayerNotFoundError,
    TeamNotFoundError,
    VenueNotFoundError,
    MatchNotFoundError,
    AmbiguousMatchError,
    CricGPTAnalyticsError,
)

logger = logging.getLogger("cricgpt_api")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "")
        errors.append(f"{loc}: {msg}")
    message = "; ".join(errors)
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": message
            }
        }
    )


async def not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc)
            }
        }
    )


async def ambiguous_match_exception_handler(request: Request, exc: AmbiguousMatchError):
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "error": {
                "type": "AmbiguousMatchError",
                "message": str(exc)
            }
        }
    )


async def analytics_exception_handler(request: Request, exc: CricGPTAnalyticsError):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc)
            }
        }
    )


async def internal_server_error_handler(request: Request, exc: Exception):
    logger.exception("Unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected internal server error occurred."
            }
        }
    )
