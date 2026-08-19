"""
Unit tests for LLM Query Planner and LLMProvider abstraction (Phase 3B.1).
"""

import unittest
from typing import Dict, Type, TypeVar, Optional, Callable, Any, cast
from pydantic import BaseModel

from orchestration.exceptions import PlanningError
from orchestration.intents import Intent
from orchestration.schemas import QueryArguments, QueryPlan
from orchestration.llm.provider import LLMProvider
from orchestration.llm.planner import LLMQueryPlanner, LLMPlanOutput

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM Provider for unit testing offline.
    """

    def __init__(
        self,
        response_map: Optional[Dict[str, Any]] = None,
        default_response: Optional[Any] = None,
        raise_error: bool = False,
        custom_handler: Optional[Callable[[str, str, Type[Any]], Any]] = None,
    ) -> None:
        self.response_map = response_map or {}
        self.default_response = default_response or LLMPlanOutput(intent=Intent.UNKNOWN)
        self.raise_error = raise_error
        self.custom_handler = custom_handler
        self.calls = []

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        self.calls.append((system_prompt, user_prompt, response_model))
        if self.raise_error:
            raise RuntimeError("Mock LLM network failure")
        if self.custom_handler:
            return cast(T, self.custom_handler(system_prompt, user_prompt, response_model))
        if user_prompt in self.response_map:
            res = self.response_map[user_prompt]
            return cast(T, res)
        return cast(T, self.default_response)


class TestLLMProviderAbstraction(unittest.TestCase):
    """Test LLMProvider interface, constructor injection, and exception wrapping."""

    def test_provider_injection(self):
        provider = MockLLMProvider()
        planner = LLMQueryPlanner(provider=provider)
        self.assertEqual(planner._provider, provider)

    def test_invalid_provider_injection_raises_type_error(self):
        with self.assertRaises(TypeError):
            LLMQueryPlanner(provider="not_a_provider")  # type: ignore

        with self.assertRaises(TypeError):
            LLMQueryPlanner(provider=None)  # type: ignore

    def test_provider_failure_converted_to_planning_error(self):
        provider = MockLLMProvider(raise_error=True)
        planner = LLMQueryPlanner(provider=provider)

        with self.assertRaises(PlanningError) as ctx:
            planner.plan("What is Virat Kohli's batting average?")
        self.assertIn("LLM provider failed during plan generation", str(ctx.exception))


class TestLLMQueryPlanner(unittest.TestCase):
    """Test LLMQueryPlanner intent mapping, entity extraction, clarification, and validation."""

    def setUp(self):
        self.response_map = {
            "What is Virat Kohli's batting average?": LLMPlanOutput(
                intent=Intent.BATTING_AVERAGE,
                arguments=QueryArguments(player_name="Virat Kohli"),
                confidence=0.95,
            ),
            "What is Kohli's strike rate?": LLMPlanOutput(
                intent=Intent.BATTING_STRIKE_RATE,
                arguments=QueryArguments(player_name="Kohli"),
                confidence=0.92,
            ),
            "Who has scored the most runs?": LLMPlanOutput(
                intent=Intent.TOP_RUN_SCORERS,
                arguments=QueryArguments(limit=10),
                confidence=0.90,
            ),
            "Who has taken the most wickets?": LLMPlanOutput(
                intent=Intent.TOP_WICKET_TAKERS,
                arguments=QueryArguments(limit=10),
                confidence=0.91,
            ),
            "How has Virat Kohli performed against Jasprit Bumrah?": LLMPlanOutput(
                intent=Intent.BATTER_VS_BOWLER,
                arguments=QueryArguments(batter="Virat Kohli", bowler="Jasprit Bumrah"),
                confidence=0.96,
            ),
            "MI vs CSK head to head": LLMPlanOutput(
                intent=Intent.TEAM_HEAD_TO_HEAD,
                arguments=QueryArguments(team1="MI", team2="CSK"),
                confidence=0.94,
            ),
            "Show me match 1304112 scorecard": LLMPlanOutput(
                intent=Intent.MATCH_SCORECARD,
                arguments=QueryArguments(match_id=1304112),
                confidence=0.98,
            ),
            "Give me Wankhede statistics": LLMPlanOutput(
                intent=Intent.VENUE_SUMMARY,
                arguments=QueryArguments(venue_name="Wankhede"),
                confidence=0.88,
            ),
            "Show me India team record": LLMPlanOutput(
                intent=Intent.TEAM_RECORD,
                arguments=QueryArguments(team_name="India"),
                confidence=0.93,
            ),
            "How did Kohli perform?": LLMPlanOutput(
                intent=Intent.PLAYER_PROFILE,
                arguments=QueryArguments(player_name="Kohli"),
                confidence=0.60,
                requires_clarification=True,
                clarification_message="Did you want Kohli's overall career stats, recent matches, or batting average?",
            ),
            "Show me the stats": LLMPlanOutput(
                intent=Intent.UNKNOWN,
                arguments=QueryArguments(),
                confidence=0.20,
                requires_clarification=True,
                clarification_message="Please specify a player, team, or match to view statistics for.",
            ),
            "Who will win tomorrow's match?": LLMPlanOutput(
                intent=Intent.UNKNOWN,
                arguments=QueryArguments(),
                confidence=0.99,
                requires_clarification=False,
            ),
        }
        self.provider = MockLLMProvider(response_map=self.response_map)
        self.planner = LLMQueryPlanner(provider=self.provider)

    def test_basic_intent_and_entity_extraction(self):
        plan = self.planner.plan("What is Virat Kohli's batting average?")
        self.assertEqual(plan.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(plan.arguments.player_name, "Virat Kohli")
        self.assertEqual(plan.confidence, 0.95)
        self.assertEqual(plan.source, "llm")
        self.assertFalse(plan.requires_clarification)

    def test_strike_rate_intent(self):
        plan = self.planner.plan("What is Kohli's strike rate?")
        self.assertEqual(plan.intent, Intent.BATTING_STRIKE_RATE)
        self.assertEqual(plan.arguments.player_name, "Kohli")

    def test_top_run_scorers_intent(self):
        plan = self.planner.plan("Who has scored the most runs?")
        self.assertEqual(plan.intent, Intent.TOP_RUN_SCORERS)
        self.assertEqual(plan.arguments.limit, 10)

    def test_top_wicket_takers_intent(self):
        plan = self.planner.plan("Who has taken the most wickets?")
        self.assertEqual(plan.intent, Intent.TOP_WICKET_TAKERS)
        self.assertEqual(plan.arguments.limit, 10)

    def test_batter_vs_bowler_intent(self):
        plan = self.planner.plan("How has Virat Kohli performed against Jasprit Bumrah?")
        self.assertEqual(plan.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan.arguments.batter, "Virat Kohli")
        self.assertEqual(plan.arguments.bowler, "Jasprit Bumrah")

    def test_team_head_to_head_intent(self):
        plan = self.planner.plan("MI vs CSK head to head")
        self.assertEqual(plan.intent, Intent.TEAM_HEAD_TO_HEAD)
        self.assertEqual(plan.arguments.team1, "MI")
        self.assertEqual(plan.arguments.team2, "CSK")

    def test_match_scorecard_intent(self):
        plan = self.planner.plan("Show me match 1304112 scorecard")
        self.assertEqual(plan.intent, Intent.MATCH_SCORECARD)
        self.assertEqual(plan.arguments.match_id, 1304112)

    def test_venue_summary_intent(self):
        plan = self.planner.plan("Give me Wankhede statistics")
        self.assertEqual(plan.intent, Intent.VENUE_SUMMARY)
        self.assertEqual(plan.arguments.venue_name, "Wankhede")

    def test_team_record_intent(self):
        plan = self.planner.plan("Show me India team record")
        self.assertEqual(plan.intent, Intent.TEAM_RECORD)
        self.assertEqual(plan.arguments.team_name, "India")

    def test_ambiguous_queries_require_clarification(self):
        plan1 = self.planner.plan("How did Kohli perform?")
        self.assertTrue(plan1.requires_clarification)
        self.assertIsNotNone(plan1.clarification_message)

        plan2 = self.planner.plan("Show me the stats")
        self.assertTrue(plan2.requires_clarification)
        self.assertEqual(plan2.intent, Intent.UNKNOWN)

    def test_unsupported_questions_return_unknown_intent(self):
        plan = self.planner.plan("Who will win tomorrow's match?")
        self.assertEqual(plan.intent, Intent.UNKNOWN)
        self.assertFalse(plan.requires_clarification)

    def test_question_input_validation(self):
        with self.assertRaises(ValueError):
            self.planner.plan("")

        with self.assertRaises(ValueError):
            self.planner.plan("   ")

        with self.assertRaises(ValueError):
            self.planner.plan(None)  # type: ignore

    def test_invalid_confidence_raises_planning_error(self):
        def invalid_confidence_handler(sys_prompt, user_prompt, model):
            return dict(
                intent=Intent.BATTING_AVERAGE,
                arguments=QueryArguments(player_name="Kohli"),
                confidence=1.5,  # Invalid confidence > 1.0
            )

        provider = MockLLMProvider(custom_handler=invalid_confidence_handler)
        planner = LLMQueryPlanner(provider=provider)

        with self.assertRaises(PlanningError) as ctx:
            planner.plan("What is Kohli's batting average?")
        self.assertIn("Failed to construct valid QueryPlan", str(ctx.exception))

    def test_malformed_llm_payload_raises_planning_error(self):
        def malformed_payload_handler(sys_prompt, user_prompt, model):
            return "not_a_valid_model_or_dict"

        provider = MockLLMProvider(custom_handler=malformed_payload_handler)
        planner = LLMQueryPlanner(provider=provider)

        with self.assertRaises(PlanningError) as ctx:
            planner.plan("What is Kohli's batting average?")
        self.assertIn("Invalid LLM output payload", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
