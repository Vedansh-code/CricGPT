import unittest
import os
import sys

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.batting import (
    top_run_scorers,
    highest_individual_scores,
    batting_average,
    strike_rate,
    boundary_percentage,
)


class TestBattingAnalytics(unittest.TestCase):
    
    def test_top_run_scorers(self):
        limit = 5
        top = top_run_scorers(limit)
        self.assertEqual(len(top), limit)
        # Check sorting (first should have >= second)
        self.assertGreaterEqual(top[0]["runs"], top[1]["runs"])
        # Check required fields
        self.assertIn("player_name", top[0])
        self.assertIn("average", top[0])
        self.assertIn("strike_rate", top[0])
        
    def test_highest_individual_scores(self):
        limit = 3
        high = highest_individual_scores(limit)
        self.assertEqual(len(high), limit)
        self.assertGreaterEqual(high[0]["runs"], high[1]["runs"])
        self.assertIn("batting_team", high[0])
        self.assertIn("bowling_team", high[0])
        self.assertIn("date", high[0])
        
    def test_batting_average(self):
        avg_info = batting_average("Virat Kohli")
        self.assertEqual(avg_info["player_name"], "V Kohli")
        self.assertGreater(avg_info["runs"], 5000)
        self.assertGreater(avg_info["batting_average"], 30.0)
        
    def test_strike_rate(self):
        sr_info = strike_rate("Virat Kohli")
        self.assertEqual(sr_info["player_name"], "V Kohli")
        self.assertGreater(sr_info["strike_rate"], 100.0)
        
    def test_boundary_percentage(self):
        bp_info = boundary_percentage("Virat Kohli")
        self.assertEqual(bp_info["player_name"], "V Kohli")
        self.assertGreater(bp_info["boundary_runs_percentage"], 30.0)
        self.assertGreater(bp_info["boundary_balls_percentage"], 5.0)


if __name__ == "__main__":
    unittest.main()
