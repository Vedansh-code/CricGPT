"""
Response Formatter for CricGPT Orchestration (Phase 3A.5).

This module provides the ResponseFormatter class, which converts ExecutionResult
objects into clear, human-readable natural language answers without querying databases,
executing SDK callables, or re-calculating statistics.
"""

from typing import Any, Dict, List

from orchestration.intents import Intent
from orchestration.schemas import ExecutionResult
from orchestration.exceptions import FormattingError


def fmt_num(val: Any) -> str:
    """Format an integer or float into a readable string with thousand separators."""
    if val is None:
        return "N/A"
    if isinstance(val, int):
        return f"{val:,}"
    if isinstance(val, float):
        if val % 1 == 0:
            return f"{int(val):,}"
        return f"{val:,.2f}".rstrip("0").rstrip(".")
    return str(val)


class ResponseFormatter:
    """
    Formats ExecutionResult into a clean, human-readable natural language answer.
    """

    def format(self, execution: ExecutionResult) -> str:
        """
        Format an ExecutionResult into a human-readable string answer.

        Args:
            execution: The ExecutionResult to format.

        Returns:
            Human-readable response string.

        Raises:
            FormattingError: If input is invalid, intent is UNKNOWN, or data structure is unexpected.
        """
        if not isinstance(execution, ExecutionResult):
            raise FormattingError("Input must be an ExecutionResult instance.")

        if not execution.success:
            return f"Execution failed for intent '{execution.intent.value}'."

        if execution.intent == Intent.UNKNOWN:
            raise FormattingError("Cannot format result for UNKNOWN intent.")

        if execution.result is None:
            return "No result was returned for this query."

        # Dispatch map for intent formatters
        formatters = {
            Intent.PLAYER_SEARCH: self._format_player_search,
            Intent.PLAYER_PROFILE: self._format_player_profile,
            Intent.PLAYER_CAREER: self._format_player_career,
            Intent.PLAYER_RECENT_MATCHES: self._format_player_recent_matches,
            Intent.PLAYER_MATCH_HISTORY: self._format_player_match_history,
            Intent.TOP_RUN_SCORERS: self._format_top_run_scorers,
            Intent.HIGHEST_INDIVIDUAL_SCORES: self._format_highest_individual_scores,
            Intent.BATTING_AVERAGE: self._format_batting_average,
            Intent.BATTING_STRIKE_RATE: self._format_batting_strike_rate,
            Intent.BOUNDARY_PERCENTAGE: self._format_boundary_percentage,
            Intent.TOP_WICKET_TAKERS: self._format_top_wicket_takers,
            Intent.BEST_BOWLING_FIGURES: self._format_best_bowling_figures,
            Intent.BOWLING_ECONOMY: self._format_bowling_economy,
            Intent.BATTER_VS_BOWLER: self._format_batter_vs_bowler,
            Intent.TEAM_RECORD: self._format_team_record,
            Intent.TEAM_HEAD_TO_HEAD: self._format_team_head_to_head,
            Intent.VENUE_SUMMARY: self._format_venue_summary,
            Intent.MATCH_SUMMARY: self._format_match_summary,
            Intent.MATCH_SCORECARD: self._format_match_scorecard,
        }

        formatter_fn = formatters.get(execution.intent)
        if not formatter_fn:
            raise FormattingError(f"No formatter defined for intent '{execution.intent.value}'.")

        try:
            return formatter_fn(execution.result)
        except Exception as e:
            if isinstance(e, FormattingError):
                raise
            raise FormattingError(
                f"Failed to format result for intent '{execution.intent.value}': {str(e)}"
            ) from e

    # -------------------------------------------------------------------------
    # Internal Intent Formatters
    # -------------------------------------------------------------------------

    def _format_batting_average(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for BATTING_AVERAGE.")
        name = data.get("player_name", "Player")
        avg = data.get("batting_average", 0.0)
        runs = data.get("runs", 0)
        innings = data.get("innings", 0)
        dismissals = data.get("dismissals", 0)
        return (
            f"{name}'s batting average is {avg}. "
            f"He has scored {fmt_num(runs)} runs in {fmt_num(innings)} innings with {fmt_num(dismissals)} dismissals."
        )

    def _format_batting_strike_rate(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for BATTING_STRIKE_RATE.")
        name = data.get("player_name", "Player")
        sr = data.get("strike_rate", 0.0)
        runs = data.get("runs", 0)
        balls = data.get("balls", 0)
        innings = data.get("innings", 0)
        return (
            f"{name}'s batting strike rate is {sr}. "
            f"He has scored {fmt_num(runs)} runs off {fmt_num(balls)} balls across {fmt_num(innings)} innings."
        )

    def _format_boundary_percentage(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for BOUNDARY_PERCENTAGE.")
        name = data.get("player_name", "Player")
        pct = data.get("boundary_runs_percentage", 0.0)
        fours = data.get("fours", 0)
        sixes = data.get("sixes", 0)
        b_runs = data.get("boundary_runs", 0)
        runs = data.get("runs", 0)
        return (
            f"{name}'s boundary runs percentage is {pct}% "
            f"({fmt_num(fours)} fours, {fmt_num(sixes)} sixes, totaling {fmt_num(b_runs)} runs out of {fmt_num(runs)} total runs)."
        )

    def _format_bowling_economy(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for BOWLING_ECONOMY.")
        name = data.get("player_name", "Player")
        econ = data.get("economy_rate", 0.0)
        runs = data.get("runs_conceded", 0)
        overs = data.get("overs", 0)
        innings = data.get("innings", 0)
        return (
            f"{name}'s bowling economy rate is {econ}. "
            f"He has conceded {fmt_num(runs)} runs in {overs} overs across {fmt_num(innings)} innings."
        )

    def _format_batter_vs_bowler(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for BATTER_VS_BOWLER.")
        batter = data.get("batter_name", "Batter")
        bowler = data.get("bowler_name", "Bowler")
        runs = data.get("runs", 0)
        balls = data.get("balls", 0)
        dismissals = data.get("dismissals", 0)
        avg = data.get("average", 0.0)
        sr = data.get("strike_rate", 0.0)
        dots = data.get("dots", 0)
        fours = data.get("fours", 0)
        sixes = data.get("sixes", 0)
        return (
            f"{batter} vs {bowler}: {fmt_num(runs)} runs off {fmt_num(balls)} balls, "
            f"dismissed {fmt_num(dismissals)} times (Average: {avg}, Strike Rate: {sr}, Dots: {fmt_num(dots)}, Fours: {fmt_num(fours)}, Sixes: {fmt_num(sixes)})."
        )

    def _format_player_search(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for PLAYER_SEARCH.")
        if not data:
            return "No matching records were found."
        lines = ["Matching players found:"]
        for i, p in enumerate(data, 1):
            if not isinstance(p, dict):
                continue
            name = p.get("player_name", "Unknown")
            pid = p.get("player_id", "N/A")
            lines.append(f"{i}. {name} (ID: {pid})")
        return "\n".join(lines)

    def _format_player_profile(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for PLAYER_PROFILE.")
        name = data.get("player_name", "Player")
        pid = data.get("player_id", "N/A")
        reg_id = data.get("registry_id", "N/A")
        return f"Player Profile for {name}: Player ID: {pid}, Registry ID: {reg_id}."

    def _format_player_career(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for PLAYER_CAREER.")
        name = data.get("player_name", "Player")
        matches = data.get("matches", 0)
        b_runs = data.get("batting_runs", 0)
        b_inn = data.get("batting_innings", 0)
        b_avg = data.get("batting_average", 0.0)
        b_sr = data.get("batting_strike_rate", 0.0)
        wkts = data.get("wickets", 0)
        econ = data.get("bowling_economy", 0.0)
        catches = data.get("catches", 0)

        econ_str = f"Economy: {econ}" if econ is not None else "Economy: N/A"
        return (
            f"Career summary for {name}:\n"
            f"Matches: {fmt_num(matches)}\n"
            f"Batting: {fmt_num(b_runs)} runs in {fmt_num(b_inn)} innings (Average: {b_avg}, Strike Rate: {b_sr})\n"
            f"Bowling: {fmt_num(wkts)} wickets ({econ_str})\n"
            f"Fielding: {fmt_num(catches)} catches"
        )

    def _format_player_recent_matches(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for PLAYER_RECENT_MATCHES.")
        if not data:
            return "No matching records were found."
        lines = [f"Recent matches ({len(data)}):"]
        for i, m in enumerate(data, 1):
            if not isinstance(m, dict):
                continue
            m_id = m.get("match_id", "N/A")
            dt = m.get("date", "N/A")
            p_team = m.get("player_team", "Team")
            opp_team = m.get("opponent_team", "Opponent")
            venue = m.get("venue_name", "Venue")
            winner = m.get("winner_team", "Winner")
            margin = m.get("result_margin", "")
            res = m.get("result", "")
            margin_str = f" ({margin} {res})" if margin else ""
            lines.append(f"{i}. Match {m_id} ({dt}): {p_team} vs {opp_team} at {venue} — Winner: {winner}{margin_str}")
        return "\n".join(lines)

    def _format_player_match_history(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for PLAYER_MATCH_HISTORY.")
        if not data:
            return "No matching records were found."
        lines = [f"Match history ({len(data)} matches):"]
        for i, m in enumerate(data, 1):
            if not isinstance(m, dict):
                continue
            m_id = m.get("match_id", "N/A")
            dt = m.get("date", "N/A")
            p_team = m.get("player_team", "Team")
            opp_team = m.get("opponent_team", "Opponent")
            venue = m.get("venue_name", "Venue")
            winner = m.get("winner_team", "Winner")
            lines.append(f"{i}. Match {m_id} ({dt}): {p_team} vs {opp_team} at {venue} — Winner: {winner}")
        return "\n".join(lines)

    def _format_top_run_scorers(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for TOP_RUN_SCORERS.")
        if not data:
            return "No matching records were found."
        lines = ["Top run scorers:"]
        for i, p in enumerate(data, 1):
            if not isinstance(p, dict):
                continue
            name = p.get("player_name", "Player")
            runs = p.get("runs", 0)
            matches = p.get("matches")
            avg = p.get("average")
            sr = p.get("strike_rate")
            extra = []
            if matches is not None:
                extra.append(f"Matches: {fmt_num(matches)}")
            if avg is not None:
                extra.append(f"Avg: {avg}")
            if sr is not None:
                extra.append(f"SR: {sr}")
            extra_str = f" ({', '.join(extra)})" if extra else ""
            lines.append(f"{i}. {name} — {fmt_num(runs)} runs{extra_str}")
        return "\n".join(lines)

    def _format_highest_individual_scores(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for HIGHEST_INDIVIDUAL_SCORES.")
        if not data:
            return "No matching records were found."
        lines = ["Highest individual scores:"]
        for i, s in enumerate(data, 1):
            if not isinstance(s, dict):
                continue
            name = s.get("player_name", "Player")
            runs = s.get("runs", 0)
            balls = s.get("balls", 0)
            bat_team = s.get("batting_team", "")
            bowl_team = s.get("bowling_team", "")
            dt = s.get("date", "")
            vs_str = f" ({bat_team} vs {bowl_team}, {dt})" if bat_team and bowl_team else ""
            lines.append(f"{i}. {name} — {fmt_num(runs)} runs off {fmt_num(balls)} balls{vs_str}")
        return "\n".join(lines)

    def _format_top_wicket_takers(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for TOP_WICKET_TAKERS.")
        if not data:
            return "No matching records were found."
        lines = ["Top wicket takers:"]
        for i, p in enumerate(data, 1):
            if not isinstance(p, dict):
                continue
            name = p.get("player_name", "Player")
            wkts = p.get("wickets", 0)
            econ = p.get("economy_rate")
            avg = p.get("bowling_average")
            extra = []
            if econ is not None:
                extra.append(f"Econ: {econ}")
            if avg is not None:
                extra.append(f"Avg: {avg}")
            extra_str = f" ({', '.join(extra)})" if extra else ""
            lines.append(f"{i}. {name} — {fmt_num(wkts)} wickets{extra_str}")
        return "\n".join(lines)

    def _format_best_bowling_figures(self, data: Any) -> str:
        if not isinstance(data, list):
            raise FormattingError("Expected list result for BEST_BOWLING_FIGURES.")
        if not data:
            return "No matching records were found."
        lines = ["Best bowling figures:"]
        for i, b in enumerate(data, 1):
            if not isinstance(b, dict):
                continue
            name = b.get("player_name", "Player")
            wkts = b.get("wickets", 0)
            runs = b.get("runs", 0)
            overs = b.get("overs", 0)
            bowl_team = b.get("bowling_team", "")
            bat_team = b.get("batting_team", "")
            dt = b.get("date", "")
            vs_str = f" ({bowl_team} vs {bat_team}, {dt})" if bowl_team and bat_team else ""
            lines.append(f"{i}. {name} — {wkts}/{runs} in {overs} overs{vs_str}")
        return "\n".join(lines)

    def _format_team_record(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for TEAM_RECORD.")
        name = data.get("team_name", "Team")
        matches = data.get("matches", 0)
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        ties = data.get("ties", 0)
        win_pct = data.get("win_percentage", 0.0)
        avg_score = data.get("avg_score", 0.0)
        avg_conc = data.get("avg_conceded", 0.0)
        return (
            f"{name} team record: {fmt_num(matches)} matches played, {fmt_num(wins)} wins, "
            f"{fmt_num(losses)} losses, {fmt_num(ties)} ties (Win Rate: {win_pct}%, Avg Score: {avg_score}, Avg Conceded: {avg_conc})."
        )

    def _format_team_head_to_head(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for TEAM_HEAD_TO_HEAD.")
        t1 = data.get("team1", "Team 1")
        t2 = data.get("team2", "Team 2")
        played = data.get("matches_played", 0)
        t1_wins = data.get("team1_wins", 0)
        t2_wins = data.get("team2_wins", 0)
        ties = data.get("ties_or_no_results", 0)
        recent = data.get("recent_matches", [])

        lines = [
            f"Head-to-head: {t1} vs {t2}",
            f"Matches played: {fmt_num(played)}",
            f"{t1} wins: {fmt_num(t1_wins)}",
            f"{t2} wins: {fmt_num(t2_wins)}",
            f"Ties/No results: {fmt_num(ties)}"
        ]
        if recent and isinstance(recent, list):
            lines.append("Recent matches:")
            for m in recent:
                if not isinstance(m, dict):
                    continue
                m_id = m.get("match_id", "N/A")
                dt = m.get("date", "N/A")
                winner = m.get("winner", "N/A")
                margin = m.get("margin", "")
                res = m.get("result", "")
                margin_str = f" ({margin} {res})" if margin else ""
                lines.append(f"- Match {m_id} ({dt}): Winner — {winner}{margin_str}")
        return "\n".join(lines)

    def _format_venue_summary(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for VENUE_SUMMARY.")
        name = data.get("venue_name", "Venue")
        city = data.get("city")
        city_str = f", {city}" if city else ""
        played = data.get("matches_played", 0)
        avg1 = data.get("avg_first_innings_score", 0.0)
        avg2 = data.get("avg_second_innings_score", 0.0)
        high = data.get("highest_score", 0)
        low = data.get("lowest_score", 0)
        bat1_wins = data.get("bat_first_wins", 0)
        bowl1_wins = data.get("bowl_first_wins", 0)
        chases = data.get("successful_chases", 0)

        return (
            f"Venue summary for {name}{city_str}:\n"
            f"Matches played: {fmt_num(played)}\n"
            f"Average 1st innings score: {avg1}\n"
            f"Average 2nd innings score: {avg2}\n"
            f"Highest score: {fmt_num(high)}\n"
            f"Lowest score: {fmt_num(low)}\n"
            f"Batting 1st wins: {fmt_num(bat1_wins)} | Bowling 1st wins: {fmt_num(bowl1_wins)} (Successful chases: {fmt_num(chases)})"
        )

    def _format_match_summary(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for MATCH_SUMMARY.")
        m_id = data.get("match_id", "N/A")
        dt = data.get("date", "N/A")
        v_info = data.get("venue") if isinstance(data.get("venue"), dict) else {}
        v_name = v_info.get("venue_name", "Venue")
        t1_info = data.get("team1") if isinstance(data.get("team1"), dict) else {}
        t1_name = t1_info.get("team_name", "Team 1")
        t2_info = data.get("team2") if isinstance(data.get("team2"), dict) else {}
        t2_name = t2_info.get("team_name", "Team 2")
        res_info = data.get("result") if isinstance(data.get("result"), dict) else {}
        margin_text = res_info.get("winning_margin_text", "Completed")
        winner_info = res_info.get("winner") if isinstance(res_info.get("winner"), dict) else {}
        winner_name = winner_info.get("team_name", "Winner")
        pom_info = data.get("player_of_match") if isinstance(data.get("player_of_match"), dict) else {}
        pom_name = pom_info.get("player_name", "N/A")
        innings_list = data.get("innings") if isinstance(data.get("innings"), list) else []

        lines = [
            f"Match Summary (Match {m_id}, {dt}):",
            f"{t1_name} vs {t2_name} at {v_name}",
            f"Result: {margin_text} (Winner: {winner_name})",
            f"Player of the Match: {pom_name}"
        ]
        if innings_list:
            lines.append("Innings:")
            for inn in innings_list:
                if not isinstance(inn, dict):
                    continue
                bat = inn.get("batting_team", "Team")
                score = inn.get("score", "")
                overs = inn.get("overs", "")
                lines.append(f"- {bat}: {score} ({overs} overs)")
        return "\n".join(lines)

    def _format_match_scorecard(self, data: Any) -> str:
        if not isinstance(data, dict):
            raise FormattingError("Expected dict result for MATCH_SCORECARD.")
        m_id = data.get("match_id", "N/A")
        innings_list = data.get("innings") if isinstance(data.get("innings"), list) else []

        lines = [f"Match Scorecard (Match {m_id}):"]
        for inn in innings_list:
            if not isinstance(inn, dict):
                continue
            no = inn.get("innings_no", 1)
            bat_team = inn.get("batting_team", "Batting Team")
            score = inn.get("score", "")
            overs = inn.get("total_overs", "")
            lines.append(f"\nInnings {no}: {bat_team} ({score}, {overs} overs)")

            bat_card = inn.get("batting_card") if isinstance(inn.get("batting_card"), list) else []
            if bat_card:
                lines.append("Top batting:")
                for b in bat_card[:5]:
                    if not isinstance(b, dict):
                        continue
                    name = b.get("batter_name", "Batter")
                    runs = b.get("runs", 0)
                    balls = b.get("balls", 0)
                    dism = b.get("dismissal", "not out")
                    lines.append(f"- {name}: {runs} ({balls}b) - {dism}")

            bowl_card = inn.get("bowling_card") if isinstance(inn.get("bowling_card"), list) else []
            if bowl_card:
                lines.append("Top bowling:")
                for bo in bowl_card[:5]:
                    if not isinstance(bo, dict):
                        continue
                    name = bo.get("bowler_name", "Bowler")
                    o = bo.get("overs", 0)
                    m = bo.get("maidens", 0)
                    r = bo.get("runs", 0)
                    w = bo.get("wickets", 0)
                    econ = bo.get("economy", 0.0)
                    lines.append(f"- {name}: {o}-{m}-{r}-{w} (Econ: {econ})")

        return "\n".join(lines)
