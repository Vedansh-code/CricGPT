import unittest
import os
import sys

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.bowling import (
    top_wicket_takers,
    economy_rate,
    best_bowling_figures,
)


class TestBowlingAnalytics(unittest.TestCase):
    
    def test_top_wicket_takers(self):
        limit = 5
        top = top_wicket_takers(limit)
        self.assertEqual(len(top), limit)
        self.assertGreaterEqual(top[0]["wickets"], top[1]["wickets"])
        self.assertIn("player_name", top[0])
        self.assertIn("economy_rate", top[0])
        
    def test_economy_rate(self):
        # Jasprit Bumrah -> "JJ Bumrah"
        econ_info = economy_rate("Jasprit Bumrah")
        self.assertEqual(econ_info["player_name"], "JJ Bumrah")
        self.assertGreater(econ_info["balls_bowled"], 500)
        self.assertGreater(econ_info["economy_rate"], 4.0)
        self.assertLess(econ_info["economy_rate"], 10.0)
        
    def test_best_bowling_figures(self):
        limit = 3
        best = best_bowling_figures(limit)
        self.assertEqual(len(best), limit)
        self.assertGreaterEqual(best[0]["wickets"], best[1]["wickets"])
        self.assertIn("bowling_team", best[0])
        self.assertIn("batting_team", best[0])
        
        # Check that overs is correctly formatted using format_overs()
        self.assertIsInstance(best[0]["overs"], str)
        # Check that it contains a dot and split parts are digits
        parts = best[0]["overs"].split(".")
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())
        self.assertLess(int(parts[1]), 6)  # balls must be less than 6 in cricket notation


if __name__ == "__main__":
    unittest.main()
