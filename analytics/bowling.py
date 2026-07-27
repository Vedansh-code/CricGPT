from typing import List, Dict, Any
from analytics.database import get_connection
from analytics.utils import resolve_player_id, PlayerNotFoundError, format_overs, _get_player_name


def top_wicket_takers(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve top wicket takers overall.
    
    Args:
        limit (int): Maximum number of wicket takers to retrieve.
        
    Returns:
        List[Dict[str, Any]]: List of top wicket takers.
    """
    if limit <= 0:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                p.player_id,
                p.player_name,
                pc.wickets,
                pc.matches,
                COALESCE(bi.total_runs, 0) as runs_conceded,
                COALESCE(bi.total_balls, 0) as total_balls
            FROM player_career pc
            JOIN players p ON pc.player_id = p.player_id
            LEFT JOIN (
                SELECT 
                    bowler_id,
                    SUM(runs) as total_runs,
                    SUM(CAST(overs AS INTEGER) * 6 + ROUND((overs - CAST(overs AS INTEGER)) * 10)) as total_balls
                FROM bowling_innings
                GROUP BY bowler_id
            ) bi ON pc.player_id = bi.bowler_id
            ORDER BY pc.wickets DESC, runs_conceded ASC
            LIMIT ?
            """,
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            wickets = row["wickets"] or 0
            runs = row["runs_conceded"] or 0
            balls = int(row["total_balls"]) or 0
            
            # Overs format: X.Y
            overs = float(f"{balls // 6}.{balls % 6}")
            
            economy = round(runs / (balls / 6.0), 2) if balls > 0 else 0.0
            average = round(runs / wickets, 2) if wickets > 0 else None
            strike_rate = round(balls / wickets, 2) if wickets > 0 else None
            
            d_dict = dict(row)
            d_dict["total_balls"] = balls
            d_dict["overs"] = overs
            d_dict["economy_rate"] = economy
            d_dict["bowling_average"] = average
            d_dict["strike_rate"] = strike_rate
            results.append(d_dict)
            
        return results
    finally:
        conn.close()


def economy_rate(player_name: str) -> Dict[str, Any]:
    """
    Get bowling economy statistics for a player.
    
    Args:
        player_name (str): The player's name.
        
    Returns:
        Dict[str, Any]: Bowling economy rate details.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                SUM(runs) as total_runs,
                SUM(CAST(overs AS INTEGER) * 6 + ROUND((overs - CAST(overs AS INTEGER)) * 10)) as total_balls,
                COUNT(innings_id) as innings
            FROM bowling_innings
            WHERE bowler_id = ?
            """,
            (player_id,),
        )
        row = cursor.fetchone()
        
        # Get standard player details
        actual_name = _get_player_name(conn, player_id)
        
        runs = row["total_runs"] or 0
        balls = int(row["total_balls"]) if row["total_balls"] else 0
        innings = row["innings"] or 0
        
        econ = round(runs / (balls / 6.0), 2) if balls > 0 else 0.0
        overs = float(f"{balls // 6}.{balls % 6}")
        
        return {
            "player_name": actual_name,
            "runs_conceded": runs,
            "balls_bowled": balls,
            "overs": overs,
            "innings": innings,
            "economy_rate": econ,
        }
    finally:
        conn.close()


def best_bowling_figures(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve best individual bowling figures in a single innings.
    
    Args:
        limit (int): Maximum number of figures to retrieve.
        
    Returns:
        List[Dict[str, Any]]: List of best bowling figures.
    """
    if limit <= 0:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                bi.match_id,
                bi.overs,
                bi.maidens,
                bi.runs,
                bi.wickets,
                bi.economy,
                p.player_name,
                t_bowl.team_name AS bowling_team,
                t_bat.team_name AS batting_team,
                m.date,
                m.season
            FROM bowling_innings bi
            JOIN players p ON bi.bowler_id = p.player_id
            JOIN matches m ON bi.match_id = m.match_id
            JOIN innings i ON bi.match_id = i.match_id AND bi.innings_id = i.innings_id
            JOIN teams t_bowl ON i.bowling_team_id = t_bowl.team_id
            JOIN teams t_bat ON i.batting_team_id = t_bat.team_id
            ORDER BY bi.wickets DESC, bi.runs ASC
            LIMIT ?
            """,
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            d["overs"] = format_overs(row["overs"])
            results.append(d)
        return results
    finally:
        conn.close()
