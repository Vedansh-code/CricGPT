from typing import Dict, Any, List
from analytics.database import get_connection
from analytics.utils import validate_match_id, MatchNotFoundError, format_overs


def format_result(result_type: str, margin: Any) -> str:
    """
    Format the match result margin into a reader-friendly string.
    e.g. "Won by X runs", "Won by X wickets", "Tie", "No Result"
    """
    if not result_type:
        return "No Result"
        
    res_lower = result_type.lower()
    if res_lower == "runs":
        return f"Won by {margin} runs"
    elif res_lower == "wickets":
        return f"Won by {margin} wickets"
    elif res_lower == "tie":
        return "Match Tied"
    elif res_lower == "no result" or res_lower == "nr":
        return "No Result"
        
    if margin:
        return f"Won by {margin} {result_type}"
    return result_type


def _calculate_run_rate(runs: int, decimal_overs: float) -> float:
    """Calculate run rate based on runs and decimal overs (e.g. 19.4 -> 19.66667 overs)."""
    if not decimal_overs or decimal_overs <= 0:
        return 0.0
    whole_overs = int(decimal_overs)
    balls = round((decimal_overs - whole_overs) * 6)
    if balls == 6:
        whole_overs += 1
        balls = 0
    total_balls = whole_overs * 6 + balls
    if total_balls == 0:
        return 0.0
    return round(runs / (total_balls / 6), 2)


def get_match_summary(match_id: int) -> Dict[str, Any]:
    """
    Retrieve a comprehensive summary of a match.
    
    Args:
        match_id (int): The match ID to query.
        
    Returns:
        Dict[str, Any]: A dictionary containing match summary information.
        
    Raises:
        MatchNotFoundError: If the match ID does not exist.
    """
    conn = get_connection()
    try:
        validate_match_id(conn, match_id)
        cursor = conn.cursor()
        
        # Get match basic details
        cursor.execute(
            """
            SELECT 
                m.match_id,
                m.season,
                m.date,
                m.match_type,
                m.venue_id,
                v.venue_name,
                v.city,
                m.team1_id,
                t1.team_name AS team1,
                m.team2_id,
                t2.team_name AS team2,
                m.winner_team_id,
                tw.team_name AS winner,
                m.toss_winner_team_id,
                tt.team_name AS toss_winner,
                m.toss_decision,
                m.result,
                m.result_margin,
                m.player_of_match_id,
                pom.player_name AS player_of_match,
                m.overs,
                m.event_name,
                m.gender
            FROM matches m
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams tw ON m.winner_team_id = tw.team_id
            LEFT JOIN teams tt ON m.toss_winner_team_id = tt.team_id
            LEFT JOIN players pom ON m.player_of_match_id = pom.player_id
            WHERE m.match_id = ?
            """,
            (match_id,),
        )
        m_row = cursor.fetchone()
        if not m_row:
            raise MatchNotFoundError(f"Match ID '{match_id}' not found.")
            
        # Get innings brief summaries
        cursor.execute(
            """
            SELECT 
                i.innings_no,
                t_bat.team_name AS batting_team,
                t_bowl.team_name AS bowling_team,
                i.total_runs,
                i.total_wickets,
                i.total_overs
            FROM innings i
            JOIN teams t_bat ON i.batting_team_id = t_bat.team_id
            JOIN teams t_bowl ON i.bowling_team_id = t_bowl.team_id
            WHERE i.match_id = ?
            ORDER BY i.innings_no ASC
            """,
            (match_id,),
        )
        inn_rows = cursor.fetchall()
        
        match_info = dict(m_row)
        
        # Process innings summary
        innings_summary = []
        for inn in inn_rows:
            tot_runs = inn["total_runs"]
            tot_wkt = inn["total_wickets"]
            tot_overs = inn["total_overs"]
            run_rate = _calculate_run_rate(tot_runs, tot_overs)
            score_str = f"{tot_runs}/{tot_wkt}"
            innings_summary.append({
                "innings_no": inn["innings_no"],
                "batting_team": inn["batting_team"],
                "bowling_team": inn["bowling_team"],
                "runs": tot_runs,
                "wickets": tot_wkt,
                "overs": format_overs(tot_overs) if tot_overs is not None else None,
                "score": score_str,
                "run_rate": run_rate,
            })
        
        # Structure the returned dictionary
        return {
            "match_id": match_info["match_id"],
            "season": match_info["season"],
            "date": match_info["date"],
            "match_type": match_info["match_type"],
            "venue": {
                "venue_id": match_info["venue_id"],
                "venue_name": match_info["venue_name"],
                "city": match_info["city"],
            },
            "team1": {
                "team_id": match_info["team1_id"],
                "team_name": match_info["team1"],
            },
            "team2": {
                "team_id": match_info["team2_id"],
                "team_name": match_info["team2"],
            },
            "toss": {
                "winner": {
                    "team_id": match_info["toss_winner_team_id"],
                    "team_name": match_info["toss_winner"],
                } if match_info["toss_winner"] else None,
                "decision": match_info["toss_decision"],
            },
            "result": {
                "winner": {
                    "team_id": match_info["winner_team_id"],
                    "team_name": match_info["winner"],
                } if match_info["winner"] else None,
                "result_type": match_info["result"],
                "margin": match_info["result_margin"],
                "winning_margin_text": format_result(match_info["result"], match_info["result_margin"]),
            },
            "player_of_match": {
                "player_id": match_info["player_of_match_id"],
                "player_name": match_info["player_of_match"],
            } if match_info["player_of_match"] else None,
            "overs": format_overs(match_info["overs"]) if match_info["overs"] is not None else None,
            "event_name": match_info["event_name"],
            "gender": match_info["gender"],
            "innings": innings_summary,
        }
    finally:
        conn.close()


