from typing import List, Dict, Any
from analytics.database import get_connection
from analytics.utils import resolve_player_id, PlayerNotFoundError, _get_player_name


def search_players(name: str) -> List[Dict[str, Any]]:
    """
    Search for players whose names contain the query (case-insensitive).
    
    Args:
        name (str): The search query.
        
    Returns:
        List[Dict[str, Any]]: List of matching players with player_id, registry_id, player_name.
    """
    if not name:
        return []
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT player_id, registry_id, player_name FROM players WHERE player_name LIKE ? ORDER BY player_name",
            (f"%{name}%",),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_player(player_name: str) -> Dict[str, Any]:
    """
    Retrieve player details by name.
    
    Args:
        player_name (str): The player's name (resolves via heuristics).
        
    Returns:
        Dict[str, Any]: Player record dictionary.
        
    Raises:
        PlayerNotFoundError: If the player does not exist.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT player_id, registry_id, player_name FROM players WHERE player_id = ?",
            (player_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise PlayerNotFoundError(f"Player '{player_name}' not found.")
        return dict(row)
    finally:
        conn.close()


def get_player_career(player_name: str) -> Dict[str, Any]:
    """
    Retrieve career summary statistics for a player (batting, bowling, fielding).
    
    Args:
        player_name (str): The player's name.
        
    Returns:
        Dict[str, Any]: Career statistics dictionary.
        
    Raises:
        PlayerNotFoundError: If the player does not exist.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        
        # Get basic details
        actual_name = _get_player_name(conn, player_id)
        
        # Get precomputed career stats
        cursor.execute(
            "SELECT * FROM player_career WHERE player_id = ?",
            (player_id,),
        )
        c_row = cursor.fetchone()
        
        # If no career stats found, return basic details with empty stats
        if not c_row:
            return {
                "player_id": player_id,
                "player_name": actual_name,
                "matches": 0,
                "batting_innings": 0,
                "batting_runs": 0,
                "batting_balls": 0,
                "fours": 0,
                "sixes": 0,
                "hundreds": 0,
                "fifties": 0,
                "batting_average": 0.0,
                "batting_strike_rate": 0.0,
                "wickets": 0,
                "bowling_runs": 0,
                "bowling_balls": 0,
                "bowling_average": None,
                "bowling_economy": 0.0,
                "bowling_strike_rate": None,
                "catches": 0,
                "run_outs": 0,
            }
            
        career = dict(c_row)
        
        # Calculate batting average: runs / dismissals
        cursor.execute(
            """
            SELECT COUNT(*) FROM batting_innings 
            WHERE batter_id = ? 
              AND dismissal_type IS NOT NULL 
              AND dismissal_type != 'retired hurt'
            """,
            (player_id,),
        )
        dismissals = cursor.fetchone()[0]
        
        runs = career.get("runs") or 0
        bat_innings = career.get("innings") or 0
        balls_faced = career.get("balls") or 0
        
        if dismissals > 0:
            batting_avg = round(runs / dismissals, 2)
        else:
            batting_avg = float(runs) if bat_innings > 0 else 0.0
            
        # Batting strike rate: (runs / balls_faced) * 100
        batting_sr = round((runs / balls_faced) * 100, 2) if balls_faced > 0 else 0.0
        
        # Fetch bowling details (runs conceded and balls bowled)
        cursor.execute(
            """
            SELECT 
                COALESCE(SUM(runs), 0) as total_runs,
                COALESCE(SUM(CAST(overs AS INTEGER) * 6 + ROUND((overs - CAST(overs AS INTEGER)) * 10)), 0) as total_balls,
                COALESCE(COUNT(*), 0) as total_bowl_innings
            FROM bowling_innings
            WHERE bowler_id = ?
            """,
            (player_id,),
        )
        bowling_agg = cursor.fetchone()
        
        bowl_runs = bowling_agg["total_runs"]
        bowl_balls = int(bowling_agg["total_balls"])
        wickets = career.get("wickets") or 0
        
        # Calculate bowling average: runs / wickets
        bowling_avg = round(bowl_runs / wickets, 2) if wickets > 0 else None
        
        # Calculate bowling economy: (runs / (balls / 6))
        bowling_econ = round(bowl_runs / (bowl_balls / 6.0), 2) if bowl_balls > 0 else 0.0
        
        # Calculate bowling strike rate: balls / wickets
        bowling_sr = round(bowl_balls / wickets, 2) if wickets > 0 else None
        
        return {
            "player_id": player_id,
            "player_name": actual_name,
            "matches": career.get("matches") or 0,
            "batting_innings": bat_innings,
            "batting_runs": runs,
            "batting_balls": balls_faced,
            "fours": career.get("fours") or 0,
            "sixes": career.get("sixes") or 0,
            "hundreds": career.get("hundreds") or 0,
            "fifties": career.get("fifties") or 0,
            "batting_average": batting_avg,
            "batting_strike_rate": batting_sr,
            "wickets": wickets,
            "bowling_runs": bowl_runs,
            "bowling_balls": bowl_balls,
            "bowling_average": bowling_avg,
            "bowling_economy": bowling_econ,
            "bowling_strike_rate": bowling_sr,
            "catches": career.get("catches") or 0,
            "run_outs": career.get("run_outs") or 0,
        }
    finally:
        conn.close()


