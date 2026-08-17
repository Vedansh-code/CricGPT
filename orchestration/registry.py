"""
Capability Registry for CricGPT Orchestration (Phase 3A.3).

This module defines the Capability model and CapabilityRegistry for mapping
Intent enum values to Phase 1 analytics SDK callables and argument contracts.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Dict

from orchestration.intents import Intent
from orchestration.exceptions import UnsupportedIntentError
import analytics


@dataclass(frozen=True)
class Capability:
    """
    Represents an executable CricGPT capability.

    Attributes:
        intent: The Intent enum value.
        name: Human-readable name of the capability.
        description: Description of what the capability does.
        handler: The underlying Phase 1 SDK callable.
        required_arguments: List of required argument names from QueryArguments.
        optional_arguments: List of optional argument names from QueryArguments.
    """

    intent: Intent
    name: str
    description: str
    handler: Callable
    required_arguments: List[str] = field(default_factory=list)
    optional_arguments: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.intent == Intent.UNKNOWN:
            raise ValueError("UNKNOWN cannot be registered as an executable capability.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Capability name cannot be empty or non-string.")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("Capability description cannot be empty or non-string.")
        if not callable(self.handler):
            raise ValueError("Capability handler must be callable.")


class CapabilityRegistry:
    """
    Registry for managing and resolving executable CricGPT capabilities.
    """

    def __init__(self):
        self._capabilities: Dict[Intent, Capability] = {}

    def register(self, capability: Capability) -> None:
        """
        Register a new capability.

        Args:
            capability: The Capability object to register.

        Raises:
            ValueError: If Intent is UNKNOWN or capability for intent is already registered.
        """
        if capability.intent == Intent.UNKNOWN:
            raise ValueError("UNKNOWN cannot be registered as an executable capability.")
        if capability.intent in self._capabilities:
            raise ValueError(f"Capability for intent '{capability.intent.value}' is already registered.")

        self._capabilities[capability.intent] = capability

    def get(self, intent: Intent) -> Capability:
        """
        Retrieve a registered capability by intent.

        Args:
            intent: The Intent enum value to resolve.

        Returns:
            Capability object.

        Raises:
            UnsupportedIntentError: If the intent is missing or unsupported.
        """
        if intent not in self._capabilities:
            raise UnsupportedIntentError(f"No capability registered for intent '{intent.value}'.")
        return self._capabilities[intent]

    def has(self, intent: Intent) -> bool:
        """Check if an intent is registered in the registry."""
        return intent in self._capabilities

    def all(self) -> List[Capability]:
        """Return a list of all registered capabilities."""
        return list(self._capabilities.values())

    def count(self) -> int:
        """Return the total number of registered capabilities."""
        return len(self._capabilities)


def get_default_registry() -> CapabilityRegistry:
    """
    Construct and return the default CapabilityRegistry pre-populated with
    all 19 Phase 1 Analytics SDK capabilities.
    """
    registry = CapabilityRegistry()

    # Player Capabilities
    registry.register(Capability(
        intent=Intent.PLAYER_SEARCH,
        name="Search Players",
        description="Search for players by name.",
        handler=analytics.search_players,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.PLAYER_PROFILE,
        name="Get Player Profile",
        description="Retrieve basic player details and registry information.",
        handler=analytics.get_player,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.PLAYER_CAREER,
        name="Get Player Career",
        description="Retrieve comprehensive career summary statistics for a player.",
        handler=analytics.get_player_career,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.PLAYER_RECENT_MATCHES,
        name="Get Player Recent Matches",
        description="Retrieve recent match history for a player up to N matches.",
        handler=analytics.get_player_last_n_matches,
        required_arguments=["player_name"],
        optional_arguments=["limit"]
    ))
    registry.register(Capability(
        intent=Intent.PLAYER_MATCH_HISTORY,
        name="Get Player Match History",
        description="Retrieve full chronological match history for a player.",
        handler=analytics.get_player_match_history,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))

    # Batting Capabilities
    registry.register(Capability(
        intent=Intent.TOP_RUN_SCORERS,
        name="Top Run Scorers",
        description="Retrieve top run scorers overall.",
        handler=analytics.top_run_scorers,
        required_arguments=[],
        optional_arguments=["limit"]
    ))
    registry.register(Capability(
        intent=Intent.HIGHEST_INDIVIDUAL_SCORES,
        name="Highest Individual Scores",
        description="Retrieve highest individual scores in a single innings.",
        handler=analytics.highest_individual_scores,
        required_arguments=[],
        optional_arguments=["limit"]
    ))
    registry.register(Capability(
        intent=Intent.BATTING_AVERAGE,
        name="Batting Average",
        description="Get batting average statistics for a player.",
        handler=analytics.batting_average,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.BATTING_STRIKE_RATE,
        name="Batting Strike Rate",
        description="Get batting strike rate statistics for a player.",
        handler=analytics.strike_rate,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.BOUNDARY_PERCENTAGE,
        name="Boundary Percentage",
        description="Get boundary statistics and percentage for a player.",
        handler=analytics.boundary_percentage,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))

    # Bowling Capabilities
    registry.register(Capability(
        intent=Intent.TOP_WICKET_TAKERS,
        name="Top Wicket Takers",
        description="Retrieve top wicket takers overall.",
        handler=analytics.top_wicket_takers,
        required_arguments=[],
        optional_arguments=["limit"]
    ))
    registry.register(Capability(
        intent=Intent.BEST_BOWLING_FIGURES,
        name="Best Bowling Figures",
        description="Retrieve best individual bowling figures in a single innings.",
        handler=analytics.best_bowling_figures,
        required_arguments=[],
        optional_arguments=["limit"]
    ))
    registry.register(Capability(
        intent=Intent.BOWLING_ECONOMY,
        name="Bowling Economy",
        description="Get bowling economy statistics for a player.",
        handler=analytics.economy_rate,
        required_arguments=["player_name"],
        optional_arguments=[]
    ))

    # Matchup Capabilities
    registry.register(Capability(
        intent=Intent.BATTER_VS_BOWLER,
        name="Batter vs Bowler Matchup",
        description="Retrieve player-versus-player head-to-head matchup statistics.",
        handler=analytics.get_batter_vs_bowler,
        required_arguments=["batter", "bowler"],
        optional_arguments=[]
    ))

    # Team Capabilities
    registry.register(Capability(
        intent=Intent.TEAM_RECORD,
        name="Team Record",
        description="Retrieve performance statistics for a team.",
        handler=analytics.get_team_record,
        required_arguments=["team_name"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.TEAM_HEAD_TO_HEAD,
        name="Team Head to Head",
        description="Retrieve head-to-head record between two teams.",
        handler=analytics.head_to_head,
        required_arguments=["team1", "team2"],
        optional_arguments=[]
    ))

    # Venue Capabilities
    registry.register(Capability(
        intent=Intent.VENUE_SUMMARY,
        name="Venue Summary",
        description="Retrieve statistics summary for a given stadium/venue.",
        handler=analytics.venue_summary,
        required_arguments=["venue_name"],
        optional_arguments=[]
    ))

    # Match Capabilities
    registry.register(Capability(
        intent=Intent.MATCH_SUMMARY,
        name="Match Summary",
        description="Retrieve comprehensive match summary information.",
        handler=analytics.get_match_summary,
        required_arguments=["match_id"],
        optional_arguments=[]
    ))
    registry.register(Capability(
        intent=Intent.MATCH_SCORECARD,
        name="Match Scorecard",
        description="Retrieve full detailed scorecard for a match.",
        handler=analytics.get_scorecard,
        required_arguments=["match_id"],
        optional_arguments=[]
    ))

    return registry
