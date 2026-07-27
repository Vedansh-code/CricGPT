# SQL schemas and queries for CricGPT ingestion pipeline

# 19 Normalized Tables structured into three layers:
# Layer 1: Lookup Tables
# Layer 2: Event Tables (Source of Truth)
# Layer 3: Analytics Tables (Precomputed summaries)

CREATE_TABLES_SQL = [
    # --- LAYER 1: LOOKUP TABLES ---
    """
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        registry_id TEXT,
        player_name TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT UNIQUE NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS venues (
        venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_name TEXT NOT NULL,
        city TEXT,
        UNIQUE(venue_name, city)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS officials (
        official_id INTEGER PRIMARY KEY AUTOINCREMENT,
        official_name TEXT UNIQUE NOT NULL,
        role TEXT
    );
    """,
    
    # --- LAYER 2: EVENT TABLES ---
    """
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        season TEXT,
        date TEXT,
        match_type TEXT,
        venue_id INTEGER,
        team1_id INTEGER,
        team2_id INTEGER,
        winner_team_id INTEGER,
        toss_winner_team_id INTEGER,
        toss_decision TEXT,
        result TEXT,
        result_margin INTEGER,
        player_of_match_id TEXT,
        overs INTEGER,
        event_name TEXT,
        gender TEXT,
        FOREIGN KEY (venue_id) REFERENCES venues(venue_id),
        FOREIGN KEY (team1_id) REFERENCES teams(team_id),
        FOREIGN KEY (team2_id) REFERENCES teams(team_id),
        FOREIGN KEY (winner_team_id) REFERENCES teams(team_id),
        FOREIGN KEY (toss_winner_team_id) REFERENCES teams(team_id),
        FOREIGN KEY (player_of_match_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS innings (
        innings_id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER,
        innings_no INTEGER,
        batting_team_id INTEGER,
        bowling_team_id INTEGER,
        target_runs INTEGER,
        target_overs REAL,
        total_runs INTEGER,
        total_wickets INTEGER,
        total_overs REAL,
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (batting_team_id) REFERENCES teams(team_id),
        FOREIGN KEY (bowling_team_id) REFERENCES teams(team_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS playing_xi (
        match_id INTEGER,
        team_id INTEGER,
        player_id TEXT,
        is_captain INTEGER,
        is_keeper INTEGER,
        PRIMARY KEY (match_id, team_id, player_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (team_id) REFERENCES teams(team_id),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER,
        innings_id INTEGER,
        over_no INTEGER,
        ball_no INTEGER,
        ball_sequence INTEGER,
        actual_delivery TEXT,
        legal_delivery INTEGER,
        batting_team_id INTEGER,
        bowling_team_id INTEGER,
        batter_id TEXT,
        bowler_id TEXT,
        non_striker_id TEXT,
        runs_batter INTEGER,
        runs_extras INTEGER,
        runs_total INTEGER,
        extras_type TEXT,
        is_boundary INTEGER,
        boundary_type INTEGER,
        is_dot_ball INTEGER,
        is_wicket INTEGER,
        dismissal_type TEXT,
        player_out_id TEXT,
        fielder1_id TEXT,
        fielder2_id TEXT,
        current_score INTEGER,
        current_wickets INTEGER,
        target_runs INTEGER,
        required_runs INTEGER,
        required_balls INTEGER,
        required_run_rate REAL,
        phase TEXT,
        is_powerplay INTEGER,
        is_middle INTEGER,
        is_death INTEGER,
        partnership_id INTEGER,
        striker_end TEXT,
        non_striker_end TEXT,
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (innings_id) REFERENCES innings(innings_id),
        FOREIGN KEY (batting_team_id) REFERENCES teams(team_id),
        FOREIGN KEY (bowling_team_id) REFERENCES teams(team_id),
        FOREIGN KEY (batter_id) REFERENCES players(player_id),
        FOREIGN KEY (bowler_id) REFERENCES players(player_id),
        FOREIGN KEY (non_striker_id) REFERENCES players(player_id),
        FOREIGN KEY (player_out_id) REFERENCES players(player_id),
        FOREIGN KEY (fielder1_id) REFERENCES players(player_id),
        FOREIGN KEY (fielder2_id) REFERENCES players(player_id)
    );
    """,

    # --- LAYER 3: ANALYTICS TABLES ---
    """
    CREATE TABLE IF NOT EXISTS batting_innings (
        match_id INTEGER,
        innings_id INTEGER,
        batter_id TEXT,
        runs INTEGER,
        balls INTEGER,
        fours INTEGER,
        sixes INTEGER,
        strike_rate REAL,
        dismissal_type TEXT,
        dismissed_by TEXT,
        PRIMARY KEY (match_id, innings_id, batter_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (innings_id) REFERENCES innings(innings_id),
        FOREIGN KEY (batter_id) REFERENCES players(player_id),
        FOREIGN KEY (dismissed_by) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bowling_innings (
        match_id INTEGER,
        innings_id INTEGER,
        bowler_id TEXT,
        overs REAL,
        maidens INTEGER,
        runs INTEGER,
        wickets INTEGER,
        economy REAL,
        PRIMARY KEY (match_id, innings_id, bowler_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (innings_id) REFERENCES innings(innings_id),
        FOREIGN KEY (bowler_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_ball_matchup (
        batter_id TEXT,
        bowler_id TEXT,
        balls INTEGER,
        runs INTEGER,
        dots INTEGER,
        fours INTEGER,
        sixes INTEGER,
        dismissals INTEGER,
        PRIMARY KEY (batter_id, bowler_id),
        FOREIGN KEY (batter_id) REFERENCES players(player_id),
        FOREIGN KEY (bowler_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_phase_stats (
        player_id TEXT,
        phase TEXT,
        balls INTEGER,
        runs INTEGER,
        outs INTEGER,
        strike_rate REAL,
        PRIMARY KEY (player_id, phase),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bowler_phase_stats (
        player_id TEXT,
        phase TEXT,
        overs REAL,
        runs INTEGER,
        wkts INTEGER,
        economy REAL,
        PRIMARY KEY (player_id, phase),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS partnerships (
        match_id INTEGER,
        innings_id INTEGER,
        player1_id TEXT,
        player2_id TEXT,
        runs INTEGER,
        balls INTEGER,
        PRIMARY KEY (match_id, innings_id, player1_id, player2_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (innings_id) REFERENCES innings(innings_id),
        FOREIGN KEY (player1_id) REFERENCES players(player_id),
        FOREIGN KEY (player2_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fall_of_wickets (
        match_id INTEGER,
        innings_id INTEGER,
        wicket_no INTEGER,
        score INTEGER,
        over REAL,
        player_out_id TEXT,
        PRIMARY KEY (match_id, innings_id, wicket_no),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (innings_id) REFERENCES innings(innings_id),
        FOREIGN KEY (player_out_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS over_summary (
        match_id INTEGER,
        innings_id INTEGER,
        over INTEGER,
        runs INTEGER,
        wickets INTEGER,
        extras INTEGER,
        PRIMARY KEY (match_id, innings_id, over),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (innings_id) REFERENCES innings(innings_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_career (
        player_id TEXT PRIMARY KEY,
        matches INTEGER,
        innings INTEGER,
        runs INTEGER,
        balls INTEGER,
        fours INTEGER,
        sixes INTEGER,
        hundreds INTEGER,
        fifties INTEGER,
        wickets INTEGER,
        catches INTEGER,
        run_outs INTEGER,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS venue_statistics (
        venue_id INTEGER PRIMARY KEY,
        matches INTEGER,
        avg_first_innings REAL,
        avg_second_innings REAL,
        highest_score INTEGER,
        lowest_score INTEGER,
        successful_chases INTEGER,
        bat_first_wins INTEGER,
        bowl_first_wins INTEGER,
        FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS team_statistics (
        team_id INTEGER PRIMARY KEY,
        matches INTEGER,
        wins INTEGER,
        losses INTEGER,
        ties INTEGER,
        avg_score REAL,
        avg_conceded REAL,
        FOREIGN KEY (team_id) REFERENCES teams(team_id)
    );
    """
]

