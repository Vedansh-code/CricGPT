"""
Unit tests for CricGPT Natural Language Query Parser (Phase 3A.2).
"""

import unittest
from orchestration.intents import Intent
from orchestration.schemas import QueryPlan, QueryArguments
from orchestration.exceptions import PlanningError
from orchestration.parser import QueryParser


class TestQueryParser(unittest.TestCase):
    """Test suite for QueryParser implementation."""

    def setUp(self):
        self.parser = QueryParser()

    # -------------------------------------------------------------------------
    # 1. Player Intents
    # -------------------------------------------------------------------------
    def test_player_search(self):
        plan = self.parser.parse("search player Kohli")
        self.assertEqual(plan.intent, Intent.PLAYER_SEARCH)
        self.assertEqual(plan.arguments.player_name, "Kohli")
        self.assertFalse(plan.requires_clarification)
        self.assertTrue(0.0 <= plan.confidence <= 1.0)

    def test_player_profile(self):
        plan = self.parser.parse("who is Jasprit Bumrah")
        self.assertEqual(plan.intent, Intent.PLAYER_PROFILE)
        self.assertEqual(plan.arguments.player_name, "Jasprit Bumrah")
        self.assertFalse(plan.requires_clarification)

    def test_player_career(self):
        plan = self.parser.parse("Kohli career stats")
        self.assertEqual(plan.intent, Intent.PLAYER_CAREER)
        self.assertEqual(plan.arguments.player_name, "Kohli")
        self.assertFalse(plan.requires_clarification)

    def test_player_recent_matches(self):
        plan = self.parser.parse("Show me Kohli's last 5 matches")
        self.assertEqual(plan.intent, Intent.PLAYER_RECENT_MATCHES)
        self.assertEqual(plan.arguments.player_name, "Kohli")
        self.assertEqual(plan.arguments.limit, 5)
        self.assertFalse(plan.requires_clarification)

    def test_player_match_history(self):
        plan = self.parser.parse("match history of Kohli")
        self.assertEqual(plan.intent, Intent.PLAYER_MATCH_HISTORY)
        self.assertEqual(plan.arguments.player_name, "Kohli")
        self.assertFalse(plan.requires_clarification)

    # -------------------------------------------------------------------------
    # 2. Batting Analytics Intents
    # -------------------------------------------------------------------------
    def test_top_run_scorers(self):
        plan = self.parser.parse("Who are the top run scorers?")
        self.assertEqual(plan.intent, Intent.TOP_RUN_SCORERS)
        self.assertIsNone(plan.arguments.limit)
        self.assertFalse(plan.requires_clarification)

        plan_limit = self.parser.parse("top 10 run scorers")
        self.assertEqual(plan_limit.intent, Intent.TOP_RUN_SCORERS)
        self.assertEqual(plan_limit.arguments.limit, 10)

    def test_highest_individual_scores(self):
        plan = self.parser.parse("highest individual score")
        self.assertEqual(plan.intent, Intent.HIGHEST_INDIVIDUAL_SCORES)
        self.assertFalse(plan.requires_clarification)

        plan_limit = self.parser.parse("top 5 highest individual scores")
        self.assertEqual(plan_limit.intent, Intent.HIGHEST_INDIVIDUAL_SCORES)
        self.assertEqual(plan_limit.arguments.limit, 5)

    def test_batting_average(self):
        plan = self.parser.parse("What is Virat Kohli's batting average?")
        self.assertEqual(plan.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(plan.arguments.player_name, "Virat Kohli")
        self.assertEqual(plan.source, "rule_based_parser")
        self.assertFalse(plan.requires_clarification)

    def test_batting_strike_rate(self):
        plan = self.parser.parse("Kohli strike rate")
        self.assertEqual(plan.intent, Intent.BATTING_STRIKE_RATE)
        self.assertEqual(plan.arguments.player_name, "Kohli")
        self.assertFalse(plan.requires_clarification)

    def test_boundary_percentage(self):
        plan = self.parser.parse("boundary percentage of Rohit")
        self.assertEqual(plan.intent, Intent.BOUNDARY_PERCENTAGE)
        self.assertEqual(plan.arguments.player_name, "Rohit")
        self.assertFalse(plan.requires_clarification)

    # -------------------------------------------------------------------------
    # 3. Bowling Analytics Intents
    # -------------------------------------------------------------------------
    def test_top_wicket_takers(self):
        plan = self.parser.parse("Who has taken the most wickets?")
        self.assertEqual(plan.intent, Intent.TOP_WICKET_TAKERS)
        self.assertIsNone(plan.arguments.limit)
        self.assertFalse(plan.requires_clarification)

    def test_best_bowling_figures(self):
        plan = self.parser.parse("best bowling figures of Bumrah")
        self.assertEqual(plan.intent, Intent.BEST_BOWLING_FIGURES)
        self.assertEqual(plan.arguments.player_name, "Bumrah")
        self.assertFalse(plan.requires_clarification)

    def test_bowling_economy(self):
        plan = self.parser.parse("Bumrah economy")
        self.assertEqual(plan.intent, Intent.BOWLING_ECONOMY)
        self.assertEqual(plan.arguments.player_name, "Bumrah")
        self.assertFalse(plan.requires_clarification)

    # -------------------------------------------------------------------------
    # 4. Matchup Intents
    # -------------------------------------------------------------------------
    def test_batter_vs_bowler(self):
        plan = self.parser.parse("How has Virat Kohli performed against Jasprit Bumrah?")
        self.assertEqual(plan.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan.arguments.batter, "Virat Kohli")
        self.assertEqual(plan.arguments.bowler, "Jasprit Bumrah")
        self.assertFalse(plan.requires_clarification)

        plan_short = self.parser.parse("Kohli vs Bumrah")
        self.assertEqual(plan_short.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan_short.arguments.batter, "Kohli")
        self.assertEqual(plan_short.arguments.bowler, "Bumrah")

        plan_against = self.parser.parse("Kohli against Bumrah")
        self.assertEqual(plan_against.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan_against.arguments.batter, "Kohli")
        self.assertEqual(plan_against.arguments.bowler, "Bumrah")

        plan_versus = self.parser.parse("Virat Kohli versus Jasprit Bumrah")
        self.assertEqual(plan_versus.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan_versus.arguments.batter, "Virat Kohli")
        self.assertEqual(plan_versus.arguments.bowler, "Jasprit Bumrah")

        plan_v = self.parser.parse("Kohli v Bumrah")
        self.assertEqual(plan_v.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan_v.arguments.batter, "Kohli")
        self.assertEqual(plan_v.arguments.bowler, "Bumrah")

        plan_v_dot = self.parser.parse("Kohli v. Bumrah")
        self.assertEqual(plan_v_dot.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan_v_dot.arguments.batter, "Kohli")
        self.assertEqual(plan_v_dot.arguments.bowler, "Bumrah")

    def test_v_kohli_batting_average_regression(self):
        """Test fix for 'What is V Kohli\'s batting average?' false-positive matchup bug."""
        plan = self.parser.parse("What is V Kohli's batting average?")
        self.assertEqual(plan.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(plan.arguments.player_name, "V Kohli")
        self.assertFalse(plan.requires_clarification)

    def test_virat_kohli_batting_average(self):
        """Test 'What is Virat Kohli\'s batting average?' parsing."""
        plan = self.parser.parse("What is Virat Kohli's batting average?")
        self.assertEqual(plan.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(plan.arguments.player_name, "Virat Kohli")
        self.assertFalse(plan.requires_clarification)

    def test_virat_kohli_strike_rate(self):
        """Test 'What is Virat Kohli\'s strike rate?' parsing."""
        plan = self.parser.parse("What is Virat Kohli's strike rate?")
        self.assertEqual(plan.intent, Intent.BATTING_STRIKE_RATE)
        self.assertEqual(plan.arguments.player_name, "Virat Kohli")
        self.assertFalse(plan.requires_clarification)

    def test_no_false_positive_matchup_for_initials_and_queries(self):
        """Ensure questions with player initials like 'V Kohli' or stat keywords are not misclassified as matchups."""
        plan_laxman = self.parser.parse("What is V. Laxman's strike rate?")
        self.assertEqual(plan_laxman.intent, Intent.BATTING_STRIKE_RATE)
        self.assertEqual(plan_laxman.arguments.player_name, "V. Laxman")

        plan_career = self.parser.parse("Show me V Kohli's career stats")
        self.assertEqual(plan_career.intent, Intent.PLAYER_CAREER)
        self.assertEqual(plan_career.arguments.player_name, "V Kohli")

        plan_economy = self.parser.parse("What is Bumrah's bowling economy?")
        self.assertEqual(plan_economy.intent, Intent.BOWLING_ECONOMY)
        self.assertEqual(plan_economy.arguments.player_name, "Bumrah")


    # -------------------------------------------------------------------------
    # 5. Team Analytics Intents
    # -------------------------------------------------------------------------
    def test_team_record(self):
        plan = self.parser.parse("MI record")
        self.assertEqual(plan.intent, Intent.TEAM_RECORD)
        self.assertEqual(plan.arguments.team_name, "MI")
        self.assertFalse(plan.requires_clarification)

    def test_team_head_to_head(self):
        plan = self.parser.parse("MI vs CSK head to head")
        self.assertEqual(plan.intent, Intent.TEAM_HEAD_TO_HEAD)
        self.assertEqual(plan.arguments.team1, "MI")
        self.assertEqual(plan.arguments.team2, "CSK")
        self.assertFalse(plan.requires_clarification)

    # -------------------------------------------------------------------------
    # 6. Venue Intents
    # -------------------------------------------------------------------------
    def test_venue_summary(self):
        plan = self.parser.parse("Give me the stats for Wankhede")
        self.assertEqual(plan.intent, Intent.VENUE_SUMMARY)
        self.assertEqual(plan.arguments.venue_name, "Wankhede")
        self.assertFalse(plan.requires_clarification)

    # -------------------------------------------------------------------------
    # 7. Match Intents
    # -------------------------------------------------------------------------
    def test_match_scorecard(self):
        plan = self.parser.parse("Show me the scorecard for match 1304112")
        self.assertEqual(plan.intent, Intent.MATCH_SCORECARD)
        self.assertEqual(plan.arguments.match_id, 1304112)
        self.assertFalse(plan.requires_clarification)

    def test_match_summary(self):
        plan = self.parser.parse("summary of match 1304112")
        self.assertEqual(plan.intent, Intent.MATCH_SUMMARY)
        self.assertEqual(plan.arguments.match_id, 1304112)
        self.assertFalse(plan.requires_clarification)

    # -------------------------------------------------------------------------
    # 8. Input Validation & Edge Cases
    # -------------------------------------------------------------------------
    def test_empty_string_input(self):
        with self.assertRaises(PlanningError):
            self.parser.parse("")

    def test_whitespace_input(self):
        with self.assertRaises(PlanningError):
            self.parser.parse("   ")

    def test_surrounding_whitespace_and_case(self):
        plan = self.parser.parse("  what is kohli's batting average?  ")
        self.assertEqual(plan.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(plan.arguments.player_name, "Kohli")

    def test_invalid_match_id(self):
        with self.assertRaises(PlanningError):
            self.parser.parse("scorecard for match -1304112")

    def test_invalid_limit(self):
        with self.assertRaises(PlanningError):
            self.parser.parse("last -5 matches for Kohli")

    # -------------------------------------------------------------------------
    # 9. Ambiguity & Clarification Handling
    # -------------------------------------------------------------------------
    def test_ambiguous_kohli_stats(self):
        plan = self.parser.parse("Kohli stats")
        self.assertEqual(plan.intent, Intent.PLAYER_PROFILE)
        self.assertEqual(plan.arguments.player_name, "Kohli")
        self.assertEqual(plan.confidence, 0.5)
        self.assertFalse(plan.requires_clarification)

    def test_vague_how_did_kohli_perform(self):
        plan = self.parser.parse("How did Kohli perform?")
        self.assertTrue(plan.requires_clarification)
        self.assertIsNotNone(plan.clarification_message)
        self.assertEqual(plan.arguments.player_name, "Kohli")

    def test_vague_show_me_the_stats(self):
        plan = self.parser.parse("Show me the stats")
        self.assertEqual(plan.intent, Intent.UNKNOWN)
        self.assertTrue(plan.requires_clarification)
        self.assertIsNotNone(plan.clarification_message)
        self.assertEqual(plan.confidence, 0.0)

    # -------------------------------------------------------------------------
    # 10. Unknown / Unsupported Questions
    # -------------------------------------------------------------------------
    def test_unsupported_questions(self):
        plan = self.parser.parse("Who will win tomorrow's match?")
        self.assertEqual(plan.intent, Intent.UNKNOWN)
        self.assertEqual(plan.confidence, 0.0)
        self.assertFalse(plan.requires_clarification)

        plan2 = self.parser.parse("What is the best cricket strategy?")
        self.assertEqual(plan2.intent, Intent.UNKNOWN)
        self.assertEqual(plan2.confidence, 0.0)

    # -------------------------------------------------------------------------
    # 11. Confidence Range & Source Verification
    # -------------------------------------------------------------------------
    def test_confidence_values_and_source(self):
        questions = [
            "What is Virat Kohli's batting average?",
            "Show me Kohli's last 5 matches",
            "Who are the top run scorers?",
            "How has Kohli performed against Bumrah?",
            "MI vs CSK head to head",
            "Give me Wankhede statistics",
            "Show me match 1304112 scorecard",
            "Who has taken the most wickets?",
            "Kohli stats",
            "Show me the stats",
            "Who will win tomorrow's match?"
        ]
        for q in questions:
            plan = self.parser.parse(q)
            self.assertTrue(0.0 <= plan.confidence <= 1.0, f"Confidence out of range for query: {q}")
            self.assertEqual(plan.source, "rule_based_parser")


if __name__ == "__main__":
    unittest.main()