def get_scorecard(match_id: int) -> Dict[str, Any]:
    """
    Retrieve the full detailed scorecard for a match.
    
    Args:
        match_id (int): The match ID to query.
        
    Returns:
        Dict[str, Any]: Detailed innings-by-innings batting and bowling cards.
        
    Raises:
        MatchNotFoundError: If the match ID does not exist.
    """
    conn = get_connection()
    try:
        validate_match_id(conn, match_id)
        cursor = conn.cursor()
        
        # Get innings list
        cursor.execute(
            """
            SELECT 
                i.innings_id,
                i.innings_no,
                t_bat.team_name AS batting_team,
                t_bowl.team_name AS bowling_team,
                i.total_runs,
                i.total_wickets,
                i.total_overs
            FROM innings i
            JOIN teams t_bat ON i.batting_team_id = t_bat.team_id
            JOIN teams t_bowl ON i.bowling_team_id = t_bowl.team_id
            WHERE i.match_id = ?
            ORDER BY i.innings_no ASC
            """,
            (match_id,),
        )
        innings_list = cursor.fetchall()
        
        innings_cards = []
        for inn in innings_list:
            inn_id = inn["innings_id"]
            
            # Fetch batting performances, ordered by order of appearance at crease
            # Includes left joins to deliveries (where batter got dismissed) to get fielder names
            cursor.execute(
                """
                SELECT 
                    bi.batter_id,
                    p.player_name AS batter_name,
                    bi.runs,
                    bi.balls,
                    bi.fours,
                    bi.sixes,
                    bi.strike_rate,
                    bi.dismissal_type,
                    p_bowl.player_name AS dismissed_by,
                    f1.player_name AS fielder1_name,
                    f2.player_name AS fielder2_name,
                    COALESCE(MIN(d.ball_sequence), 9999) as batting_order
                FROM batting_innings bi
                JOIN players p ON bi.batter_id = p.player_id
                LEFT JOIN players p_bowl ON bi.dismissed_by = p_bowl.player_id
                LEFT JOIN deliveries d ON bi.match_id = d.match_id 
                                      AND bi.innings_id = d.innings_id 
                                      AND bi.batter_id = d.batter_id
                LEFT JOIN deliveries dw ON bi.match_id = dw.match_id 
                                       AND bi.innings_id = dw.innings_id 
                                       AND bi.batter_id = dw.player_out_id
                                       AND dw.is_wicket = 1
                LEFT JOIN players f1 ON dw.fielder1_id = f1.player_id
                LEFT JOIN players f2 ON dw.fielder2_id = f2.player_id
                WHERE bi.match_id = ? AND bi.innings_id = ?
                GROUP BY bi.batter_id
                ORDER BY batting_order ASC
                """,
                (match_id, inn_id),
            )
            batting_rows = cursor.fetchall()
            
            batting_card = []
            for bat in batting_rows:
                fielders = []
                if bat["fielder1_name"]:
                    fielders.append(bat["fielder1_name"])
                if bat["fielder2_name"]:
                    fielders.append(bat["fielder2_name"])
                batting_card.append({
                    "batter_name": bat["batter_name"],
                    "runs": bat["runs"],
                    "balls": bat["balls"],
                    "fours": bat["fours"],
                    "sixes": bat["sixes"],
                    "strike_rate": bat["strike_rate"],
                    "dismissal": bat["dismissal_type"] if bat["dismissal_type"] else "not out",
                    "dismissed_by": bat["dismissed_by"],
                    "fielders": fielders,
                })
            
            # Fetch bowling performances, ordered by order of first ball sequence
            cursor.execute(
                """
                SELECT 
                    bo.bowler_id,
                    p.player_name AS bowler_name,
                    bo.overs,
                    bo.maidens,
                    bo.runs,
                    bo.wickets,
                    bo.economy,
                    COALESCE(MIN(d.ball_sequence), 9999) as bowling_order
                FROM bowling_innings bo
                JOIN players p ON bo.bowler_id = p.player_id
                LEFT JOIN deliveries d ON bo.match_id = d.match_id 
                                      AND bo.innings_id = d.innings_id 
                                      AND bo.bowler_id = d.bowler_id
                WHERE bo.match_id = ? AND bo.innings_id = ?
                GROUP BY bo.bowler_id
                ORDER BY bowling_order ASC
                """,
                (match_id, inn_id),
            )
            bowling_rows = cursor.fetchall()
            
            bowling_card = []
            for bowl in bowling_rows:
                bowling_card.append({
                    "bowler_name": bowl["bowler_name"],
                    "overs": format_overs(bowl["overs"]) if bowl["overs"] is not None else None,
                    "maidens": bowl["maidens"],
                    "runs": bowl["runs"],
                    "wickets": bowl["wickets"],
                    "economy": bowl["economy"],
                })
            
            # Get expanded extras from deliveries
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(runs_extras), 0) as total,
                    COALESCE(SUM(CASE WHEN extras_type = 'wides' THEN runs_extras ELSE 0 END), 0) as wides,
                    COALESCE(SUM(CASE WHEN extras_type = 'noballs' THEN runs_extras ELSE 0 END), 0) as no_balls,
                    COALESCE(SUM(CASE WHEN extras_type = 'byes' THEN runs_extras ELSE 0 END), 0) as byes,
                    COALESCE(SUM(CASE WHEN extras_type = 'legbyes' THEN runs_extras ELSE 0 END), 0) as leg_byes
                FROM deliveries 
                WHERE match_id = ? AND innings_id = ?
                """,
                (match_id, inn_id),
            )
            extras_row = dict(cursor.fetchone())
            
            tot_runs = inn["total_runs"]
            tot_wkt = inn["total_wickets"]
            tot_overs = inn["total_overs"]
            run_rate = _calculate_run_rate(tot_runs, tot_overs)
            score_str = f"{tot_runs}/{tot_wkt}"
            
            innings_cards.append({
                "innings_no": inn["innings_no"],
                "batting_team": inn["batting_team"],
                "bowling_team": inn["bowling_team"],
                "batting_card": batting_card,
                "bowling_card": bowling_card,
                "total_runs": tot_runs,
                "total_wickets": tot_wkt,
                "total_overs": format_overs(tot_overs) if tot_overs is not None else None,
                "score": score_str,
                "run_rate": run_rate,
                "extras": {
                    "total": extras_row["total"],
                    "wides": extras_row["wides"],
                    "no_balls": extras_row["no_balls"],
                    "byes": extras_row["byes"],
                    "leg_byes": extras_row["leg_byes"],
                },
            })
            
        return {
            "match_id": match_id,
            "innings": innings_cards,
        }
    finally:
        conn.close()
