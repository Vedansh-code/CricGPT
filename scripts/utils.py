import hashlib

def get_stable_player_id(player_name: str) -> str:
    """
    Generate a stable 8-character hex ID for a player based on their name.
    Matches the official Cricsheet ID length (8 chars).
    """
    clean_name = " ".join(player_name.strip().split()).lower()
    return hashlib.sha256(clean_name.encode("utf-8")).hexdigest()[:8]

def get_match_phase(over_no: int) -> str:
    """
    Determine the match phase based on the 0-indexed over number.
    - Powerplay: Overs 1-6 (0-5 0-indexed)
    - Middle: Overs 7-15 (6-14 0-indexed)
    - Death: Overs 16-20+ (15+ 0-indexed)
    """
    if over_no < 6:
        return "Powerplay"
    elif over_no < 15:
        return "Middle"
    else:
        return "Death"

def clean_string(val) -> str:
    if val is None:
        return ""
    return str(val).strip()

def safe_int(val, default=0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def safe_float(val, default=0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
