from typing import Dict, Any
from analytics.database import get_connection
from analytics.utils import resolve_player_id, PlayerNotFoundError


def get_batter_vs_bowler(batter_name: str, bowler_name: str) -> Dict[str, Any]:
    """
    Retrieve player-versus-player matchup statistics.
    
    Args:
        batter_name (str): The batter's name.
        bowler_name (str): The bowler's name.
        
    Returns:
        Dict[str, Any]: Detailed matchup statistics.
    """
    conn = get_connection()
    try:
        batter_id = resolve_player_id(conn, batter_name)
        bowler_id = resolve_player_id(conn, bowler_name)
        
        # Get standard player names
        cursor = conn.cursor()
        cursor.execute("SELECT player_name FROM players WHERE player_id = ?", (batter_id,))
        bat_row = cursor.fetchone()
        batter_actual = bat_row["player_name"]
        
        cursor.execute("SELECT player_name FROM players WHERE player_id = ?", (bowler_id,))
        bowl_row = cursor.fetchone()
        bowler_actual = bowl_row["player_name"]
        
        cursor.execute(
            """
            SELECT balls, runs, dots, fours, sixes, dismissals 
            FROM player_ball_matchup
            WHERE batter_id = ? AND bowler_id = ?
            """,
            (batter_id, bowler_id),
        )
        row = cursor.fetchone()
        
        if not row:
            return {
                "batter_name": batter_actual,
                "bowler_name": bowler_actual,
                "balls": 0,
                "runs": 0,
                "dots": 0,
                "fours": 0,
                "sixes": 0,
                "dismissals": 0,
                "strike_rate": 0.0,
                "average": 0.0,
            }
            
        balls = row["balls"] or 0
        runs = row["runs"] or 0
        dots = row["dots"] or 0
        fours = row["fours"] or 0
        sixes = row["sixes"] or 0
        dismissals = row["dismissals"] or 0
        
        sr = round((runs / balls) * 100, 2) if balls > 0 else 0.0
        
        if dismissals > 0:
            avg = round(runs / dismissals, 2)
        else:
            avg = float(runs) if balls > 0 else 0.0
            
        return {
            "batter_name": batter_actual,
            "bowler_name": bowler_actual,
            "balls": balls,
            "runs": runs,
            "dots": dots,
            "fours": fours,
            "sixes": sixes,
            "dismissals": dismissals,
            "strike_rate": sr,
            "average": avg,
        }
    finally:
        conn.close()
