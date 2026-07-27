import unittest
import os
import sys

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.database import get_connection
from analytics.matchup import get_batter_vs_bowler
from analytics.match import get_match_summary, get_scorecard
from analytics.team import get_team_record, head_to_head
from analytics.venue import venue_summary
from analytics.utils import (
    TeamNotFoundError,
    VenueNotFoundError,
    MatchNotFoundError,
)


class TestOtherAnalytics(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Dynamically fetch a valid match_id from the database to ensure test is robust
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT match_id FROM matches LIMIT 1")
            cls.match_id = cursor.fetchone()[0]
            
            # Fetch a valid venue name
            cursor.execute("SELECT venue_name FROM venues LIMIT 1")
            cls.venue_name = cursor.fetchone()[0]
        finally:
            conn.close()
            
    def test_get_batter_vs_bowler(self):
        matchup = get_batter_vs_bowler("Virat Kohli", "Jasprit Bumrah")
        self.assertEqual(matchup["batter_name"], "V Kohli")
        self.assertEqual(matchup["bowler_name"], "JJ Bumrah")
        self.assertIn("runs", matchup)
        self.assertIn("balls", matchup)
        self.assertIn("dismissals", matchup)
        self.assertIn("strike_rate", matchup)
        self.assertIn("average", matchup)
        
    def test_get_match_summary(self):
        summary = get_match_summary(self.match_id)
        self.assertEqual(summary["match_id"], self.match_id)
        self.assertIn("season", summary)
        self.assertIn("team1", summary)
        self.assertIn("team2", summary)
        self.assertIn("innings", summary)
        
        # Invalid match ID
        with self.assertRaises(MatchNotFoundError):
            get_match_summary(-999)
            
    def test_get_scorecard(self):
        scorecard = get_scorecard(self.match_id)
        self.assertEqual(scorecard["match_id"], self.match_id)
        self.assertIn("innings", scorecard)
        self.assertGreater(len(scorecard["innings"]), 0)
        
        first_innings = scorecard["innings"][0]
        self.assertIn("batting_team", first_innings)
        self.assertIn("bowling_team", first_innings)
        self.assertIn("batting_card", first_innings)
        self.assertIn("bowling_card", first_innings)
        self.assertIn("total_runs", first_innings)
        self.assertIn("total_wickets", first_innings)
        self.assertIn("extras", first_innings)
        
    def test_get_team_record(self):
        record = get_team_record("CSK")
        self.assertEqual(record["team_name"], "Chennai Super Kings")
        self.assertGreater(record["matches"], 0)
        self.assertIn("win_percentage", record)
        
        # Invalid team
        with self.assertRaises(TeamNotFoundError):
            get_team_record("NonExistentTeamXYZ")
            
    def test_head_to_head(self):
        h2h = head_to_head("CSK", "MI")
        self.assertEqual(h2h["team1"], "Chennai Super Kings")
        self.assertEqual(h2h["team2"], "Mumbai Indians")
        self.assertGreater(h2h["matches_played"], 0)
        self.assertIn("recent_matches", h2h)
        
        # Verify venue formatting has no duplicates (e.g. Wankhede Stadium, Mumbai, Mumbai)
        for m in h2h["recent_matches"]:
            venue = m["venue"]
            parts = [p.strip() for p in venue.split(",")]
            if len(parts) >= 2:
                self.assertNotEqual(parts[-1].lower(), parts[-2].lower())
        
    def test_venue_summary(self):
        v_sum = venue_summary(self.venue_name)
        self.assertEqual(v_sum["venue_name"], self.venue_name)
        self.assertGreater(v_sum["matches_played"], 0)
        self.assertIn("avg_first_innings_score", v_sum)
        
        # Invalid venue
        with self.assertRaises(VenueNotFoundError):
            venue_summary("NonExistentVenueXYZ")

    def test_venue_normalization_regression(self):
        from scripts.normalization import normalize_venue_name, normalize_city
        
        # Test normalize_venue_name variants
        self.assertEqual(normalize_venue_name("M.Chinnaswamy Stadium"), "M Chinnaswamy Stadium")
        self.assertEqual(normalize_venue_name("M Chinnaswamy Stadium"), "M Chinnaswamy Stadium")
        self.assertEqual(normalize_venue_name("M Chinnaswamy Stadium, Bengaluru"), "M Chinnaswamy Stadium")
        
        self.assertEqual(normalize_venue_name("Wankhede Stadium"), "Wankhede Stadium")
        self.assertEqual(normalize_venue_name("Wankhede Stadium, Mumbai"), "Wankhede Stadium")
        
        self.assertEqual(normalize_venue_name("MA Chidambaram Stadium, Chepauk"), "MA Chidambaram Stadium, Chepauk")
        self.assertEqual(normalize_venue_name("MA Chidambaram Stadium, Chepauk, Chennai"), "MA Chidambaram Stadium, Chepauk")
        
        # Test normalize_city variants
        self.assertEqual(normalize_city("M Chinnaswamy Stadium", "Bangalore"), "Bengaluru")
        self.assertEqual(normalize_city("M Chinnaswamy Stadium", "Bengaluru"), "Bengaluru")
        self.assertEqual(normalize_city("Dr DY Patil Sports Academy", "Navi Mumbai"), "Mumbai")
        self.assertEqual(normalize_city("Dr DY Patil Sports Academy", "Mumbai"), "Mumbai")
        self.assertEqual(normalize_city("Sheikh Zayed Stadium", None), "Abu Dhabi")
        self.assertEqual(normalize_city("Zayed Cricket Stadium", "Abu Dhabi"), "Abu Dhabi")

        # Test historical renames resolve to the same venue and return identical statistics
        f1 = venue_summary("Feroz Shah Kotla")
        f2 = venue_summary("Arun Jaitley Stadium")
        self.assertEqual(f1, f2)
        self.assertEqual(f1["venue_name"], "Arun Jaitley Stadium")
        self.assertEqual(f1["city"], "Delhi")
        
        s1 = venue_summary("Sardar Patel Stadium Motera")
        s2 = venue_summary("Narendra Modi Stadium")
        self.assertEqual(s1, s2)
        self.assertEqual(s1["venue_name"], "Narendra Modi Stadium")
        self.assertEqual(s1["city"], "Ahmedabad")
        
        p1 = venue_summary("Punjab Cricket Association Stadium")
        p2 = venue_summary("PCA IS Bindra Stadium")
        p3 = venue_summary("Punjab Cricket Association IS Bindra Stadium, Mohali")
        self.assertEqual(p1, p2)
        self.assertEqual(p2, p3)
        self.assertEqual(p1["venue_name"], "Punjab Cricket Association IS Bindra Stadium, Mohali")
        self.assertEqual(p1["city"], "Mohali")

    def test_match_analytics_improvements_regression(self):
        # Fetch summary of self.match_id
        summary = get_match_summary(self.match_id)
        
        # Verify venue contains venue_id
        self.assertIn("venue_id", summary["venue"])
        self.assertIsInstance(summary["venue"]["venue_id"], int)
        
        # Verify team1 and team2 are dicts with team_id and team_name
        self.assertIsInstance(summary["team1"], dict)
        self.assertIn("team_id", summary["team1"])
        self.assertIn("team_name", summary["team1"])
        self.assertIsInstance(summary["team2"], dict)
        self.assertIn("team_id", summary["team2"])
        self.assertIn("team_name", summary["team2"])
        
        # Verify player_of_match is dict with player_id and player_name
        self.assertIsInstance(summary["player_of_match"], dict)
        self.assertIn("player_id", summary["player_of_match"])
        self.assertIn("player_name", summary["player_of_match"])
        
        # Verify winning_margin_text
        self.assertIn("winning_margin_text", summary["result"])
        self.assertTrue(
            summary["result"]["winning_margin_text"].startswith("Won by") or 
            summary["result"]["winning_margin_text"] == "Match Tied" or
            summary["result"]["winning_margin_text"] == "No Result"
        )
        
        # Verify innings score, run_rate, and format_overs
        for inn in summary["innings"]:
            self.assertIn("score", inn)
            self.assertIn("run_rate", inn)
            self.assertIsInstance(inn["run_rate"], float)
            self.assertIsInstance(inn["score"], str)
            self.assertIn("/", inn["score"])
            self.assertIsInstance(inn["overs"], str)
            self.assertRegex(inn["overs"], r"^\d+\.[0-5]$")
            
        # Fetch scorecard of self.match_id
        scorecard = get_scorecard(self.match_id)
        
        # Verify extras and fielders
        for inn in scorecard["innings"]:
            self.assertIn("score", inn)
            self.assertIn("run_rate", inn)
            self.assertIsInstance(inn["run_rate"], float)
            self.assertIsInstance(inn["score"], str)
            self.assertIn("/", inn["score"])
            
            # Expanded extras
            self.assertIsInstance(inn["extras"], dict)
            self.assertIn("total", inn["extras"])
            self.assertIn("wides", inn["extras"])
            self.assertIn("no_balls", inn["extras"])
            self.assertIn("byes", inn["extras"])
            self.assertIn("leg_byes", inn["extras"])
            
            # Batter fielders list
            for bat in inn["batting_card"]:
                self.assertIn("fielders", bat)
                self.assertIsInstance(bat["fielders"], list)
                
            # Bowler overs
            for bowl in inn["bowling_card"]:
                self.assertIsInstance(bowl["overs"], str)
                self.assertRegex(bowl["overs"], r"^\d+\.[0-5]$")


if __name__ == "__main__":
    unittest.main()
