"""
Unit tests for orchestration Intent enum.
"""

import unittest
from orchestration import Intent


class TestIntents(unittest.TestCase):
    """Test cases for Intent enum values and structure."""

    def test_intent_members_count(self):
        """Verify total count of supported intents."""
        self.assertEqual(len(Intent), 20)

    def test_intent_values(self):
        """Verify expected intent string values."""
        expected_members = [
            "PLAYER_SEARCH",
            "PLAYER_PROFILE",
            "PLAYER_CAREER",
            "PLAYER_RECENT_MATCHES",
            "PLAYER_MATCH_HISTORY",
            "TOP_RUN_SCORERS",
            "HIGHEST_INDIVIDUAL_SCORES",
            "BATTING_AVERAGE",
            "BATTING_STRIKE_RATE",
            "BOUNDARY_PERCENTAGE",
            "TOP_WICKET_TAKERS",
            "BEST_BOWLING_FIGURES",
            "BOWLING_ECONOMY",
            "BATTER_VS_BOWLER",
            "TEAM_RECORD",
            "TEAM_HEAD_TO_HEAD",
            "VENUE_SUMMARY",
            "MATCH_SUMMARY",
            "MATCH_SCORECARD",
            "UNKNOWN",
        ]
        for name in expected_members:
            self.assertTrue(hasattr(Intent, name))
            self.assertEqual(getattr(Intent, name).value, name)

    def test_intent_string_comparison(self):
        """Verify enum member value access and comparison."""
        self.assertEqual(Intent.BATTER_VS_BOWLER.value, "BATTER_VS_BOWLER")
        self.assertEqual(Intent.UNKNOWN.value, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
