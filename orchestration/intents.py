"""
Orchestration Intent Definitions for CricGPT.

This module defines the strongly typed Intent enumeration covering all supported
cricket analytics capabilities in the CricGPT platform.
"""

from enum import Enum


class Intent(Enum):
    """
    Strongly typed enumeration of all query intents supported by CricGPT.

    Each intent maps to a specific capability within the domain SDK.
    """

    # Player Intents
    PLAYER_SEARCH = "PLAYER_SEARCH"
    PLAYER_PROFILE = "PLAYER_PROFILE"
    PLAYER_CAREER = "PLAYER_CAREER"
    PLAYER_RECENT_MATCHES = "PLAYER_RECENT_MATCHES"
    PLAYER_MATCH_HISTORY = "PLAYER_MATCH_HISTORY"

    # Batting Analytics Intents
    TOP_RUN_SCORERS = "TOP_RUN_SCORERS"
    HIGHEST_INDIVIDUAL_SCORES = "HIGHEST_INDIVIDUAL_SCORES"
    BATTING_AVERAGE = "BATTING_AVERAGE"
    BATTING_STRIKE_RATE = "BATTING_STRIKE_RATE"
    BOUNDARY_PERCENTAGE = "BOUNDARY_PERCENTAGE"

    # Bowling Analytics Intents
    TOP_WICKET_TAKERS = "TOP_WICKET_TAKERS"
    BEST_BOWLING_FIGURES = "BEST_BOWLING_FIGURES"
    BOWLING_ECONOMY = "BOWLING_ECONOMY"

    # Matchup Intents
    BATTER_VS_BOWLER = "BATTER_VS_BOWLER"

    # Team Analytics Intents
    TEAM_RECORD = "TEAM_RECORD"
    TEAM_HEAD_TO_HEAD = "TEAM_HEAD_TO_HEAD"

    # Venue Intents
    VENUE_SUMMARY = "VENUE_SUMMARY"

    # Match Intents
    MATCH_SUMMARY = "MATCH_SUMMARY"
    MATCH_SCORECARD = "MATCH_SCORECARD"

    # Fallback Intent
    UNKNOWN = "UNKNOWN"