def get_player_match_history(player_name: str) -> List[Dict[str, Any]]:
    """
    Get chronological match history of a player.
    
    Args:
        player_name (str): The player's name.
        
    Returns:
        List[Dict[str, Any]]: Chronological list of match history dictionaries.
    """
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                m.match_id,
                m.season,
                m.date,
                m.match_type,
                v.venue_name,
                v.city,
                t_player.team_name AS player_team,
                t_opp.team_name AS opponent_team,
                t_winner.team_name AS winner_team,
                m.result,
                m.result_margin,
                pxi.is_captain,
                pxi.is_keeper
            FROM playing_xi pxi
            JOIN matches m ON pxi.match_id = m.match_id
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            LEFT JOIN teams t_player ON pxi.team_id = t_player.team_id
            LEFT JOIN teams t_opp ON (
                CASE 
                    WHEN m.team1_id = pxi.team_id THEN m.team2_id 
                    ELSE m.team1_id 
                END
            ) = t_opp.team_id
            LEFT JOIN teams t_winner ON m.winner_team_id = t_winner.team_id
            WHERE pxi.player_id = ?
            ORDER BY m.date DESC, m.match_id DESC
            """,
            (player_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_player_last_n_matches(player_name: str, n: int) -> List[Dict[str, Any]]:
    """
    Get the last N matches played by a player.
    
    Args:
        player_name (str): The player's name.
        n (int): Number of matches to retrieve.
        
    Returns:
        List[Dict[str, Any]]: List of at most N match history dictionaries.
    """
    if n <= 0:
        return []
        
    conn = get_connection()
    try:
        player_id = resolve_player_id(conn, player_name)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                m.match_id,
                m.season,
                m.date,
                m.match_type,
                v.venue_name,
                v.city,
                t_player.team_name AS player_team,
                t_opp.team_name AS opponent_team,
                t_winner.team_name AS winner_team,
                m.result,
                m.result_margin,
                pxi.is_captain,
                pxi.is_keeper
            FROM playing_xi pxi
            JOIN matches m ON pxi.match_id = m.match_id
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            LEFT JOIN teams t_player ON pxi.team_id = t_player.team_id
            LEFT JOIN teams t_opp ON (
                CASE 
                    WHEN m.team1_id = pxi.team_id THEN m.team2_id 
                    ELSE m.team1_id 
                END
            ) = t_opp.team_id
            LEFT JOIN teams t_winner ON m.winner_team_id = t_winner.team_id
            WHERE pxi.player_id = ?
            ORDER BY m.date DESC, m.match_id DESC
            LIMIT ?
            """,
            (player_id, n),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
