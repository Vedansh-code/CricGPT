"""
Unit tests for orchestration Pydantic v2 schemas.
"""

import unittest
from pydantic import ValidationError

from orchestration import (
    Intent,
    QuestionRequest,
    QueryArguments,
    QueryPlan,
    ExecutionResult,
    OrchestrationResponse,
)


class TestSchemas(unittest.TestCase):
    """Test cases for orchestration Pydantic v2 models and field validations."""

    def test_question_request_valid(self):
        """Test valid question requests and automatic whitespace stripping."""
        req = QuestionRequest(question="  Who has the highest batting average?  ")
        self.assertEqual(req.question, "Who has the highest batting average?")

    def test_question_request_empty_rejection(self):
        """Test empty string and whitespace-only question rejection."""
        with self.assertRaises(ValidationError):
            QuestionRequest(question="")
        with self.assertRaises(ValidationError):
            QuestionRequest(question="   \n\t  ")

    def test_query_arguments_defaults(self):
        """Test default instantiation of QueryArguments."""
        args = QueryArguments()
        self.assertIsNone(args.player_name)
        self.assertIsNone(args.batter)
        self.assertIsNone(args.bowler)
        self.assertIsNone(args.team_name)
        self.assertIsNone(args.team1)
        self.assertIsNone(args.team2)
        self.assertIsNone(args.venue_name)
        self.assertIsNone(args.match_id)
        self.assertIsNone(args.limit)

    def test_query_arguments_valid(self):
        """Test QueryArguments with entity parameters."""
        args = QueryArguments(
            batter="Virat Kohli",
            bowler="Jasprit Bumrah",
            limit=10,
            match_id=12345,
        )
        self.assertEqual(args.batter, "Virat Kohli")
        self.assertEqual(args.bowler, "Jasprit Bumrah")
        self.assertEqual(args.limit, 10)
        self.assertEqual(args.match_id, 12345)

    def test_query_arguments_validation_failure(self):
        """Test match_id and limit positive number constraints."""
        with self.assertRaises(ValidationError):
            QueryArguments(match_id=0)
        with self.assertRaises(ValidationError):
            QueryArguments(match_id=-5)
        with self.assertRaises(ValidationError):
            QueryArguments(limit=0)
        with self.assertRaises(ValidationError):
            QueryArguments(limit=-10)

    def test_query_plan_valid_and_defaults(self):
        """Test QueryPlan instantiation and default values."""
        plan = QueryPlan(
            intent=Intent.BATTER_VS_BOWLER,
            arguments=QueryArguments(batter="Virat Kohli", bowler="Jasprit Bumrah"),
            confidence=0.98,
            source="rule_based",
        )
        self.assertEqual(plan.version, "1.0")
        self.assertEqual(plan.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan.confidence, 0.98)
        self.assertEqual(plan.source, "rule_based")
        self.assertFalse(plan.requires_clarification)
        self.assertIsNone(plan.clarification_message)

    def test_query_plan_immutability(self):
        """Test frozen model immutability enforcement."""
        plan = QueryPlan(
            intent=Intent.TOP_RUN_SCORERS,
            confidence=0.95,
            source="rule_based",
        )
        with self.assertRaises(ValidationError):
            plan.intent = Intent.UNKNOWN

    def test_query_plan_confidence_validation(self):
        """Test confidence range validation (0.0 to 1.0)."""
        # Lower bound valid
        p_min = QueryPlan(intent=Intent.UNKNOWN, confidence=0.0, source="rule_based")
        self.assertEqual(p_min.confidence, 0.0)

        # Upper bound valid
        p_max = QueryPlan(intent=Intent.UNKNOWN, confidence=1.0, source="rule_based")
        self.assertEqual(p_max.confidence, 1.0)

        # Invalid bounds
        with self.assertRaises(ValidationError):
            QueryPlan(intent=Intent.UNKNOWN, confidence=-0.1, source="rule_based")
        with self.assertRaises(ValidationError):
            QueryPlan(intent=Intent.UNKNOWN, confidence=1.05, source="rule_based")

    def test_query_plan_source_validation(self):
        """Test source non-empty validation."""
        with self.assertRaises(ValidationError):
            QueryPlan(intent=Intent.UNKNOWN, confidence=0.5, source="")
        with self.assertRaises(ValidationError):
            QueryPlan(intent=Intent.UNKNOWN, confidence=0.5, source="   ")

    def test_execution_result(self):
        """Test ExecutionResult model behavior."""
        res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_PROFILE,
            result={"player_id": "P123", "name": "MS Dhoni"},
        )
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.PLAYER_PROFILE)
        self.assertEqual(res.result["name"], "MS Dhoni")
        self.assertEqual(res.metadata, {})

    def test_orchestration_response(self):
        """Test OrchestrationResponse nested structure."""
        plan = QueryPlan(
            intent=Intent.VENUE_SUMMARY,
            confidence=0.9,
            source="rule_based",
        )
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.VENUE_SUMMARY,
            result={"venue": "Wankhede Stadium"},
        )
        response = OrchestrationResponse(
            success=True,
            question="What is the summary for Wankhede Stadium?",
            plan=plan,
            result=exec_res,
            answer="Wankhede Stadium is located in Mumbai.",
        )
        self.assertTrue(response.success)
        self.assertIsNotNone(response.plan)
        self.assertEqual(response.plan.intent, Intent.VENUE_SUMMARY)
        self.assertIsNotNone(response.result)
        self.assertTrue(response.result.success)
        self.assertIn("Wankhede", response.answer)


if __name__ == "__main__":
    unittest.main()
