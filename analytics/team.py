from typing import Dict, Any, List
from analytics.database import get_connection
from analytics.utils import resolve_team_id, TeamNotFoundError


def get_team_record(team_name: str) -> Dict[str, Any]:
    """
    Retrieve statistics for a team.
    
    Args:
        team_name (str): The team's name or abbreviation.
        
    Returns:
        Dict[str, Any]: Detailed stats for the team.
        
    Raises:
        TeamNotFoundError: If the team name cannot be resolved.
    """
    conn = get_connection()
    try:
        team_id = resolve_team_id(conn, team_name)
        cursor = conn.cursor()
        
        # Get team name
        cursor.execute("SELECT team_name FROM teams WHERE team_id = ?", (team_id,))
        t_row = cursor.fetchone()
        actual_name = t_row["team_name"]
        
        # Fetch team stats
        cursor.execute(
            """
            SELECT matches, wins, losses, ties, avg_score, avg_conceded 
            FROM team_statistics 
            WHERE team_id = ?
            """,
            (team_id,),
        )
        stats_row = cursor.fetchone()
        
        if not stats_row:
            return {
                "team_name": actual_name,
                "matches": 0,
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "win_percentage": 0.0,
                "avg_score": 0.0,
                "avg_conceded": 0.0,
            }
            
        stats = dict(stats_row)
        matches = stats["matches"] or 0
        wins = stats["wins"] or 0
        
        win_pct = round((wins / matches) * 100, 2) if matches > 0 else 0.0
        
        return {
            "team_name": actual_name,
            "matches": matches,
            "wins": wins,
            "losses": stats["losses"] or 0,
            "ties": stats["ties"] or 0,
            "win_percentage": win_pct,
            "avg_score": round(stats["avg_score"], 2) if stats["avg_score"] else 0.0,
            "avg_conceded": round(stats["avg_conceded"], 2) if stats["avg_conceded"] else 0.0,
        }
    finally:
        conn.close()


def head_to_head(team1: str, team2: str) -> Dict[str, Any]:
    """
    Retrieve head-to-head match details between two teams.
    
    Args:
        team1 (str): The first team's name or abbreviation.
        team2 (str): The second team's name or abbreviation.
        
    Returns:
        Dict[str, Any]: Head-to-head performance record.
        
    Raises:
        TeamNotFoundError: If either team name cannot be resolved.
    """
    conn = get_connection()
    try:
        t1_id = resolve_team_id(conn, team1)
        t2_id = resolve_team_id(conn, team2)
        
        cursor = conn.cursor()
        
        # Get actual team names
        cursor.execute("SELECT team_name FROM teams WHERE team_id = ?", (t1_id,))
        team1_actual = cursor.fetchone()["team_name"]
        
        cursor.execute("SELECT team_name FROM teams WHERE team_id = ?", (t2_id,))
        team2_actual = cursor.fetchone()["team_name"]
        
        # Get head-to-head statistics
        cursor.execute(
            """
            SELECT 
                COUNT(*) as matches_played,
                SUM(CASE WHEN winner_team_id = :t1 THEN 1 ELSE 0 END) as team1_wins,
                SUM(CASE WHEN winner_team_id = :t2 THEN 1 ELSE 0 END) as team2_wins,
                SUM(CASE WHEN winner_team_id IS NULL OR (winner_team_id != :t1 AND winner_team_id != :t2) THEN 1 ELSE 0 END) as ties_no_result
            FROM matches
            WHERE (team1_id = :t1 AND team2_id = :t2) OR (team1_id = :t2 AND team2_id = :t1)
            """,
            {"t1": t1_id, "t2": t2_id},
        )
        summary = dict(cursor.fetchone())
        
        # Get 5 recent matches between them
        cursor.execute(
            """
            SELECT 
                m.match_id,
                m.season,
                m.date,
                v.venue_name,
                v.city,
                tw.team_name AS winner_team,
                m.result,
                m.result_margin
            FROM matches m
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            LEFT JOIN teams tw ON m.winner_team_id = tw.team_id
            WHERE (m.team1_id = :t1 AND m.team2_id = :t2) OR (m.team1_id = :t2 AND m.team2_id = :t1)
            ORDER BY m.date DESC, m.match_id DESC
            LIMIT 5
            """,
            {"t1": t1_id, "t2": t2_id},
        )
        recent_rows = cursor.fetchall()
        
        recent_matches = []
        for r in recent_rows:
            venue_name = r["venue_name"]
            city = r["city"]
            if city and city.lower() not in venue_name.lower():
                venue_str = f"{venue_name}, {city}"
            else:
                venue_str = venue_name
            recent_matches.append({
                "match_id": r["match_id"],
                "season": r["season"],
                "date": r["date"],
                "venue": venue_str,
                "winner": r["winner_team"],
                "result": r["result"],
                "margin": r["result_margin"],
            })
            
        return {
            "team1": team1_actual,
            "team2": team2_actual,
            "matches_played": summary["matches_played"] or 0,
            "team1_wins": summary["team1_wins"] or 0,
            "team2_wins": summary["team2_wins"] or 0,
            "ties_or_no_results": summary["ties_no_result"] or 0,
            "recent_matches": recent_matches,
        }
    finally:
        conn.close()
