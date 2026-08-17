"""
Natural Language Query Parser for CricGPT (Phase 3A.2).

This module provides the deterministic, rule-based QueryParser that converts
natural-language cricket questions into structured QueryPlan objects.

Architecture & Isolation Rules:
- Responsible ONLY for parsing natural language into a QueryPlan.
- Does NOT execute SDK functions, access SQLite, write SQL, call FastAPI routes,
  or perform database queries.
- Must NOT import analytics, sqlite3, api, FastAPI, or database modules.
"""

import re
from typing import Optional, Tuple

from orchestration.intents import Intent
from orchestration.schemas import QuestionRequest, QueryArguments, QueryPlan
from orchestration.exceptions import PlanningError

# Recognized team names and abbreviations for disambiguating team vs player matchups
KNOWN_TEAMS = {
    "mi", "mumbai indians",
    "csk", "chennai super kings",
    "rcb", "royal challengers bengaluru", "royal challengers bangalore",
    "kkr", "kolkata knight riders",
    "dc", "delhi capitals", "delhi daredevils",
    "pbks", "punjab kings", "kings xi punjab", "kxip",
    "rr", "rajasthan royals",
    "srh", "sunrisers hyderabad",
    "gt", "gujarat titans",
    "lsg", "lucknow super giants",
    "india", "ind",
    "australia", "aus",
    "england", "eng",
    "pakistan", "pak",
    "south africa", "sa",
    "new zealand", "nz",
    "west indies", "wi",
    "sri lanka", "sl",
    "afghanistan", "afg",
    "bangladesh", "ban",
}

# Recognized cricket venues/stadiums for disambiguating venue queries
KNOWN_VENUES = {
    "wankhede", "wankhede stadium",
    "eden gardens",
    "mcg", "melbourne cricket ground",
    "chinnaswamy", "m. chinnaswamy stadium", "chinnaswamy stadium",
    "chepauk", "ma chidambaram stadium",
    "feroz shah kotla", "arun jaitley stadium",
    "narendra modi stadium", "motera",
    "dharamsala", "hpca stadium",
    "rajiv gandhi international stadium", "uppal",
    "sawai mansingh stadium",
    "ekana", "ekana stadium", "brsabu ekana stadium",
    "barabati stadium", "green park", "holkar stadium",
    "scg", "sydney cricket ground",
    "lord's", "lords", "the oval", "edgbaston", "trent bridge", "headingley",
    "gabba", "perth stadium", "waca", "adelaide oval"
}


SOURCE_NAME = "rule_based_parser"


def format_entity_name(name: str) -> str:
    """Format and clean an extracted entity string."""
    cleaned = name.strip(" ?.,'\"")
    cleaned = re.sub(r"(?:'s|’s)$", "", cleaned, flags=re.IGNORECASE).strip(" ?.,'\"")
    if not cleaned:
        return ""

    low = cleaned.lower()
    invalid_entities = {
        "what is", "what's", "whats", "who is", "who's", "whos",
        "show me", "give me", "tell me", "what", "is", "how", "how has", "how did",
        "stats", "statistics", "record", "batting average", "batting avg", "strike rate",
        "bowling economy", "economy", "about", "performance", "perform", "played",
        "matches", "games", "history", "career", "profile", "search", "details",
        "the", "a", "an", "all", "best", "top", "score", "scores", "runs", "wickets",
        "average", "strike", "bowling", "batting"
    }
    if low in invalid_entities:
        return ""

    if low in {"mi", "csk", "rcb", "kkr", "dc", "pbks", "kxip", "rr", "srh", "gt", "lsg", "mcg"}:
        return cleaned.upper()
    if cleaned.islower():
        return cleaned.title()
    return cleaned


