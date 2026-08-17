"""
Unit tests for CricGPT Capability Registry (Phase 3A.3).
"""

import unittest
from unittest.mock import MagicMock
from orchestration.intents import Intent
from orchestration.exceptions import UnsupportedIntentError
from orchestration.registry import Capability, CapabilityRegistry, get_default_registry
import analytics


class TestCapabilityRegistry(unittest.TestCase):
    """Test suite for Capability and CapabilityRegistry implementations."""

    def test_register_and_retrieve_capability(self):
        registry = CapabilityRegistry()
        mock_handler = MagicMock()
        cap = Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Batting Average",
            description="Get batting average statistics for a player.",
            handler=mock_handler,
            required_arguments=["player_name"]
        )
        registry.register(cap)

        self.assertTrue(registry.has(Intent.BATTING_AVERAGE))
        self.assertEqual(registry.count(), 1)
        retrieved = registry.get(Intent.BATTING_AVERAGE)
        self.assertEqual(retrieved.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(retrieved.name, "Batting Average")
        self.assertEqual(retrieved.handler, mock_handler)
        self.assertEqual(retrieved.required_arguments, ["player_name"])

    def test_has_intent(self):
        registry = CapabilityRegistry()
        self.assertFalse(registry.has(Intent.BATTING_AVERAGE))
        cap = Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Batting Average",
            description="Test description",
            handler=lambda x: x
        )
        registry.register(cap)
        self.assertTrue(registry.has(Intent.BATTING_AVERAGE))
        self.assertFalse(registry.has(Intent.BOWLING_ECONOMY))

    def test_count(self):
        registry = CapabilityRegistry()
        self.assertEqual(registry.count(), 0)
        registry.register(Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Batting Average",
            description="Test description",
            handler=lambda x: x
        ))
        self.assertEqual(registry.count(), 1)

    def test_duplicate_intent_registration(self):
        registry = CapabilityRegistry()
        cap = Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Batting Average",
            description="Test description",
            handler=lambda x: x
        )
        registry.register(cap)
        with self.assertRaises(ValueError):
            registry.register(cap)

    def test_cannot_register_unknown_intent(self):
        registry = CapabilityRegistry()
        with self.assertRaises(ValueError):
            Capability(
                intent=Intent.UNKNOWN,
                name="Unknown Capability",
                description="Test description",
                handler=lambda x: x
            )

        # Direct register call check
        dummy_cap = MagicMock()
        dummy_cap.intent = Intent.UNKNOWN
        with self.assertRaises(ValueError):
            registry.register(dummy_cap)

    def test_unsupported_intent_raises_error(self):
        registry = CapabilityRegistry()
        with self.assertRaises(UnsupportedIntentError):
            registry.get(Intent.BATTING_AVERAGE)

    def test_all_returns_all_capabilities(self):
        registry = CapabilityRegistry()
        cap1 = Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Batting Average",
            description="Test desc 1",
            handler=lambda x: x
        )
        cap2 = Capability(
            intent=Intent.BOWLING_ECONOMY,
            name="Bowling Economy",
            description="Test desc 2",
            handler=lambda x: x
        )
        registry.register(cap1)
        registry.register(cap2)

        caps = registry.all()
        self.assertEqual(len(caps), 2)
        self.assertIn(cap1, caps)
        self.assertIn(cap2, caps)

    def test_default_registry_count_and_intents(self):
        registry = get_default_registry()
        self.assertEqual(registry.count(), 19)
        self.assertFalse(registry.has(Intent.UNKNOWN))

        executable_intents = [intent for intent in Intent if intent != Intent.UNKNOWN]
        self.assertEqual(len(executable_intents), 19)

        for intent in executable_intents:
            self.assertTrue(registry.has(intent), f"Missing intent in default registry: {intent}")

    def test_default_capability_fields(self):
        registry = get_default_registry()
        for cap in registry.all():
            self.assertIsInstance(cap.intent, Intent)
            self.assertNotEqual(cap.intent, Intent.UNKNOWN)
            self.assertTrue(bool(cap.name and cap.name.strip()))
            self.assertTrue(bool(cap.description and cap.description.strip()))
            self.assertTrue(callable(cap.handler))

    def test_representative_sdk_mappings(self):
        registry = get_default_registry()

        # BATTING_AVERAGE -> analytics.batting_average
        bat_avg_cap = registry.get(Intent.BATTING_AVERAGE)
        self.assertEqual(bat_avg_cap.handler, analytics.batting_average)
        self.assertEqual(bat_avg_cap.required_arguments, ["player_name"])

        # PLAYER_CAREER -> analytics.get_player_career
        career_cap = registry.get(Intent.PLAYER_CAREER)
        self.assertEqual(career_cap.handler, analytics.get_player_career)
        self.assertEqual(career_cap.required_arguments, ["player_name"])

        # BATTER_VS_BOWLER -> analytics.get_batter_vs_bowler
        matchup_cap = registry.get(Intent.BATTER_VS_BOWLER)
        self.assertEqual(matchup_cap.handler, analytics.get_batter_vs_bowler)
        self.assertEqual(matchup_cap.required_arguments, ["batter", "bowler"])

        # MATCH_SCORECARD -> analytics.get_scorecard
        scorecard_cap = registry.get(Intent.MATCH_SCORECARD)
        self.assertEqual(scorecard_cap.handler, analytics.get_scorecard)
        self.assertEqual(scorecard_cap.required_arguments, ["match_id"])

    def test_no_execution_during_lookup(self):
        mock_handler = MagicMock()
        registry = CapabilityRegistry()
        cap = Capability(
            intent=Intent.BATTING_AVERAGE,
            name="Batting Average",
            description="Test desc",
            handler=mock_handler
        )
        registry.register(cap)

        retrieved = registry.get(Intent.BATTING_AVERAGE)
        self.assertEqual(retrieved.handler, mock_handler)
        mock_handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
