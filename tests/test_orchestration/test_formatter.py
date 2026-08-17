"""
Unit tests for CricGPT Response Formatter (Phase 3A.5).
"""

import unittest
from orchestration.intents import Intent
from orchestration.schemas import ExecutionResult
from orchestration.exceptions import FormattingError
from orchestration.formatter import ResponseFormatter


class TestResponseFormatter(unittest.TestCase):
    """Test suite for ResponseFormatter implementation."""

    def setUp(self):
        self.formatter = ResponseFormatter()

    # 1. BATTING_AVERAGE
    def test_format_batting_average(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTING_AVERAGE,
            result={
                "player_name": "V Kohli",
                "runs": 9346,
                "innings": 277,
                "dismissals": 229,
                "batting_average": 40.81
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("V Kohli's batting average is 40.81", res)
        self.assertIn("9,346 runs", res)
        self.assertIn("277 innings", res)

    # 2. BATTING_STRIKE_RATE
    def test_format_batting_strike_rate(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTING_STRIKE_RATE,
            result={
                "player_name": "RG Sharma",
                "runs": 7331,
                "balls": 5612,
                "innings": 257,
                "strike_rate": 130.62
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("RG Sharma's batting strike rate is 130.62", res)
        self.assertIn("7,331 runs", res)
        self.assertIn("5,612 balls", res)

    # 3. BOUNDARY_PERCENTAGE
    def test_format_boundary_percentage(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BOUNDARY_PERCENTAGE,
            result={
                "player_name": "V Kohli",
                "runs": 9346,
                "balls": 7198,
                "innings": 277,
                "fours": 700,
                "sixes": 250,
                "boundary_runs": 4300,
                "boundary_runs_percentage": 46.01
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("boundary runs percentage is 46.01%", res)
        self.assertIn("700 fours", res)
        self.assertIn("250 sixes", res)

    # 4. BOWLING_ECONOMY
    def test_format_bowling_economy(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BOWLING_ECONOMY,
            result={
                "player_name": "JJ Bumrah",
                "runs_conceded": 4469,
                "balls_bowled": 3668,
                "overs": 611.2,
                "innings": 162,
                "economy_rate": 7.31
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("JJ Bumrah's bowling economy rate is 7.31", res)
        self.assertIn("4,469 runs", res)
        self.assertIn("611.2 overs", res)

    # 5. BATTER_VS_BOWLER
    def test_format_batter_vs_bowler(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTER_VS_BOWLER,
            result={
                "batter_name": "V Kohli",
                "bowler_name": "JJ Bumrah",
                "balls": 110,
                "runs": 164,
                "dots": 37,
                "fours": 17,
                "sixes": 6,
                "dismissals": 5,
                "strike_rate": 149.09,
                "average": 32.8
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("V Kohli vs JJ Bumrah: 164 runs off 110 balls", res)
        self.assertIn("Average: 32.8", res)

    # 6. PLAYER_SEARCH
    def test_format_player_search(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_SEARCH,
            result=[
                {"player_name": "V Kohli", "player_id": 1, "registry_id": "vk1"},
                {"player_name": "T Kohli", "player_id": 2, "registry_id": "tk2"}
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Matching players found:", res)
        self.assertIn("1. V Kohli (ID: 1)", res)
        self.assertIn("2. T Kohli (ID: 2)", res)

    # 7. PLAYER_PROFILE
    def test_format_player_profile(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_PROFILE,
            result={"player_id": 1, "player_name": "V Kohli", "registry_id": "vk123"}
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Player Profile for V Kohli: Player ID: 1, Registry ID: vk123.", res)

    # 8. PLAYER_CAREER
    def test_format_player_career(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_CAREER,
            result={
                "player_name": "V Kohli",
                "matches": 277,
                "batting_runs": 9346,
                "batting_innings": 277,
                "batting_average": 40.81,
                "batting_strike_rate": 129.85,
                "wickets": 4,
                "bowling_economy": 8.6,
                "catches": 110
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Career summary for V Kohli:", res)
        self.assertIn("Matches: 277", res)
        self.assertIn("9,346 runs", res)

    # 9. PLAYER_RECENT_MATCHES
    def test_format_player_recent_matches(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_RECENT_MATCHES,
            result=[
                {
                    "match_id": 1304112,
                    "date": "2022-05-18",
                    "venue_name": "Wankhede Stadium",
                    "player_team": "RCB",
                    "opponent_team": "CSK",
                    "winner_team": "RCB",
                    "result": "runs",
                    "result_margin": 13
                }
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Recent matches (1):", res)
        self.assertIn("Match 1304112 (2022-05-18): RCB vs CSK", res)

    # 10. PLAYER_MATCH_HISTORY
    def test_format_player_match_history(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_MATCH_HISTORY,
            result=[
                {
                    "match_id": 1304112,
                    "date": "2022-05-18",
                    "venue_name": "Wankhede Stadium",
                    "player_team": "RCB",
                    "opponent_team": "CSK",
                    "winner_team": "RCB"
                }
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Match history (1 matches):", res)

    # 11. TOP_RUN_SCORERS
    def test_format_top_run_scorers(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.TOP_RUN_SCORERS,
            result=[
                {"player_name": "V Kohli", "runs": 9346, "matches": 277, "average": 40.81, "strike_rate": 129.85},
                {"player_name": "RG Sharma", "runs": 7331, "matches": 257, "average": 29.80, "strike_rate": 130.62}
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Top run scorers:", res)
        self.assertIn("1. V Kohli — 9,346 runs", res)
        self.assertIn("2. RG Sharma — 7,331 runs", res)

    # 12. HIGHEST_INDIVIDUAL_SCORES
    def test_format_highest_individual_scores(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.HIGHEST_INDIVIDUAL_SCORES,
            result=[
                {"player_name": "V Kohli", "runs": 183, "balls": 148, "batting_team": "RCB", "bowling_team": "CSK", "date": "2022-05-18"}
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Highest individual scores:", res)
        self.assertIn("1. V Kohli — 183 runs off 148 balls", res)

    # 13. TOP_WICKET_TAKERS
    def test_format_top_wicket_takers(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.TOP_WICKET_TAKERS,
            result=[
                {"player_name": "YS Chahal", "wickets": 187, "economy_rate": 7.67, "bowling_average": 21.68}
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Top wicket takers:", res)
        self.assertIn("1. YS Chahal — 187 wickets", res)

    # 14. BEST_BOWLING_FIGURES
    def test_format_best_bowling_figures(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BEST_BOWLING_FIGURES,
            result=[
                {"player_name": "Alzarri Joseph", "wickets": 6, "runs": 12, "overs": 3.4, "bowling_team": "MI", "batting_team": "SRH", "date": "2019-04-06"}
            ]
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Best bowling figures:", res)
        self.assertIn("1. Alzarri Joseph — 6/12 in 3.4 overs", res)

    # 15. TEAM_RECORD
    def test_format_team_record(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.TEAM_RECORD,
            result={
                "team_name": "MI",
                "matches": 231,
                "wins": 138,
                "losses": 89,
                "ties": 4,
                "win_percentage": 59.74,
                "avg_score": 162.5,
                "avg_conceded": 158.2
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("MI team record: 231 matches played, 138 wins, 89 losses", res)
        self.assertIn("Win Rate: 59.74%", res)

    # 16. TEAM_HEAD_TO_HEAD
    def test_format_team_head_to_head(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.TEAM_HEAD_TO_HEAD,
            result={
                "team1": "MI",
                "team2": "CSK",
                "matches_played": 36,
                "team1_wins": 20,
                "team2_wins": 16,
                "ties_or_no_results": 0,
                "recent_matches": [
                    {"match_id": 1304112, "date": "2022-05-18", "winner": "MI", "result": "runs", "margin": 5}
                ]
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Head-to-head: MI vs CSK", res)
        self.assertIn("Matches played: 36", res)
        self.assertIn("MI wins: 20", res)
        self.assertIn("CSK wins: 16", res)

    # 17. VENUE_SUMMARY
    def test_format_venue_summary(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.VENUE_SUMMARY,
            result={
                "venue_name": "Wankhede Stadium",
                "city": "Mumbai",
                "matches_played": 104,
                "avg_first_innings_score": 168.4,
                "avg_second_innings_score": 159.2,
                "highest_score": 235,
                "lowest_score": 67,
                "bat_first_wins": 48,
                "bowl_first_wins": 56,
                "successful_chases": 56
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Venue summary for Wankhede Stadium, Mumbai:", res)
        self.assertIn("Matches played: 104", res)

    # 18. MATCH_SUMMARY
    def test_format_match_summary(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.MATCH_SUMMARY,
            result={
                "match_id": 1304112,
                "date": "2022-05-18",
                "venue": {"venue_name": "Wankhede Stadium"},
                "team1": {"team_name": "RCB"},
                "team2": {"team_name": "CSK"},
                "result": {"winning_margin_text": "Won by 13 runs", "winner": {"team_name": "RCB"}},
                "player_of_match": {"player_name": "V Kohli"},
                "innings": [
                    {"batting_team": "RCB", "score": "173/8", "overs": "20.0"},
                    {"batting_team": "CSK", "score": "160/8", "overs": "20.0"}
                ]
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Match Summary (Match 1304112, 2022-05-18):", res)
        self.assertIn("RCB vs CSK at Wankhede Stadium", res)
        self.assertIn("Result: Won by 13 runs (Winner: RCB)", res)

    # 19. MATCH_SCORECARD
    def test_format_match_scorecard(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.MATCH_SCORECARD,
            result={
                "match_id": 1304112,
                "innings": [
                    {
                        "innings_no": 1,
                        "batting_team": "RCB",
                        "score": "173/8",
                        "total_overs": "20.0",
                        "batting_card": [
                            {"batter_name": "V Kohli", "runs": 30, "balls": 33, "dismissal": "b Choudhary"}
                        ],
                        "bowling_card": [
                            {"bowler_name": "M Theekshana", "overs": 4.0, "maidens": 0, "runs": 27, "wickets": 3, "economy": 6.75}
                        ]
                    }
                ]
            }
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Match Scorecard (Match 1304112):", res)
        self.assertIn("Innings 1: RCB (173/8, 20.0 overs)", res)
        self.assertIn("- V Kohli: 30 (33b) - b Choudhary", res)

    # 20. Empty result handling
    def test_format_empty_list_result(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.PLAYER_SEARCH,
            result=[]
        )
        res = self.formatter.format(exec_res)
        self.assertEqual(res, "No matching records were found.")

    # 21. None result handling
    def test_format_none_result(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTING_AVERAGE,
            result=None
        )
        res = self.formatter.format(exec_res)
        self.assertEqual(res, "No result was returned for this query.")

    # 22. Failed execution handling
    def test_format_failed_execution(self):
        exec_res = ExecutionResult(
            success=False,
            intent=Intent.BATTING_AVERAGE,
            result=None
        )
        res = self.formatter.format(exec_res)
        self.assertIn("Execution failed for intent 'BATTING_AVERAGE'.", res)

    # 23. Missing optional fields
    def test_format_missing_optional_fields(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTING_AVERAGE,
            result={"player_name": "V Kohli"} # missing runs, innings, dismissals, batting_average
        )
        res = self.formatter.format(exec_res)
        self.assertIn("V Kohli's batting average is 0.0", res)

    # 24. Empty list handling in TOP_RUN_SCORERS
    def test_format_empty_top_run_scorers(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.TOP_RUN_SCORERS,
            result=[]
        )
        res = self.formatter.format(exec_res)
        self.assertEqual(res, "No matching records were found.")

    # 25. UNKNOWN intent handling
    def test_format_unknown_intent(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.UNKNOWN,
            result={"data": "test"}
        )
        with self.assertRaises(FormattingError):
            self.formatter.format(exec_res)

    # 26. Unexpected result structure / FormattingError
    def test_format_unexpected_result_structure(self):
        exec_res = ExecutionResult(
            success=True,
            intent=Intent.BATTING_AVERAGE,
            result="invalid string result instead of dict"
        )
        with self.assertRaises(FormattingError):
            self.formatter.format(exec_res)


if __name__ == "__main__":
    unittest.main()
