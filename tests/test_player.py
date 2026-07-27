import unittest
import os
import sys

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.player import (
    search_players,
    get_player,
    get_player_career,
    get_player_match_history,
    get_player_last_n_matches,
)
from analytics.utils import PlayerNotFoundError, AmbiguousMatchError


class TestPlayerAnalytics(unittest.TestCase):
    
    def test_search_players(self):
        # Search for a substring we know exists
        results = search_players("Kohli")
        self.assertGreater(len(results), 0)
        # Verify keys
        first = results[0]
        self.assertIn("player_id", first)
        self.assertIn("player_name", first)
        self.assertIn("registry_id", first)
        
        # Empty query
        self.assertEqual(search_players(""), [])
        
    def test_get_player_exact_and_heuristics(self):
        # Exact match
        p1 = get_player("V Kohli")
        self.assertEqual(p1["player_name"], "V Kohli")
        
        # Heuristic matching "Virat Kohli" -> "V Kohli"
        p2 = get_player("Virat Kohli")
        self.assertEqual(p2["player_id"], p1["player_id"])
        
        # Ambiguous match (multiple Kohlis: V Kohli, T Kohli)
        with self.assertRaises(AmbiguousMatchError) as ctx:
            get_player("Kohli")
        self.assertEqual(
            str(ctx.exception),
            "Multiple players matched 'Kohli'.\n\nCandidates:\n- V Kohli\n- T Kohli"
        )
            
        # Non-existent player
        with self.assertRaises(PlayerNotFoundError):
            get_player("NonExistentPlayerXYZ")
            
    def test_get_player_career(self):
        # Retrieve career for a known player
        career = get_player_career("Virat Kohli")
        self.assertEqual(career["player_name"], "V Kohli")
        self.assertGreater(career["matches"], 0)
        self.assertGreater(career["batting_runs"], 5000)  # Kohli has > 9000 runs in IPL
        self.assertGreater(career["batting_average"], 30.0)
        self.assertGreater(career["batting_strike_rate"], 100.0)
        
    def test_get_player_match_history(self):
        # Fetch history
        history = get_player_match_history("Virat Kohli")
        self.assertGreater(len(history), 0)
        first = history[0]
        self.assertIn("match_id", first)
        self.assertIn("player_team", first)
        self.assertIn("opponent_team", first)
        self.assertIn("winner_team", first)
        
    def test_get_player_last_n_matches(self):
        # Fetch last 5 matches
        history_5 = get_player_last_n_matches("Virat Kohli", 5)
        self.assertEqual(len(history_5), 5)
        
        # Zero limit
        self.assertEqual(get_player_last_n_matches("Virat Kohli", 0), [])

    def test_extended_initials_matching(self):
        # Lasith Malinga -> SL Malinga
        p1 = get_player("Lasith Malinga")
        self.assertEqual(p1["player_name"], "SL Malinga")
        
        # Ravindra Jadeja -> RA Jadeja
        p2 = get_player("Ravindra Jadeja")
        self.assertEqual(p2["player_name"], "RA Jadeja")
        
        # AB de Villiers -> AB de Villiers
        p3 = get_player("AB de Villiers")
        self.assertEqual(p3["player_name"], "AB de Villiers")
        
        # Dwayne Bravo -> should raise AmbiguousMatchError due to DJ Bravo and DM Bravo
        with self.assertRaises(AmbiguousMatchError):
            get_player("Dwayne Bravo")


if __name__ == "__main__":
    unittest.main()
