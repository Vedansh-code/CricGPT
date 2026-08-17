"""
Unit tests for CricGPT Capability Executor (Phase 3A.4).
"""

import unittest
from unittest.mock import MagicMock
from orchestration.intents import Intent
from orchestration.schemas import QueryPlan, QueryArguments
from orchestration.exceptions import (
    UnsupportedIntentError,
    ClarificationRequired,
    ExecutionError,
)
from orchestration.registry import Capability, CapabilityRegistry
from orchestration.executor import CapabilityExecutor
from analytics.utils import PlayerNotFoundError


class TestCapabilityExecutor(unittest.TestCase):
    """Test suite for CapabilityExecutor implementation."""

    def setUp(self):
        self.executor = CapabilityExecutor()

    # 1. Successful PLAYER_PROFILE execution
    def test_execute_player_profile(self):
        plan = QueryPlan(
            intent=Intent.PLAYER_PROFILE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.PLAYER_PROFILE)
        self.assertIsNotNone(res.result)
        self.assertEqual(res.metadata["capability"], "Get Player Profile")
        self.assertEqual(res.metadata["source"], "analytics_sdk")

    # 2. Successful BATTING_AVERAGE execution
    def test_execute_batting_average(self):
        plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.BATTING_AVERAGE)
        self.assertIn("batting_average", res.result)

    # 3. Successful PLAYER_RECENT_MATCHES with limit
    def test_execute_player_recent_matches_with_limit(self):
        plan = QueryPlan(
            intent=Intent.PLAYER_RECENT_MATCHES,
            arguments=QueryArguments(player_name="Virat Kohli", limit=5),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.PLAYER_RECENT_MATCHES)
        self.assertLessEqual(len(res.result), 5)

    # 4. Successful PLAYER_RECENT_MATCHES without limit
    def test_execute_player_recent_matches_without_limit(self):
        plan = QueryPlan(
            intent=Intent.PLAYER_RECENT_MATCHES,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.90,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.PLAYER_RECENT_MATCHES)
        self.assertIsInstance(res.result, list)

    # 5. Successful BATTER_VS_BOWLER execution
    def test_execute_batter_vs_bowler(self):
        plan = QueryPlan(
            intent=Intent.BATTER_VS_BOWLER,
            arguments=QueryArguments(batter="Virat Kohli", bowler="Jasprit Bumrah"),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.BATTER_VS_BOWLER)
        self.assertIn("strike_rate", res.result)

    # 6. Successful TEAM_HEAD_TO_HEAD execution
    def test_execute_team_head_to_head(self):
        plan = QueryPlan(
            intent=Intent.TEAM_HEAD_TO_HEAD,
            arguments=QueryArguments(team1="MI", team2="CSK"),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.TEAM_HEAD_TO_HEAD)
        self.assertIn("matches_played", res.result)

    # 7. Successful MATCH_SUMMARY execution
    def test_execute_match_summary(self):
        plan = QueryPlan(
            intent=Intent.MATCH_SUMMARY,
            arguments=QueryArguments(match_id=1304112),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = self.executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.intent, Intent.MATCH_SUMMARY)
        self.assertEqual(res.result["match_id"], 1304112)

    # 8. Missing required argument
    def test_execute_missing_required_argument(self):
        plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(), # player_name is None
            confidence=0.4,
            source="rule_based_parser"
        )
        with self.assertRaises(ExecutionError):
            self.executor.execute(plan)

    # 9. UNKNOWN intent
    def test_execute_unknown_intent(self):
        plan = QueryPlan(
            intent=Intent.UNKNOWN,
            arguments=QueryArguments(),
            confidence=0.0,
            source="rule_based_parser"
        )
        with self.assertRaises(UnsupportedIntentError):
            self.executor.execute(plan)

    # 10. Unsupported/unregistered intent
    def test_execute_unregistered_intent(self):
        empty_registry = CapabilityRegistry()
        custom_executor = CapabilityExecutor(registry=empty_registry)
        plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser"
        )
        with self.assertRaises(UnsupportedIntentError):
            custom_executor.execute(plan)

    # 11. ClarificationRequired plan
    def test_execute_requires_clarification(self):
        plan = QueryPlan(
            intent=Intent.UNKNOWN,
            arguments=QueryArguments(),
            confidence=0.0,
            source="rule_based_parser",
            requires_clarification=True,
            clarification_message="Please specify a player or team."
        )
        with self.assertRaises(ClarificationRequired) as ctx:
            self.executor.execute(plan)
        self.assertIn("Please specify a player or team.", str(ctx.exception))

    # 12. SDK handler domain failure preservation
    def test_execute_sdk_domain_exception_preserved(self):
        plan = QueryPlan(
            intent=Intent.PLAYER_PROFILE,
            arguments=QueryArguments(player_name="NonExistentPlayerXYZ123"),
            confidence=0.95,
            source="rule_based_parser"
        )
        with self.assertRaises(PlayerNotFoundError):
            self.executor.execute(plan)

    # 13. Unexpected handler exception wrapped as ExecutionError
    def test_execute_unexpected_exception_wrapped(self):
        mock_handler = MagicMock(side_effect=AttributeError("Internal unexpected error"))
        custom_registry = CapabilityRegistry()
        custom_registry.register(Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Mock Batting Average",
            description="Mock capability",
            handler=mock_handler,
            required_arguments=["player_name"]
        ))
        custom_executor = CapabilityExecutor(registry=custom_registry)

        plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser"
        )
        with self.assertRaises(ExecutionError) as ctx:
            custom_executor.execute(plan)
        self.assertIn("Execution failed for capability", str(ctx.exception))

    # 14. Irrelevant QueryArguments are not passed to handlers
    def test_irrelevant_arguments_not_passed(self):
        mock_handler = MagicMock(return_value={"mock": "data"})
        custom_registry = CapabilityRegistry()
        custom_registry.register(Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Mock Batting Average",
            description="Mock capability",
            handler=mock_handler,
            required_arguments=["player_name"],
            optional_arguments=[]
        ))
        custom_executor = CapabilityExecutor(registry=custom_registry)

        # Plan contains player_name, but also irrelevant arguments like match_id and limit
        plan = QueryPlan(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli", match_id=1304112, limit=10),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = custom_executor.execute(plan)
        self.assertTrue(res.success)
        # Mock handler should only receive player_name
        mock_handler.assert_called_once_with(player_name="Virat Kohli")

    # 15. Custom registry dependency injection
    def test_custom_registry_dependency_injection(self):
        mock_handler = MagicMock(return_value={"result": "custom"})
        custom_registry = CapabilityRegistry()
        custom_registry.register(Capability(
            intent=Intent.PLAYER_PROFILE,
            name="Custom Profile",
            description="Custom description",
            handler=mock_handler,
            required_arguments=["player_name"]
        ))
        custom_executor = CapabilityExecutor(registry=custom_registry)

        plan = QueryPlan(
            intent=Intent.PLAYER_PROFILE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
            source="rule_based_parser"
        )
        res = custom_executor.execute(plan)
        self.assertTrue(res.success)
        self.assertEqual(res.result, {"result": "custom"})
        self.assertEqual(res.metadata["capability"], "Custom Profile")


if __name__ == "__main__":
    unittest.main()
