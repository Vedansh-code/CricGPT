from typing import List, Dict, Any
from analytics.database import get_connection
from analytics.utils import resolve_player_id, PlayerNotFoundError, _get_player_name


def top_run_scorers(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve top run scorers overall.
    
    Args:
        limit (int): Maximum number of top scorers to retrieve.
        
    Returns:
        List[Dict[str, Any]]: List of top run scorers.
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
                pc.runs,
                pc.matches,
                pc.innings,
                pc.balls,
                pc.fours,
                pc.sixes,
                COALESCE(d.dismissals, 0) as dismissals
            FROM player_career pc
            JOIN players p ON pc.player_id = p.player_id
            LEFT JOIN (
                SELECT batter_id, COUNT(*) as dismissals
                FROM batting_innings
                WHERE dismissal_type IS NOT NULL AND dismissal_type != 'retired hurt'
                GROUP BY batter_id
            ) d ON pc.player_id = d.batter_id
            ORDER BY pc.runs DESC
            LIMIT ?
            """,
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            runs = row["runs"] or 0
            innings = row["innings"] or 0
            balls = row["balls"] or 0
            dismissals = row["dismissals"] or 0

            # Calculate average
            if dismissals > 0:
                avg = round(runs / dismissals, 2)
            else:
                avg = float(runs) if innings > 0 else 0.0

            # Calculate strike rate
            sr = round((runs / balls) * 100, 2) if balls > 0 else 0.0

            d_dict = dict(row)
            d_dict["average"] = avg
            d_dict["strike_rate"] = sr
            results.append(d_dict)
            
        return results
    finally:
        conn.close()


def highest_individual_scores(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve highest individual scores in a single innings.
    
    Args:
        limit (int): Maximum number of scores to retrieve.
        
    Returns:
        List[Dict[str, Any]]: List of highest individual scores.
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
                bi.runs,
                bi.balls,
                bi.fours,
                bi.sixes,
                bi.strike_rate,
                bi.dismissal_type,
                p.player_name,
                t_bat.team_name AS batting_team,
                t_bowl.team_name AS bowling_team,
                m.date,
                m.season
            FROM batting_innings bi
            JOIN players p ON bi.batter_id = p.player_id
            JOIN matches m ON bi.match_id = m.match_id
            JOIN innings i ON bi.match_id = i.match_id AND bi.innings_id = i.innings_id
            JOIN teams t_bat ON i.batting_team_id = t_bat.team_id
            JOIN teams t_bowl ON i.bowling_team_id = t_bowl.team_id
            ORDER BY bi.runs DESC, bi.balls ASC
            LIMIT ?
            """,
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            d_dict = dict(row)
            d_dict["dismissal_type"] = row["dismissal_type"] if row["dismissal_type"] else "not out"
            results.append(d_dict)
        return results
    finally:
        conn.close()


def batting_average(player_name: str) -> Dict[str, Any]:
    """
    Get batting average statistics for a player.
    
    Args:
        player_name (str): The player's name.
        
    Returns:
        Dict[str, Any]: Batting average details.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                SUM(runs) as total_runs,
                COUNT(CASE WHEN dismissal_type IS NOT NULL AND dismissal_type != 'retired hurt' THEN 1 END) as dismissals,
                COUNT(innings_id) as innings
            FROM batting_innings
            WHERE batter_id = ?
            """,
            (player_id,),
        )
        row = cursor.fetchone()
        
        # Get standard player details
        actual_name = _get_player_name(conn, player_id)
        
        runs = row["total_runs"] or 0
        innings = row["innings"] or 0
        dismissals = row["dismissals"] or 0
        
        if innings == 0:
            avg = 0.0
        elif dismissals == 0:
            avg = float(runs)
        else:
            avg = round(runs / dismissals, 2)
            
        return {
            "player_name": actual_name,
            "runs": runs,
            "innings": innings,
            "dismissals": dismissals,
            "batting_average": avg,
        }
    finally:
        conn.close()


def strike_rate(player_name: str) -> Dict[str, Any]:
    """
    Get strike rate statistics for a player.
    
    Args:
        player_name (str): The player's name.
        
    Returns:
        Dict[str, Any]: Strike rate details.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                SUM(runs) as total_runs,
                SUM(balls) as total_balls,
                COUNT(innings_id) as innings
            FROM batting_innings
            WHERE batter_id = ?
            """,
            (player_id,),
        )
        row = cursor.fetchone()
        
        # Get standard player details
        actual_name = _get_player_name(conn, player_id)
        
        runs = row["total_runs"] or 0
        balls = row["total_balls"] or 0
        innings = row["innings"] or 0
        
        sr = round((runs / balls) * 100, 2) if balls > 0 else 0.0
        
        return {
            "player_name": actual_name,
            "runs": runs,
            "balls": balls,
            "innings": innings,
            "strike_rate": sr,
        }
    finally:
        conn.close()


def boundary_percentage(player_name: str) -> Dict[str, Any]:
    """
    Get boundary statistics and percentage for a player.
    
    Args:
        player_name (str): The player's name.
        
    Returns:
        Dict[str, Any]: Boundary percentages.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                SUM(runs) as total_runs,
                SUM(balls) as total_balls,
                SUM(fours) as total_fours,
                SUM(sixes) as total_sixes,
                COUNT(innings_id) as innings
            FROM batting_innings
            WHERE batter_id = ?
            """,
            (player_id,),
        )
        row = cursor.fetchone()
        
        # Get standard player details
        actual_name = _get_player_name(conn, player_id)
        
        runs = row["total_runs"] or 0
        balls = row["total_balls"] or 0
        innings = row["innings"] or 0
        fours = row["total_fours"] or 0
        sixes = row["total_sixes"] or 0
        
        boundary_runs = (fours * 4) + (sixes * 6)
        boundary_balls = fours + sixes
        
        boundary_runs_pct = round((boundary_runs / runs) * 100, 2) if runs > 0 else 0.0
        boundary_balls_pct = round((boundary_balls / balls) * 100, 2) if balls > 0 else 0.0
        
        return {
            "player_name": actual_name,
            "runs": runs,
            "balls": balls,
            "innings": innings,
            "fours": fours,
            "sixes": sixes,
            "boundary_runs": boundary_runs,
            "boundary_runs_percentage": boundary_runs_pct,
            "boundary_balls_percentage": boundary_balls_pct,
        }
    finally:
        conn.close()
