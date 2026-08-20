"""
Unit and Integration tests for CricGPT Hybrid Query Planner (Phase 3B.3).
"""

import os
import unittest
from unittest.mock import MagicMock

from orchestration.exceptions import (
    PlanningError,
    UnsupportedIntentError,
    ExecutionError,
    FormattingError,
)
from orchestration.executor import CapabilityExecutor
from orchestration.formatter import ResponseFormatter
from orchestration.hybrid_planner import HybridQueryPlanner
from orchestration.intents import Intent
from orchestration.parser import QueryParser
from orchestration.schemas import (
    ExecutionResult,
    QueryArguments,
    QueryPlan,
)
from orchestration.service import OrchestrationService


class TestHybridQueryPlanner(unittest.TestCase):
    """Unit test suite for HybridQueryPlanner."""

    def setUp(self):
        self.mock_det_parser = MagicMock()
        self.mock_llm_planner = MagicMock()
        self.hybrid_planner = HybridQueryPlanner(
            deterministic_parser=self.mock_det_parser,
            llm_planner=self.mock_llm_planner,
        )

    def test_deterministic_success_does_not_call_llm(self):
        """Verify deterministic plan is returned directly and LLM is not called."""
        det_plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser",
            requires_clarification=False,
        )
        self.mock_det_parser.parse.return_value = det_plan

        plan = self.hybrid_planner.plan("What is Virat Kohli's batting average?")

        self.mock_det_parser.parse.assert_called_once_with("What is Virat Kohli's batting average?")
        self.mock_llm_planner.plan.assert_not_called()
        self.assertEqual(plan, det_plan)
        self.assertEqual(plan.source, "rule_based_parser")

    def test_unknown_deterministic_plan_falls_back_to_llm(self):
        """Verify fallback to LLM when deterministic parser produces Intent.UNKNOWN."""
        det_plan = QueryPlan(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            source="rule_based_parser",
            requires_clarification=False,
        )
        llm_plan = QueryPlan(
            intent=Intent.PLAYER_RECENT_MATCHES,
            arguments=QueryArguments(player_name="Virat Kohli", limit=5),
            confidence=0.95,
            source="llm",
            requires_clarification=False,
        )
        self.mock_det_parser.parse.return_value = det_plan
        self.mock_llm_planner.plan.return_value = llm_plan

        plan = self.hybrid_planner.plan("Show Kohli's recent form in last 5 games")

        self.mock_det_parser.parse.assert_called_once_with("Show Kohli's recent form in last 5 games")
        self.mock_llm_planner.plan.assert_called_once_with("Show Kohli's recent form in last 5 games")
        self.assertEqual(plan, llm_plan)
        self.assertEqual(plan.source, "llm")

    def test_llm_plan_is_returned_correctly(self):
        """Verify LLM plan attributes (intent, arguments, confidence) are returned accurately."""
        self.mock_det_parser.parse.return_value = QueryPlan(
            intent=Intent.UNKNOWN, confidence=0.0, source="rule_based_parser"
        )
        expected_llm_plan = QueryPlan(
            intent=Intent.BOWLING_ECONOMY,
            arguments=QueryArguments(player_name="Jasprit Bumrah"),
            confidence=0.90,
            source="llm",
        )
        self.mock_llm_planner.plan.return_value = expected_llm_plan

        plan = self.hybrid_planner.plan("What is Bumrah's economy rate?")

        self.assertEqual(plan.intent, Intent.BOWLING_ECONOMY)
        self.assertEqual(plan.arguments.player_name, "Jasprit Bumrah")
        self.assertEqual(plan.confidence, 0.90)
        self.assertEqual(plan.source, "llm")

    def test_deterministic_plan_preserves_source(self):
        """Verify source='rule_based_parser' is preserved without mutation."""
        det_plan = QueryPlan(
            intent=Intent.TEAM_HEAD_TO_HEAD,
            arguments=QueryArguments(team1="MI", team2="CSK"),
            confidence=0.95,
            source="rule_based_parser",
        )
        self.mock_det_parser.parse.return_value = det_plan

        plan = self.hybrid_planner.plan("MI vs CSK head to head")

        self.assertEqual(plan.source, "rule_based_parser")

    def test_llm_plan_preserves_source(self):
        """Verify source='llm' is preserved without mutation."""
        self.mock_det_parser.parse.return_value = QueryPlan(
            intent=Intent.UNKNOWN, confidence=0.0, source="rule_based_parser"
        )
        llm_plan = QueryPlan(
            intent=Intent.BATTER_VS_BOWLER,
            arguments=QueryArguments(batter="Virat Kohli", bowler="Jasprit Bumrah"),
            confidence=0.92,
            source="llm",
        )
        self.mock_llm_planner.plan.return_value = llm_plan

        plan = self.hybrid_planner.plan("Kohli vs Bumrah stats")

        self.assertEqual(plan.source, "llm")

    def test_deterministic_clarification_is_handled_correctly(self):
        """Verify deterministic clarification request is returned directly and LLM is NOT called."""
        clarification_plan = QueryPlan(
            intent=Intent.UNKNOWN,
            arguments=QueryArguments(player_name="Kohli"),
            confidence=0.4,
            source="rule_based_parser",
            requires_clarification=True,
            clarification_message="Could you specify what performance details you want for Kohli?",
        )
        self.mock_det_parser.parse.return_value = clarification_plan

        plan = self.hybrid_planner.plan("How did Kohli perform?")

        self.mock_llm_planner.plan.assert_not_called()
        self.assertTrue(plan.requires_clarification)
        self.assertEqual(plan.clarification_message, "Could you specify what performance details you want for Kohli?")
        self.assertEqual(plan.source, "rule_based_parser")

    def test_ambiguous_query_is_not_silently_resolved(self):
        """Verify ambiguous queries preserve clarification requirements without LLM intervention."""
        ambiguous_plan = QueryPlan(
            intent=Intent.UNKNOWN,
            arguments=QueryArguments(),
            confidence=0.4,
            source="rule_based_parser",
            requires_clarification=True,
            clarification_message="Multiple players matched 'Kohli'. Please specify full name.",
        )
        self.mock_det_parser.parse.return_value = ambiguous_plan

        plan = self.hybrid_planner.plan("Kohli vs Bumrah")

        self.mock_llm_planner.plan.assert_not_called()
        self.assertTrue(plan.requires_clarification)
        self.assertIsNotNone(plan.clarification_message)
        assert plan.clarification_message is not None
        self.assertIn("Multiple players matched", plan.clarification_message)

    def test_llm_failure_becomes_clean_PlanningError(self):
        """Verify that an exception in LLM planning propagates as PlanningError."""
        self.mock_det_parser.parse.return_value = QueryPlan(
            intent=Intent.UNKNOWN, confidence=0.0, source="rule_based_parser"
        )
        self.mock_llm_planner.plan.side_effect = PlanningError("LLM API network timeout")

        with self.assertRaises(PlanningError) as ctx:
            self.hybrid_planner.plan("Unrecognized complex query")

        self.assertIn("LLM API network timeout", str(ctx.exception))

    def test_missing_llm_configuration_does_not_break_deterministic_queries(self):
        """Verify deterministic queries work cleanly even when no LLM API key is present in env."""
        old_key = os.environ.pop("CRICGPT_LLM_API_KEY", None)
        try:
            planner = HybridQueryPlanner()
            plan = planner.plan("What is Virat Kohli's batting average?")
            self.assertEqual(plan.intent, Intent.BATTING_AVERAGE)
            self.assertEqual(plan.arguments.player_name, "Virat Kohli")
            self.assertEqual(plan.source, "rule_based_parser")
        finally:
            if old_key is not None:
                os.environ["CRICGPT_LLM_API_KEY"] = old_key

    def test_invalid_question_is_rejected(self):
        """Verify empty or whitespace-only questions raise PlanningError."""
        with self.assertRaises(PlanningError):
            self.hybrid_planner.plan("")

        with self.assertRaises(PlanningError):
            self.hybrid_planner.plan("   ")

    def test_dependency_injection_works(self):
        """Verify injected dependencies are properly stored and accessible via properties."""
        p_det = MagicMock()
        p_llm = MagicMock()
        hp = HybridQueryPlanner(deterministic_parser=p_det, llm_planner=p_llm)
        self.assertIs(hp.deterministic_parser, p_det)
        self.assertIs(hp.llm_planner, p_llm)

    def test_existing_query_parser_behavior_remains_unchanged(self):
        """Verify standard QueryParser functionality is unchanged."""
        parser = QueryParser()
        plan = parser.parse("MI vs CSK head to head")
        self.assertEqual(plan.intent, Intent.TEAM_HEAD_TO_HEAD)
        self.assertEqual(plan.arguments.team1, "MI")
        self.assertEqual(plan.arguments.team2, "CSK")
        self.assertEqual(plan.source, "rule_based_parser")

    def test_parse_alias(self):
        """Verify parse() is an exact alias for plan()."""
        det_plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser",
        )
        self.mock_det_parser.parse.return_value = det_plan

        plan = self.hybrid_planner.parse("What is Virat Kohli's batting average?")
        self.assertEqual(plan, det_plan)