def extract_match_id(text: str) -> Optional[int]:
    """Extract a positive match ID from the text, throwing PlanningError if invalid."""
    match = re.search(r"\bmatch\s*(?:id|#)?\s*(-?\d+)\b", text, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(?:scorecard|summary)\s*(?:for|of)?\s*(?:match\s*)?(-?\d+)\b", text, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(-?\d{5,8})\b", text)

    if match:
        val = int(match.group(1))
        if val <= 0:
            raise PlanningError("match_id must be greater than 0.")
        return val
    return None


def extract_limit(text: str, match_id: Optional[int] = None) -> Optional[int]:
    """Extract a numeric limit (e.g., top 5, last 10), throwing PlanningError if <= 0."""
    matches = re.findall(r"\b(?:top|last|recent|first|best)\s+(-?\d+)\b", text, re.IGNORECASE)
    if not matches:
        matches = re.findall(r"\b(-?\d+)\s+(?:matches|games|scores|figures|wickets|scorers|runs)\b", text, re.IGNORECASE)

    if matches:
        val = int(matches[0])
        if match_id is not None and val == match_id:
            return None
        if val <= 0:
            raise PlanningError("limit must be greater than 0.")
        return val
    return None


def extract_vs_entities(text: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extract entity1 and entity2 from explicit 'vs', 'versus', 'v', or 'against' queries.
    Returns (entity1, entity2, is_team_matchup).
    """
    p1 = re.search(r"\bhow\s+has\s+(.+?)\s+performed\s+against\s+(.+?)(?:\?|$|\s+stats|\s+record)", text, re.IGNORECASE)
    if p1:
        e1, e2 = p1.group(1), p1.group(2)
    else:
        p2 = re.search(r"\bhead\s+to\s+head\s+(?:record\s+)?(?:between\s+)?(.+?)\s+and\s+(.+?)(?:\?|$)", text, re.IGNORECASE)
        if p2:
            e1, e2 = p2.group(1), p2.group(2)
        else:
            p3 = re.search(r"(.+?)\s+(?:vs\.?|versus|against|\bv\.(?=\s+|$)|(?<=\s)v(?=\s+|$))\s+(.+?)(?:\s+head\s+to\s+head|\s+h2h|\s+record|\s+stats|\?|$)", text, re.IGNORECASE)
            if p3:
                e1, e2 = p3.group(1), p3.group(2)
            else:
                return None, None, False

    # Clean leading filler / question prefixes from e1
    QUESTION_PREFIX_REGEX = r"^(?:what\s+is|what's|whats|who\s+is|who's|whos|show\s+me|give\s+me|tell\s+me\s+about|tell\s+me|how\s+has|how\s+did|how\s+is|stats\s+for|record\s+for|between|the|a|an|about)\s*"
    while re.search(QUESTION_PREFIX_REGEX, e1, re.IGNORECASE):
        new_e1 = re.sub(QUESTION_PREFIX_REGEX, "", e1, flags=re.IGNORECASE).strip()
        if new_e1 == e1:
            break
        e1 = new_e1

    # Clean trailing filler / stats from e2
    e2 = re.sub(r"\s+(?:head\s+to\s+head|h2h|stats|statistics|record|batting\s+average|strike\s+rate|bowling\s+economy|economy)$", "", e2, flags=re.IGNORECASE)

    f1 = format_entity_name(e1)
    f2 = format_entity_name(e2)

    if not f1 or not f2:
        return None, None, False

    # Reject single-character entities unless recognized as a team abbreviation (e.g., "MI", "GT", etc.)
    if len(f1) < 2 and f1.lower() not in KNOWN_TEAMS:
        return None, None, False
    if len(f2) < 2 and f2.lower() not in KNOWN_TEAMS:
        return None, None, False

    # Reject if f1 or f2 contains invalid keywords (stat names, common verbs/prepositions)
    invalid_keywords = {
        "batting average", "batting avg", "strike rate", "bowling economy", "economy rate",
        "top run scorers", "wicket takers", "average", "strike", "economy", "bowling", "batting",
        "record", "stats", "statistics", "performance", "perform", "profile", "career", "history",
        "is", "about"
    }
    if f1.lower() in invalid_keywords or f2.lower() in invalid_keywords:
        return None, None, False

    is_head_to_head_phrase = bool(re.search(r"\b(?:head\s+to\s+head|h2h)\b", text, re.IGNORECASE))
    is_team = is_head_to_head_phrase or (f1.lower() in KNOWN_TEAMS or f2.lower() in KNOWN_TEAMS)

    return f1, f2, is_team



def extract_team_name(text: str) -> Optional[str]:
    """Extract team name for TEAM_RECORD intent."""
    match = re.search(r"(?:team\s+record\s+for|team\s+record\s+of|record\s+for|win\s+loss\s+record\s+of|record\s+of)\s+(.+?)(?:\?|$|\s+team)", text, re.IGNORECASE)
    if match:
        return format_entity_name(match.group(1))

    match = re.search(r"(.+?)\s+(?:team\s+record|win\s+loss\s+record|record)", text, re.IGNORECASE)
    if match:
        cand = re.sub(r"^(?:show\s+me|give\s+me|what\s+is|the)\s+", "", match.group(1), flags=re.IGNORECASE)
        return format_entity_name(cand)

    for team in KNOWN_TEAMS:
        if re.search(r"\b" + re.escape(team) + r"\b", text, re.IGNORECASE):
            return format_entity_name(team)

    return None


def extract_venue_name(text: str) -> Optional[str]:
    """Extract venue/stadium name for VENUE_SUMMARY intent."""
    for venue in KNOWN_VENUES:
        if re.search(r"\b" + re.escape(venue) + r"\b", text, re.IGNORECASE):
            # Strip " stadium" if in known list to get clean base name unless specified
            clean = re.sub(r"\s+stadium$", "", venue, flags=re.IGNORECASE)
            return format_entity_name(clean)

    match = re.search(r"(?:stats|statistics|summary)\s+(?:for|of|at|in)?\s+(.+?)(?:\?|$|\s+stadium|\s+venue)", text, re.IGNORECASE)
    if match:
        return format_entity_name(match.group(1))

    match = re.search(r"(.+?)\s+(?:stadium|venue|ground)\s+(?:stats|summary|statistics)?", text, re.IGNORECASE)
    if match:
        cand = re.sub(r"^(?:show\s+me|give\s+me|what\s+are|the)\s+", "", match.group(1), flags=re.IGNORECASE)
        return format_entity_name(cand)

    return None


def extract_player_name(text: str) -> Optional[str]:
    """Extract player name from a query."""
    QUESTION_PREFIX_REGEX = r"^(?:what\s+is|what's|whats|who\s+is|who's|whos|show\s+me|give\s+me|get|tell\s+me|how\s+is|how\s+was|how\s+did|how\s+has|find|search|the|a|an|please)\s+"

    # 1. Check apostrophe pattern e.g. "Virat Kohli's", "V Kohli's"
    pos_match = re.search(r"([A-Za-z0-9\s\.\'-]+?)(?:'s|’s)", text)
    if pos_match:
        cand = pos_match.group(1)
        while re.search(QUESTION_PREFIX_REGEX, cand, re.IGNORECASE):
            cand = re.sub(QUESTION_PREFIX_REGEX, "", cand, flags=re.IGNORECASE)
        formatted = format_entity_name(cand)
        if formatted and formatted.lower() not in {"match", "team", "venue"}:
            return formatted

    # 2. Check preposition pattern e.g. "average of Virat Kohli", "strike rate for Rohit Sharma"
    prep_match = re.search(r"(?:average|avg|strike\s+rate|sr|economy|economy\s+rate|percentage|figures|matches|games|history|career|profile|stats|statistics)\s+(?:of|for|by)\s+([A-Za-z0-9\s\.\'-]+?)(?:\?|$)", text, re.IGNORECASE)
    if prep_match:
        cand = prep_match.group(1)
        cand = re.sub(r"\s+(?:head\s+to\s+head|h2h|stats|statistics|record|\?)+$", "", cand, flags=re.IGNORECASE)
        while re.search(QUESTION_PREFIX_REGEX, cand, re.IGNORECASE):
            cand = re.sub(QUESTION_PREFIX_REGEX, "", cand, flags=re.IGNORECASE)
        formatted = format_entity_name(cand)
        if formatted and formatted.lower() not in KNOWN_TEAMS:
            return formatted

    # 3. Check verb/phrase pattern e.g. "who is Jasprit Bumrah", "search player Kohli"
    verb_match = re.search(r"(?:who\s+is|search\s+player|find\s+player|search\s+for|profile\s+of)\s+([A-Za-z0-9\s\.\'-]+?)(?:\?|$)", text, re.IGNORECASE)
    if verb_match:
        cand = verb_match.group(1)
        formatted = format_entity_name(cand)
        if formatted:
            return formatted

    # 4. Token removal fallback
    words_to_strip = {
        "what", "is", "what's", "whats", "who", "who's", "whos", "the", "a", "an", "show", "me", "give", "for", "of", "by", "stats", "statistics",
        "please", "how", "did", "has", "perform", "performed", "get", "tell", "batting", "average", "avg",
        "strike", "rate", "sr", "boundary", "percentage", "percent", "%", "boundaries", "bowling",
        "economy", "best", "figures", "recent", "matches", "games", "history", "career", "profile",
        "search", "highest", "individual", "scores", "top", "run", "scorers", "wicket", "takers",
        "player", "all", "last"
    }

    tokens = text.split()
    remaining = []
    for tok in tokens:
        clean_tok = tok.strip(" ?.,'\"")
        clean_tok_no_poss = re.sub(r"(?:'s|’s)$", "", clean_tok, flags=re.IGNORECASE)
        if clean_tok_no_poss.lower() not in words_to_strip and not clean_tok_no_poss.isdigit():
            remaining.append(clean_tok_no_poss)

    if remaining:
        cand = " ".join(remaining)
        return format_entity_name(cand)

    return None


class QueryParser:
    """
    Natural Language Query Parser for CricGPT.

    Parses user questions into structured QueryPlan instances using deterministic rules.
    """

    def parse(self, question: str) -> QueryPlan:
        """
        Parse a natural language question into a QueryPlan.

        Args:
            question: Natural language question string.

        Returns:
            QueryPlan object containing intent, arguments, confidence, and clarification info.

        Raises:
            PlanningError: If the input is invalid or malformed.
        """
        try:
            req = QuestionRequest(question=question)
        except ValueError as ve:
            raise PlanningError(str(ve)) from ve

        text = req.question
        lower_text = text.lower()

        # 1. Match-specific intents
        match_id = extract_match_id(text)

        if "scorecard" in lower_text:
            if match_id is None:
                return QueryPlan(
                    intent=Intent.MATCH_SCORECARD,
                    arguments=QueryArguments(),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Please specify the match ID for the scorecard."
                )
            return QueryPlan(
                intent=Intent.MATCH_SCORECARD,
                arguments=QueryArguments(match_id=match_id),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if "summary" in lower_text and ("match" in lower_text or match_id is not None):
            if match_id is None:
                return QueryPlan(
                    intent=Intent.MATCH_SUMMARY,
                    arguments=QueryArguments(),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Please specify the match ID for the match summary."
                )
            return QueryPlan(
                intent=Intent.MATCH_SUMMARY,
                arguments=QueryArguments(match_id=match_id),
                confidence=0.95,
                source=SOURCE_NAME
            )

        # 2. Overall / Leaderboard stats (evaluated before generic matchups)
        limit = extract_limit(text, match_id=match_id)

        if re.search(r"top\s*(?:\d+\s*)?run\s*scorer|most\s+runs|leading\s+run\s+scorer|highest\s+run\s+getter", lower_text):
            return QueryPlan(
                intent=Intent.TOP_RUN_SCORERS,
                arguments=QueryArguments(limit=limit),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if re.search(r"(?:top\s*(?:\d+\s*)?)?highest\s+individual\s+score|highest\s+score\s+in\s+an\s+innings|top\s+(?:\d+\s*)?individual\s+score", lower_text):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.HIGHEST_INDIVIDUAL_SCORES,
                arguments=QueryArguments(player_name=player, limit=limit),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if re.search(r"top\s*(?:\d+\s*)?wicket\s+taker|most\s+wickets?|leading\s+wicket\s+taker|highest\s+wicket\s+taker", lower_text):
            return QueryPlan(
                intent=Intent.TOP_WICKET_TAKERS,
                arguments=QueryArguments(limit=limit),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if re.search(r"(?:top\s*(?:\d+\s*)?)?best\s+bowling\s+figure|best\s+bowling", lower_text):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.BEST_BOWLING_FIGURES,
                arguments=QueryArguments(player_name=player, limit=limit),
                confidence=0.95,
                source=SOURCE_NAME
            )

        # 3. Specific Player Analytics (evaluated before generic matchups)
        if any(p in lower_text for p in ["batting average", "batting avg"]) or ("average" in lower_text and "bowling" not in lower_text):
            player = extract_player_name(text)
            if not player:
                return QueryPlan(
                    intent=Intent.BATTING_AVERAGE,
                    arguments=QueryArguments(),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Could you specify the player for the batting average?"
                )
            return QueryPlan(
                intent=Intent.BATTING_AVERAGE,
                arguments=QueryArguments(player_name=player),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if any(p in lower_text for p in ["batting strike rate", "batting sr"]) or ("strike rate" in lower_text and "bowling" not in lower_text):
            player = extract_player_name(text)
            if not player:
                return QueryPlan(
                    intent=Intent.BATTING_STRIKE_RATE,
                    arguments=QueryArguments(),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Could you specify the player for the batting strike rate?"
                )
            return QueryPlan(
                intent=Intent.BATTING_STRIKE_RATE,
                arguments=QueryArguments(player_name=player),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if any(p in lower_text for p in ["boundary percentage", "boundary %", "boundaries percentage", "boundary percent"]):
            player = extract_player_name(text)
            if not player:
                return QueryPlan(
                    intent=Intent.BOUNDARY_PERCENTAGE,
                    arguments=QueryArguments(),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Could you specify the player for boundary percentage?"
                )
            return QueryPlan(
                intent=Intent.BOUNDARY_PERCENTAGE,
                arguments=QueryArguments(player_name=player),
                confidence=0.95,
                source=SOURCE_NAME
            )

        if any(p in lower_text for p in ["bowling economy", "economy rate", "economy"]):
            player = extract_player_name(text)
            if not player:
                return QueryPlan(
                    intent=Intent.BOWLING_ECONOMY,
                    arguments=QueryArguments(),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Could you specify the player for bowling economy?"
                )
            return QueryPlan(
                intent=Intent.BOWLING_ECONOMY,
                arguments=QueryArguments(player_name=player),
                confidence=0.95,
                source=SOURCE_NAME
            )

        # 4. Matchups & Head to Head
        e1, e2, is_team_matchup = extract_vs_entities(text)
        if e1 and e2:
            if is_team_matchup:
                return QueryPlan(
                    intent=Intent.TEAM_HEAD_TO_HEAD,
                    arguments=QueryArguments(team1=e1, team2=e2),
                    confidence=0.95,
                    source=SOURCE_NAME
                )
            else:
                return QueryPlan(
                    intent=Intent.BATTER_VS_BOWLER,
                    arguments=QueryArguments(batter=e1, bowler=e2),
                    confidence=0.95,
                    source=SOURCE_NAME
                )

        # 5. Team Record & Venue Summary
        if "head to head" in lower_text or "h2h" in lower_text:
            return QueryPlan(
                intent=Intent.TEAM_HEAD_TO_HEAD,
                arguments=QueryArguments(),
                confidence=0.4,
                source=SOURCE_NAME,
                requires_clarification=True,
                clarification_message="Please specify the two teams for the head-to-head comparison."
            )

        if any(p in lower_text for p in ["team record", "win loss record"]) or ("record" in lower_text and not match_id):
            team_name = extract_team_name(text)
            return QueryPlan(
                intent=Intent.TEAM_RECORD,
                arguments=QueryArguments(team_name=team_name),
                confidence=0.90 if team_name else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if team_name else True,
                clarification_message=None if team_name else "Could you specify the team for the record?"
            )

        venue_name = extract_venue_name(text)
        if venue_name or any(p in lower_text for p in ["venue summary", "stadium stats", "venue stats"]):
            return QueryPlan(
                intent=Intent.VENUE_SUMMARY,
                arguments=QueryArguments(venue_name=venue_name),
                confidence=0.90 if venue_name else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if venue_name else True,
                clarification_message=None if venue_name else "Could you specify the venue or stadium name?"
            )

        # 6. Player History / Recent / Career / Profile / Search
        if any(p in lower_text for p in ["recent matches", "last matches", "recent games", "last games"]) or (limit and "matches" in lower_text):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.PLAYER_RECENT_MATCHES,
                arguments=QueryArguments(player_name=player, limit=limit),
                confidence=0.90 if player else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if player else True,
                clarification_message=None if player else "Could you specify the player for recent matches?"
            )

        if any(p in lower_text for p in ["match history", "all matches"]):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.PLAYER_MATCH_HISTORY,
                arguments=QueryArguments(player_name=player, limit=limit),
                confidence=0.90 if player else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if player else True,
                clarification_message=None if player else "Could you specify the player for match history?"
            )

        if any(p in lower_text for p in ["career stats", "career summary", "career"]):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.PLAYER_CAREER,
                arguments=QueryArguments(player_name=player),
                confidence=0.90 if player else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if player else True,
                clarification_message=None if player else "Could you specify the player for career statistics?"
            )

        if any(p in lower_text for p in ["search player", "find player", "search for player", "search for"]):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.PLAYER_SEARCH,
                arguments=QueryArguments(player_name=player),
                confidence=0.90 if player else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if player else True,
                clarification_message=None if player else "Could you specify the player name to search for?"
            )

        if any(p in lower_text for p in ["player profile", "profile of", "who is", "profile"]):
            player = extract_player_name(text)
            return QueryPlan(
                intent=Intent.PLAYER_PROFILE,
                arguments=QueryArguments(player_name=player),
                confidence=0.90 if player else 0.4,
                source=SOURCE_NAME,
                requires_clarification=False if player else True,
                clarification_message=None if player else "Could you specify the player for the profile?"
            )

        # 7. Ambiguous or vague questions
        player = extract_player_name(text)

        if any(p in lower_text for p in ["how did", "how has"]) and "perform" in lower_text:
            if player:
                return QueryPlan(
                    intent=Intent.UNKNOWN,
                    arguments=QueryArguments(player_name=player),
                    confidence=0.4,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message=f"Could you specify what performance details you want for {player} (e.g. career stats, recent matches, batting average, or strike rate)?"
                )

        if "stats" in lower_text or "statistics" in lower_text:
            if player:
                return QueryPlan(
                    intent=Intent.PLAYER_PROFILE,
                    arguments=QueryArguments(player_name=player),
                    confidence=0.5,
                    source=SOURCE_NAME,
                    requires_clarification=False
                )
            else:
                return QueryPlan(
                    intent=Intent.UNKNOWN,
                    arguments=QueryArguments(),
                    confidence=0.0,
                    source=SOURCE_NAME,
                    requires_clarification=True,
                    clarification_message="Could you specify the player, team, match, or statistic you're interested in?"
                )

        # 8. Unrecognized / Fallback query
        return QueryPlan(
            intent=Intent.UNKNOWN,
            arguments=QueryArguments(),
            confidence=0.0,
            source=SOURCE_NAME,
            requires_clarification=False,
            clarification_message=None
        )

