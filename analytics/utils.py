import sqlite3


class CricGPTAnalyticsError(Exception):
    """Base exception class for all CricGPT Analytics SDK errors."""
    pass


class PlayerNotFoundError(CricGPTAnalyticsError):
    """Raised when a player cannot be found in the database."""
    pass


class TeamNotFoundError(CricGPTAnalyticsError):
    """Raised when a team cannot be found in the database."""
    pass


class VenueNotFoundError(CricGPTAnalyticsError):
    """Raised when a venue cannot be found in the database."""
    pass


class MatchNotFoundError(CricGPTAnalyticsError):
    """Raised when a match cannot be found in the database."""
    pass


class AmbiguousMatchError(CricGPTAnalyticsError):
    """Raised when a query matches multiple entities in the database."""
    pass


# Mapping of common team abbreviations to their official database names
TEAM_ABBREVIATIONS = {
    "csk": "Chennai Super Kings",
    "mi": "Mumbai Indians",
    "rcb": "Royal Challengers Bangalore",
    "kkr": "Kolkata Knight Riders",
    "srh": "Sunrisers Hyderabad",
    "dc": "Delhi Capitals",
    "dd": "Delhi Daredevils",
    "kxip": "Kings XI Punjab",
    "pbks": "Punjab Kings",
    "rr": "Rajasthan Royals",
    "gt": "Gujarat Titans",
    "lsg": "Lucknow Super Giants",
    "rps": "Rising Pune Supergiant",
    "gl": "Gujarat Lions",
    "ktk": "Kochi Tuskers Kerala",
    "pwi": "Pune Warriors",
    "dec": "Deccan Chargers",
}


def resolve_player_id(conn: sqlite3.Connection, player_name: str) -> str:
    """
    Resolve a player name to their database player_id.
    Handles exact match, case-insensitive match, and standard initials heuristics.
    
    Args:
        conn (sqlite3.Connection): Active SQLite connection.
        player_name (str): The name of the player to resolve.
        
    Returns:
        str: The resolved player_id.
        
    Raises:
        PlayerNotFoundError: If no matching player is found.
        AmbiguousMatchError: If the search matches multiple candidates.
    """
    name_clean = player_name.strip()
    if not name_clean:
        raise PlayerNotFoundError("Player name cannot be empty.")

    cursor = conn.cursor()

    # 1. Try exact match (case-sensitive)
    cursor.execute(
        "SELECT player_id FROM players WHERE player_name = ?", (name_clean,)
    )
    row = cursor.fetchone()
    if row:
        return row["player_id"]

    # 2. Try exact match (case-insensitive)
    cursor.execute(
        "SELECT player_id FROM players WHERE player_name = ? COLLATE NOCASE",
        (name_clean,),
    )
    row = cursor.fetchone()
    if row:
        return row["player_id"]

    # 3. Apply initials heuristic (e.g. "Virat Kohli" -> "V Kohli", "Jasprit Bumrah" -> "JJ Bumrah")
    words = name_clean.split()
    if len(words) > 1:
        last_word = words[-1]
        first_char = words[0][0].upper()

        cursor.execute(
            "SELECT player_id, player_name FROM players WHERE player_name LIKE ?",
            (f"%{last_word}%",),
        )
        candidates = cursor.fetchall()

        matched_candidates = []
        for cand in candidates:
            cand_name = cand["player_name"]
            cand_parts = cand_name.split()
            if len(cand_parts) < 2:
                continue
            cand_last = cand_parts[-1]
            if cand_last.lower() != last_word.lower():
                continue

            cand_initials = cand_parts[0].upper()
            score = 0

            # 1. Match multiple first name words if supplied (e.g. "Dwayne John" -> "DJ")
            if len(words) > 2:
                input_initials = "".join(w[0].upper() for w in words[:-1])
                if cand_initials == input_initials:
                    score = 10

            if score == 0:
                if cand_initials.endswith(first_char):
                    if not cand_initials.startswith(first_char):
                        # ends with first_char, e.g. "SL" for Lasith (starts with S)
                        score = 6
                    else:
                        # repeating chars, e.g. "JJ" for Jasprit
                        score = 5
                elif cand_initials.startswith(first_char):
                    if len(cand_initials) > 1 and len(words[0]) > 1:
                        if cand_initials[1] == words[0][1].upper():
                            # prefix match, e.g. "RA" second char 'A' matches "Ravindra" second char 'a'
                            score = 8
                        else:
                            # starts with, but prefix doesn't match
                            score = 2
                    else:
                        # single char start match, e.g. "V" for Virat
                        score = 4

            if score > 0:
                matched_candidates.append((cand, score))

        if matched_candidates:
            max_score = max(item[1] for item in matched_candidates)
            best_candidates = [item[0] for item in matched_candidates if item[1] == max_score]

            if len(best_candidates) == 1:
                return best_candidates[0]["player_id"]
            elif len(best_candidates) > 1:
                candidates_formatted = "\n".join(f"- {c['player_name']}" for c in best_candidates)
                raise AmbiguousMatchError(
                    f"Multiple players matched '{name_clean}'.\n\nCandidates:\n{candidates_formatted}"
                )

    # 4. Substring search fallback
    cursor.execute(
        "SELECT player_id, player_name FROM players WHERE player_name LIKE ?",
        (f"%{name_clean}%",),
    )
    matches = cursor.fetchall()
    if len(matches) == 1:
        return matches[0]["player_id"]
    elif len(matches) > 1:
        candidates_formatted = "\n".join(f"- {m['player_name']}" for m in matches)
        raise AmbiguousMatchError(
            f"Multiple players matched '{name_clean}'.\n\nCandidates:\n{candidates_formatted}"
        )

    raise PlayerNotFoundError(f"Player '{player_name}' not found.")