class TestOrchestrationServiceHybridIntegration(unittest.TestCase):
    """Integration test suite for OrchestrationService with HybridQueryPlanner."""

    def test_deterministic_query_routes_through_deterministic_parser(self):
        mock_det = MagicMock()
        mock_llm = MagicMock()
        mock_executor = MagicMock()
        mock_formatter = MagicMock()

        det_plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser",
        )
        mock_det.parse.return_value = det_plan
        mock_executor.execute.return_value = ExecutionResult(
            success=True, intent=Intent.BATTING_AVERAGE, result={"batting_average": 40.81}
        )
        mock_formatter.format.return_value = "Virat Kohli's batting average is 40.81."

        hybrid = HybridQueryPlanner(deterministic_parser=mock_det, llm_planner=mock_llm)
        service = OrchestrationService(planner=hybrid, executor=mock_executor, formatter=mock_formatter)

        resp = service.ask("What is Virat Kohli's batting average?")

        self.assertTrue(resp.success)
        mock_det.parse.assert_called_once()
        mock_llm.plan.assert_not_called()
        mock_executor.execute.assert_called_once_with(det_plan)
        mock_formatter.format.assert_called_once()

    def test_unsupported_query_reaches_llm_planner(self):
        mock_det = MagicMock()
        mock_llm = MagicMock()
        mock_executor = MagicMock()
        mock_formatter = MagicMock()

        mock_det.parse.return_value = QueryPlan(
            intent=Intent.UNKNOWN, confidence=0.0, source="rule_based_parser"
        )
        llm_plan = QueryPlan(
            intent=Intent.PLAYER_RECENT_MATCHES,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.90,
            source="llm",
        )
        mock_llm.plan.return_value = llm_plan
        mock_executor.execute.return_value = ExecutionResult(
            success=True, intent=Intent.PLAYER_RECENT_MATCHES, result=[]
        )
        mock_formatter.format.return_value = "Recent matches for Virat Kohli."

        hybrid = HybridQueryPlanner(deterministic_parser=mock_det, llm_planner=mock_llm)
        service = OrchestrationService(planner=hybrid, executor=mock_executor, formatter=mock_formatter)

        resp = service.ask("Describe Virat Kohli's recent performance")

        self.assertTrue(resp.success)
        mock_det.parse.assert_called_once()
        mock_llm.plan.assert_called_once()
        mock_executor.execute.assert_called_once_with(llm_plan)
        mock_formatter.format.assert_called_once()

    def test_planner_contains_no_db_or_analytics_calls(self):
        """Verify planner operates strictly in isolation without analytics or database calls."""
        mock_det = MagicMock()
        mock_llm = MagicMock()
        hybrid = HybridQueryPlanner(deterministic_parser=mock_det, llm_planner=mock_llm)

        # Ensure no database connection or analytics import is touched by hybrid planner
        self.assertFalse(hasattr(hybrid, "db"))
        self.assertFalse(hasattr(hybrid, "sql"))
        self.assertFalse(hasattr(hybrid, "execute_query"))


if __name__ == "__main__":
    unittest.main()
