"""
Unit and Integration tests for CricGPT Orchestration Service (Phase 3A.6).
"""

import unittest
from unittest.mock import MagicMock
from orchestration.intents import Intent
from orchestration.schemas import QueryPlan, QueryArguments, ExecutionResult
from orchestration.exceptions import (
    PlanningError,
    UnsupportedIntentError,
    ExecutionError,
    FormattingError,
)
from orchestration.service import OrchestrationService, get_default_service
from analytics.utils import PlayerNotFoundError


class TestOrchestrationServiceUnit(unittest.TestCase):
    """Unit test suite for OrchestrationService with mocks."""

    def test_successful_end_to_end_orchestration_mocked(self):
        mock_parser = MagicMock()
        mock_executor = MagicMock()
        mock_formatter = MagicMock()

        plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser"
        )
        mock_parser.parse.return_value = plan

        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTING_AVERAGE,
            result={"batting_average": 40.81},
            metadata={"capability": "Batting Average"}
        )
        mock_executor.execute.return_value = exec_res
        mock_formatter.format.return_value = "Virat Kohli's batting average is 40.81."

        service = OrchestrationService(
            parser=mock_parser,
            executor=mock_executor,
            formatter=mock_formatter
        )

        response = service.ask("What is Virat Kohli's batting average?")

        mock_parser.parse.assert_called_once_with("What is Virat Kohli's batting average?")
        mock_executor.execute.assert_called_once_with(plan)
        mock_formatter.format.assert_called_once_with(exec_res)

        self.assertTrue(response.success)
        self.assertEqual(response.question, "What is Virat Kohli's batting average?")
        self.assertEqual(response.plan, plan)
        self.assertEqual(response.result, exec_res)
        self.assertEqual(response.answer, "Virat Kohli's batting average is 40.81.")

    def test_clarification_flow_bypasses_executor_and_formatter(self):
        mock_parser = MagicMock()
        mock_executor = MagicMock()
        mock_formatter = MagicMock()

        plan = QueryPlan(
            intent=Intent.UNKNOWN,
            arguments=QueryArguments(player_name="Kohli"),
            confidence=0.4,
            source="rule_based_parser",
            requires_clarification=True,
            clarification_message="Could you specify what performance details you want for Kohli?"
        )
        mock_parser.parse.return_value = plan

        service = OrchestrationService(
            parser=mock_parser,
            executor=mock_executor,
            formatter=mock_formatter
        )

        response = service.ask("How did Kohli perform?")

        mock_parser.parse.assert_called_once_with("How did Kohli perform?")
        mock_executor.execute.assert_not_called()
        mock_formatter.format.assert_not_called()

        self.assertFalse(response.success)
        self.assertEqual(response.plan, plan)
        self.assertIsNone(response.result)
        self.assertEqual(response.answer, "Could you specify what performance details you want for Kohli?")

    def test_unknown_question_raises_unsupported_intent_error(self):
        service = OrchestrationService()
        with self.assertRaises(UnsupportedIntentError):
            service.ask("Who will win tomorrow's match?")

    def test_invalid_empty_and_whitespace_question(self):
        service = OrchestrationService()
        with self.assertRaises(PlanningError):
            service.ask("")

        with self.assertRaises(PlanningError):
            service.ask("   ")

    def test_parser_exception_propagates(self):
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = PlanningError("Parser failure")
        service = OrchestrationService(parser=mock_parser)

        with self.assertRaises(PlanningError):
            service.ask("What is Kohli's batting average?")

    def test_executor_exception_propagates(self):
        mock_parser = MagicMock()
        mock_executor = MagicMock()
        plan = QueryPlan(intent=Intent.BATTING_AVERAGE, confidence=0.95, source="test")
        mock_parser.parse.return_value = plan
        mock_executor.execute.side_effect = ExecutionError("Execution failed")

        service = OrchestrationService(parser=mock_parser, executor=mock_executor)

        with self.assertRaises(ExecutionError):
            service.ask("What is Kohli's batting average?")

    def test_formatter_exception_propagates(self):
        mock_parser = MagicMock()
        mock_executor = MagicMock()
        mock_formatter = MagicMock()

        plan = QueryPlan(intent=Intent.BATTING_AVERAGE, confidence=0.95, source="test")
        mock_parser.parse.return_value = plan
        mock_executor.execute.return_value = ExecutionResult(success=True, intent=Intent.BATTING_AVERAGE)
        mock_formatter.format.side_effect = FormattingError("Format error")

        service = OrchestrationService(parser=mock_parser, executor=mock_executor, formatter=mock_formatter)

        with self.assertRaises(FormattingError):
            service.ask("What is Kohli's batting average?")

    def test_sdk_domain_exception_propagates(self):
        service = OrchestrationService()
        with self.assertRaises(PlayerNotFoundError):
            service.ask("What is NonExistentPlayerXYZ123's batting average?")

    def test_dependency_injection(self):
        p, e, f = MagicMock(), MagicMock(), MagicMock()
        service = OrchestrationService(parser=p, executor=e, formatter=f)
        self.assertIs(service.parser, p)
        self.assertIs(service.executor, e)
        self.assertIs(service.formatter, f)

    def test_default_service_factory(self):
        service = get_default_service()
        self.assertIsInstance(service, OrchestrationService)
        self.assertIsNotNone(service.parser)
        self.assertIsNotNone(service.executor)
        self.assertIsNotNone(service.formatter)


class TestOrchestrationServiceIntegration(unittest.TestCase):
    """Integration test suite using real components and database."""

    def setUp(self):
        self.service = OrchestrationService()

    def test_real_end_to_end_batting_average(self):
        response = self.service.ask("What is Virat Kohli's batting average?")
        self.assertTrue(response.success)
        self.assertIsNotNone(response.plan)
        self.assertEqual(response.plan.intent, Intent.BATTING_AVERAGE)
        self.assertIsNotNone(response.result)
        self.assertTrue(response.result.success)
        self.assertIsNotNone(response.answer)
        self.assertIn("Kohli", response.answer)
        self.assertIn("40.81", response.answer)


    def test_real_end_to_end_scorecard(self):
        response = self.service.ask("Show me match 1304112 scorecard")
        self.assertTrue(response.success)
        self.assertIsNotNone(response.plan)
        self.assertEqual(response.plan.intent, Intent.MATCH_SCORECARD)
        self.assertIsNotNone(response.result)
        self.assertTrue(response.result.success)
        self.assertIsNotNone(response.answer)
        self.assertIn("Match Scorecard (Match 1304112)", response.answer)

    def test_real_end_to_end_head_to_head(self):
        response = self.service.ask("MI vs CSK head to head")
        self.assertTrue(response.success)
        self.assertIsNotNone(response.plan)
        self.assertEqual(response.plan.intent, Intent.TEAM_HEAD_TO_HEAD)
        self.assertIsNotNone(response.result)
        self.assertTrue(response.result.success)
        self.assertIsNotNone(response.answer)
        self.assertIn("Mumbai Indians vs Chennai Super Kings", response.answer)


if __name__ == "__main__":
    unittest.main()
