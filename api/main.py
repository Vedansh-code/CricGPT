from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from api.config import settings
from api.routers import (
    health,
    players,
    batting,
    bowling,
    matchups,
    teams,
    venues,
    matches,
)
from api.routers.health import get_health
from api.exception_handlers import (
    validation_exception_handler,
    not_found_exception_handler,
    ambiguous_match_exception_handler,
    analytics_exception_handler,
    internal_server_error_handler,
)
from analytics.utils import (
    PlayerNotFoundError,
    TeamNotFoundError,
    VenueNotFoundError,
    MatchNotFoundError,
    AmbiguousMatchError,
    CricGPTAnalyticsError,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-quality FastAPI backend service layer over the CricGPT Cricket Analytics SDK.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health endpoint (un-prefixed)
@app.get("/health", response_model=dict, tags=["health"])
def root_health():
    return get_health()

# Register API v1 prefixed routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(batting.router, prefix="/api/v1/batting", tags=["batting"])
app.include_router(bowling.router, prefix="/api/v1/bowling", tags=["bowling"])
app.include_router(matchups.router, prefix="/api/v1/matchups", tags=["matchups"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(venues.router, prefix="/api/v1/venues", tags=["venues"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])

# Centralized exception handlers registration
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(PlayerNotFoundError, not_found_exception_handler)
app.add_exception_handler(TeamNotFoundError, not_found_exception_handler)
app.add_exception_handler(VenueNotFoundError, not_found_exception_handler)
app.add_exception_handler(MatchNotFoundError, not_found_exception_handler)
app.add_exception_handler(AmbiguousMatchError, ambiguous_match_exception_handler)
app.add_exception_handler(CricGPTAnalyticsError, analytics_exception_handler)
app.add_exception_handler(Exception, internal_server_error_handler)