def resolve_team_id(conn: sqlite3.Connection, team_name: str) -> int:
    """
    Resolve a team name or abbreviation to its database team_id.
    
    Args:
        conn (sqlite3.Connection): Active SQLite connection.
        team_name (str): The name/abbreviation of the team to resolve.
        
    Returns:
        int: The resolved team_id.
        
    Raises:
        TeamNotFoundError: If no matching team is found.
        AmbiguousMatchError: If the search matches multiple candidates.
    """
    name_clean = team_name.strip()
    if not name_clean:
        raise TeamNotFoundError("Team name cannot be empty.")

    # Check abbreviation mapping
    mapped_name = TEAM_ABBREVIATIONS.get(name_clean.lower())
    search_name = mapped_name if mapped_name else name_clean

    cursor = conn.cursor()

    # 1. Try exact match (case-sensitive)
    cursor.execute(
        "SELECT team_id FROM teams WHERE team_name = ?", (search_name,)
    )
    row = cursor.fetchone()
    if row:
        return row["team_id"]

    # 2. Try exact match (case-insensitive)
    cursor.execute(
        "SELECT team_id FROM teams WHERE team_name = ? COLLATE NOCASE",
        (search_name,),
    )
    row = cursor.fetchone()
    if row:
        return row["team_id"]

    # 3. Substring match fallback
    cursor.execute(
        "SELECT team_id, team_name FROM teams WHERE team_name LIKE ?",
        (f"%{search_name}%",),
    )
    matches = cursor.fetchall()
    if len(matches) == 1:
        return matches[0]["team_id"]
    elif len(matches) > 1:
        names_str = ", ".join([f"'{m['team_name']}'" for m in matches])
        raise AmbiguousMatchError(
            f"Ambiguous team name '{team_name}'. Candidates: {names_str}"
        )

    raise TeamNotFoundError(f"Team '{team_name}' not found.")


def resolve_venue_id(conn: sqlite3.Connection, venue_name: str) -> int:
    """
    Resolve a venue name to its database venue_id.
    
    Args:
        conn (sqlite3.Connection): Active SQLite connection.
        venue_name (str): The name of the venue to resolve.
        
    Returns:
        int: The resolved venue_id.
        
    Raises:
        VenueNotFoundError: If no matching venue is found.
        AmbiguousMatchError: If the search matches multiple candidates.
    """
    from scripts.normalization import normalize_venue_name
    name_clean = normalize_venue_name(venue_name)
    if not name_clean:
        raise VenueNotFoundError("Venue name cannot be empty.")

    cursor = conn.cursor()

    # 1. Try exact match (case-insensitive)
    cursor.execute(
        "SELECT venue_id FROM venues WHERE venue_name = ? COLLATE NOCASE",
        (name_clean,),
    )
    row = cursor.fetchone()
    if row:
        return row["venue_id"]

    # 2. Substring match
    cursor.execute(
        "SELECT venue_id, venue_name, city FROM venues WHERE venue_name LIKE ? OR city LIKE ?",
        (f"%{name_clean}%", f"%{name_clean}%"),
    )
    matches = cursor.fetchall()
    if len(matches) == 1:
        return matches[0]["venue_id"]
    elif len(matches) > 1:
        names_str = ", ".join(
            [f"'{m['venue_name']}' (City: {m['city']})" for m in matches]
        )
        raise AmbiguousMatchError(
            f"Ambiguous venue name '{venue_name}'. Candidates: {names_str}"
        )

    raise VenueNotFoundError(f"Venue '{venue_name}' not found.")


def validate_match_id(conn: sqlite3.Connection, match_id: int) -> int:
    """
    Validate if a match_id exists in the database.
    
    Args:
        conn (sqlite3.Connection): Active SQLite connection.
        match_id (int): The match_id to validate.
        
    Returns:
        int: The validated match_id.
        
    Raises:
        MatchNotFoundError: If the match_id does not exist.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match_id,))
    row = cursor.fetchone()
    if not row:
        raise MatchNotFoundError(f"Match ID '{match_id}' not found.")
    return match_id


# --- Formatting Helpers ---

def format_overs(decimal_overs: float) -> str:
    """
    Convert decimal overs stored as floats
    (e.g. 3.6666667) into cricket notation (3.4).
    """
    whole_overs = int(decimal_overs)
    balls = round((decimal_overs - whole_overs) * 6)

    if balls == 6:
        whole_overs += 1
        balls = 0

    return f"{whole_overs}.{balls}"


# --- Shared Helpers ---

def _get_player_name(conn: sqlite3.Connection, player_id: str) -> str:
    """
    Retrieve the player name for a given player_id.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT player_name FROM players WHERE player_id = ?", (player_id,))
    row = cursor.fetchone()
    if not row:
        raise PlayerNotFoundError(f"Player ID '{player_id}' not found.")
    return row["player_name"]

