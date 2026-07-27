from typing import Dict, Any
from analytics.database import get_connection
from analytics.utils import resolve_venue_id, VenueNotFoundError


def venue_summary(venue_name: str) -> Dict[str, Any]:
    """
    Retrieve statistics summary for a given venue.
    
    Args:
        venue_name (str): The venue name.
        
    Returns:
        Dict[str, Any]: Detailed statistics for the venue.
        
    Raises:
        VenueNotFoundError: If the venue name cannot be resolved.
    """
    conn = get_connection()
    try:
        venue_id = resolve_venue_id(conn, venue_name)
        cursor = conn.cursor()
        
        # Get actual venue name and city
        cursor.execute(
            "SELECT venue_name, city FROM venues WHERE venue_id = ?",
            (venue_id,),
        )
        v_row = cursor.fetchone()
        actual_name = v_row["venue_name"]
        city = v_row["city"]
        
        # Get venue precomputed statistics
        cursor.execute(
            """
            SELECT 
                matches, 
                avg_first_innings, 
                avg_second_innings, 
                highest_score, 
                lowest_score, 
                successful_chases, 
                bat_first_wins, 
                bowl_first_wins
            FROM venue_statistics
            WHERE venue_id = ?
            """,
            (venue_id,),
        )
        stats_row = cursor.fetchone()
        
        if not stats_row:
            return {
                "venue_name": actual_name,
                "city": city,
                "matches_played": 0,
                "avg_first_innings_score": 0.0,
                "avg_second_innings_score": 0.0,
                "highest_score": 0,
                "lowest_score": 0,
                "successful_chases": 0,
                "bat_first_wins": 0,
                "bowl_first_wins": 0,
            }
            
        stats = dict(stats_row)
        
        return {
            "venue_name": actual_name,
            "city": city,
            "matches_played": stats["matches"] or 0,
            "avg_first_innings_score": round(stats["avg_first_innings"], 2) if stats["avg_first_innings"] else 0.0,
            "avg_second_innings_score": round(stats["avg_second_innings"], 2) if stats["avg_second_innings"] else 0.0,
            "highest_score": stats["highest_score"] or 0,
            "lowest_score": stats["lowest_score"] or 0,
            "successful_chases": stats["successful_chases"] or 0,
            "bat_first_wins": stats["bat_first_wins"] or 0,
            "bowl_first_wins": stats["bowl_first_wins"] or 0,
        }
    finally:
        conn.close()