# Indexes for optimization
CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season);",
    "CREATE INDEX IF NOT EXISTS idx_matches_venue ON matches(venue_id);",
    "CREATE INDEX IF NOT EXISTS idx_matches_team1 ON matches(team1_id);",
    "CREATE INDEX IF NOT EXISTS idx_matches_team2 ON matches(team2_id);",
    "CREATE INDEX IF NOT EXISTS idx_innings_match ON innings(match_id);",
    "CREATE INDEX IF NOT EXISTS idx_playing_xi_match ON playing_xi(match_id);",
    "CREATE INDEX IF NOT EXISTS idx_playing_xi_player ON playing_xi(player_id);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_match ON deliveries(match_id);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_innings ON deliveries(innings_id);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter_id);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler_id);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_player_out ON deliveries(player_out_id);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_phase ON deliveries(phase);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_over_no ON deliveries(over_no);",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_ball_seq ON deliveries(ball_sequence);",
    "CREATE INDEX IF NOT EXISTS idx_matchup_batter ON player_ball_matchup(batter_id);",
    "CREATE INDEX IF NOT EXISTS idx_matchup_bowler ON player_ball_matchup(bowler_id);",
    "CREATE INDEX IF NOT EXISTS idx_player_phase_player ON player_phase_stats(player_id);",
    "CREATE INDEX IF NOT EXISTS idx_bowler_phase_player ON bowler_phase_stats(player_id);"
]
