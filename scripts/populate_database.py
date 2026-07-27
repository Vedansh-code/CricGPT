import os
import sys

# Ensure root directory is in python path and prevent shadowing
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir in sys.path:
    sys.path.remove(scripts_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import json
import time
import glob
from scripts.logging import logger
from scripts.database import DatabaseManager

def get_match_phase(over_no: int) -> str:
    if over_no < 6:
        return "Powerplay"
    elif over_no < 15:
        return "Middle"
    else:
        return "Death"

def parse_and_populate(db_path="data/database/cricgpt.db", raw_dir="data/raw"):
    start_time = time.time()
    
    db = DatabaseManager(db_path)
    
    # Global career statistics accumulators
    global_player_career = {}  # player_id -> dict
    global_matchups = {}       # (batter_id, bowler_id) -> dict
    global_player_phase = {}   # (player_id, phase) -> dict
    global_bowler_phase = {}   # (player_id, phase) -> dict
    global_venues = {}         # venue_id -> dict
    global_teams = {}          # team_id -> dict
    
    # Initialize trackers
    matches_inserted = 0
    deliveries_inserted = 0
    skipped_matches = []
    
    json_pattern = os.path.join(raw_dir, "*.json")
    json_files = sorted(glob.glob(json_pattern))
    total_files = len(json_files)
    
    logger.info(f"Found {total_files} JSON match files to ingest.")
    
    for idx, filepath in enumerate(json_files, 1):
        filename = os.path.basename(filepath)
        match_id_str = filename.replace(".json", "")
        try:
            match_id = int(match_id_str)
        except ValueError:
            logger.warning(f"Skipping file with non-numeric name: {filename}")
            skipped_matches.append(filename)
            continue
            
        logger.info(f"[{idx}/{total_files}] Parsing match {match_id}...")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read/parse JSON file {filename}: {e}")
            skipped_matches.append(filename)
            continue
            
        # Parse the match metadata
        info = data.get("info", {})
        registry = info.get("registry", {}).get("people", {})
        
        # Pre-populate all registry players in database
        for p_name in registry:
            db.get_or_insert_player(p_name, registry)
            
        # Parse Venue and City
        venue_name = info.get("venue")
        if not venue_name:
            logger.warning(f"Match {match_id} has no venue name specified. Skipping.")
            skipped_matches.append(filename)
            continue
        city = info.get("city")
        venue_id = db.get_or_insert_venue(venue_name, city)
        
        # Parse Teams
        teams = info.get("teams", [])
        if len(teams) < 2:
            logger.warning(f"Match {match_id} has fewer than 2 teams. Skipping.")
            skipped_matches.append(filename)
            continue
            
        team1_id = db.get_or_insert_team(teams[0])
        team2_id = db.get_or_insert_team(teams[1])
        
        # Toss
        toss = info.get("toss", {})
        toss_winner_name = toss.get("winner")
        toss_winner_team_id = db.get_or_insert_team(toss_winner_name) if toss_winner_name else None
        toss_decision = toss.get("decision")
        
        # Outcome and Result Margin
        outcome = info.get("outcome", {})
        winner_name = outcome.get("winner")
        winner_team_id = db.get_or_insert_team(winner_name) if winner_name else None
        result = outcome.get("result")
        result_margin = None
        
        if "by" in outcome:
            by = outcome["by"]
            if "runs" in by:
                result = "runs"
                result_margin = by["runs"]
            elif "wickets" in by:
                result = "wickets"
                result_margin = by["wickets"]
                
        if not result and outcome.get("result"):
            result = outcome.get("result")
            
        # Player of the match
        pom_list = info.get("player_of_match", [])
        player_of_match_id = None
        if pom_list:
            player_of_match_id = db.get_or_insert_player(pom_list[0], registry)
            
        season = str(info.get("season", ""))
        date = info.get("dates", [None])[0]
        match_type = info.get("match_type")
        overs = info.get("overs", 20)
        gender = info.get("gender", "male")
        
        event_dict = info.get("event")
        event_name = None
        if isinstance(event_dict, dict):
            event_name = event_dict.get("name")
        elif isinstance(event_dict, str):
            event_name = event_dict

        # Parse Officials
        officials_dict = info.get("officials", {})
        for role, name_list in officials_dict.items():
            for name in name_list:
                db.get_or_insert_official(name, role)

        # Collect playing XI information
        playing_xi_rows = []
        captains = info.get("captains", {})
        keepers = info.get("wicketkeepers", {})
        
        for team_name, players_list in info.get("players", {}).items():
            t_id = db.get_or_insert_team(team_name)
            for p_name in players_list:
                p_id = db.get_or_insert_player(p_name, registry)
                is_captain = 1 if captains.get(team_name) == p_name else 0
                is_keeper = 1 if keepers.get(team_name) == p_name else 0
                playing_xi_rows.append((match_id, t_id, p_id, is_captain, is_keeper))

        # --- PREPARE MATCH LEVEL TEMPORARY AGGREGATIONS FOR ROLLBACK SAFETY ---
        match_venues_contrib = {}
        match_teams_contrib = {}
        match_player_career_contrib = {}
        match_player_phase_contrib = {}
        match_bowler_phase_contrib = {}
        match_matchups_contrib = {}

        # Initialize match venue stats contrib
        match_venues_contrib[venue_id] = {
            'matches': 1,
            'first_inn_runs': None,
            'second_inn_runs': None,
            'highest_score': 0,
            'lowest_score': 9999,
            'successful_chases': 0,
            'bat_first_wins': 0,
            'bowl_first_wins': 0
        }
        
        # Initialize match team stats contrib
        for t_id in (team1_id, team2_id):
            match_teams_contrib[t_id] = {
                'matches': 1,
                'wins': 1 if winner_team_id == t_id else 0,
                'losses': 1 if (winner_team_id and winner_team_id != t_id) else 0,
                'ties': 1 if result == 'tie' else 0,
                'total_runs_scored': 0,
                'total_runs_conceded': 0
            }

        # Initialize match player career matches played
        for _, _, p_id, _, _ in playing_xi_rows:
            match_player_career_contrib[p_id] = {
                'matches': 1, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
            }

        # Start database transaction for this match
        try:
            db.begin_transaction()
            
            # 1. Insert Match
            db.execute(
                """
                INSERT OR REPLACE INTO matches (
                    match_id, season, date, match_type, venue_id, team1_id, team2_id,
                    winner_team_id, toss_winner_team_id, toss_decision, result,
                    result_margin, player_of_match_id, overs, event_name, gender
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id, season, date, match_type, venue_id, team1_id, team2_id,
                    winner_team_id, toss_winner_team_id, toss_decision, result,
                    result_margin, player_of_match_id, overs, event_name, gender
                )
            )
            
            # 2. Insert Playing XI
            db.executemany(
                """
                INSERT OR REPLACE INTO playing_xi (match_id, team_id, player_id, is_captain, is_keeper)
                VALUES (?, ?, ?, ?, ?)
                """,
                playing_xi_rows
            )
            
            # 3. Process Innings and Deliveries
            innings_list = data.get("innings", [])
            
            # To track running partnerships
            partnership_counter = 0
            
            for inn_idx, innings_dict in enumerate(innings_list, 1):
                batting_team_name = innings_dict.get("team")
                batting_team_id = db.get_or_insert_team(batting_team_name)
                bowling_team_id = team2_id if batting_team_id == team1_id else team1_id
                
                target_dict = innings_dict.get("target", {})
                target_runs = target_dict.get("runs")
                target_overs = target_dict.get("overs")
                
                # Inning running variables
                total_runs = 0
                total_wickets = 0
                legal_balls_count = 0
                ball_sequence = 0
                
                deliveries_to_insert = []
                
                # Match-specific Inning aggregates
                batting_stats = {}
                bowling_stats = {}
                partnership_stats = {}
                fall_of_wickets_list = []
                over_summary_stats = {}
                
                # Active partnership tracking
                active_partnership = None
                
                overs_list = innings_dict.get("overs", [])
                for over_dict in overs_list:
                    over_no = over_dict.get("over", 0)
                    deliveries_list = over_dict.get("deliveries", [])
                    
                    for del_idx, delivery_dict in enumerate(deliveries_list, 1):
                        batter_name = delivery_dict.get("batter")
                        bowler_name = delivery_dict.get("bowler")
                        non_striker_name = delivery_dict.get("non_striker")
                        
                        batter_id = db.get_or_insert_player(batter_name, registry)
                        bowler_id = db.get_or_insert_player(bowler_name, registry)
                        non_striker_id = db.get_or_insert_player(non_striker_name, registry)
                        
                        runs_dict = delivery_dict.get("runs", {})
                        runs_batter = runs_dict.get("batter", 0)
                        runs_extras = runs_dict.get("extras", 0)
                        runs_total = runs_dict.get("total", 0)
                        
                        extras_dict = delivery_dict.get("extras", {})
                        wides = extras_dict.get("wides", 0)
                        noballs = extras_dict.get("noballs", 0)
                        byes = extras_dict.get("byes", 0)
                        legbyes = extras_dict.get("legbyes", 0)
                        penalty = extras_dict.get("penalty", 0)
                        
                        is_wide = 1 if wides > 0 else 0
                        is_noball = 1 if noballs > 0 else 0
                        legal_delivery = 1 if (is_wide == 0 and is_noball == 0) else 0
                        
                        extras_type = None
                        if extras_dict:
                            # Take the first extras key found
                            extras_type = list(extras_dict.keys())[0]
                            
                        actual_delivery = delivery_dict.get("actual_delivery")
                        
                        # Boundary calculations
                        is_boundary = 1 if runs_batter in (4, 6) and not delivery_dict.get("non_boundary", False) else 0
                        boundary_type = 4 if (runs_batter == 4 and is_boundary) else (6 if (runs_batter == 6 and is_boundary) else 0)
                        
                        is_dot_ball = 1 if runs_total == 0 else 0
                        
                        # Sequential tracking
                        ball_sequence += 1
                        if legal_delivery:
                            legal_balls_count += 1
                            
                        # Dismissal logic
                        wickets_list = delivery_dict.get("wickets", [])
                        is_wicket = 1 if wickets_list else 0
                        dismissal_type = None
                        player_out_id = None
                        fielder1_id = None
                        fielder2_id = None
                        
                        if is_wicket:
                            w_dict = wickets_list[0]
                            dismissal_type = w_dict.get("kind")
                            player_out_name = w_dict.get("player_out")
                            player_out_id = db.get_or_insert_player(player_out_name, registry)
                            total_wickets += 1
                            
                            fielders = w_dict.get("fielders", [])
                            if fielders:
                                f1 = fielders[0]
                                f1_name = f1.get("name") if isinstance(f1, dict) else f1
                                fielder1_id = db.get_or_insert_player(f1_name, registry)
                                
                                # Track fielder actions in temporary player career
                                if fielder1_id not in match_player_career_contrib:
                                    match_player_career_contrib[fielder1_id] = {
                                        'matches': 0, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                                        'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
                                    }
                                if dismissal_type == "caught":
                                    match_player_career_contrib[fielder1_id]['catches'] += 1
                                elif dismissal_type == "run out":
                                    match_player_career_contrib[fielder1_id]['run_outs'] += 1
                                    
                                if len(fielders) > 1:
                                    f2 = fielders[1]
                                    f2_name = f2.get("name") if isinstance(f2, dict) else f2
                                    fielder2_id = db.get_or_insert_player(f2_name, registry)
                                    if fielder2_id not in match_player_career_contrib:
                                        match_player_career_contrib[fielder2_id] = {
                                            'matches': 0, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                                            'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
                                        }
                                    if dismissal_type == "run out":
                                        match_player_career_contrib[fielder2_id]['run_outs'] += 1
                                        
                            # Check caught & bowled
                            if dismissal_type == "caught and bowled":
                                if bowler_id not in match_player_career_contrib:
                                    match_player_career_contrib[bowler_id] = {
                                        'matches': 0, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                                        'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
                                    }
                                match_player_career_contrib[bowler_id]['catches'] += 1
                                
                        # Running total updates
                        total_runs += runs_total
                        current_score = total_runs
                        current_wickets = total_wickets
                        
                        # Required runs/balls calculations
                        required_runs = None
                        required_balls = None
                        required_run_rate = None
                        if target_runs is not None:
                            required_runs = target_runs - current_score
                            # Target balls count
                            to_overs = int(target_overs)
                            to_balls = int(round((target_overs - to_overs) * 10))
                            target_balls = to_overs * 6 + to_balls
                            
                            required_balls = max(0, target_balls - legal_balls_count)
                            if required_balls > 0:
                                required_run_rate = float(required_runs) / (required_balls / 6.0)
                            else:
                                required_run_rate = 0.0 if required_runs <= 0 else 99.99
                                
                        phase = get_match_phase(over_no)
                        is_powerplay = 1 if phase == "Powerplay" else 0
                        is_middle = 1 if phase == "Middle" else 0
                        is_death = 1 if phase == "Death" else 0
                        
                        # Partnership tracking
                        p1_id, p2_id = sorted([batter_id, non_striker_id])
                        current_pair = (p1_id, p2_id)
                        if active_partnership != current_pair:
                            partnership_counter += 1
                            active_partnership = current_pair
                        pid_val = partnership_counter
                        
                        # Add to deliveries rows
                        deliveries_to_insert.append((
                            match_id, None, over_no, del_idx, ball_sequence, actual_delivery,
                            legal_delivery, batting_team_id, bowling_team_id, batter_id, bowler_id, non_striker_id,
                            runs_batter, runs_extras, runs_total, extras_type, is_boundary, boundary_type, is_dot_ball,
                            is_wicket, dismissal_type, player_out_id, fielder1_id, fielder2_id,
                            current_score, current_wickets, target_runs, required_runs, required_balls, required_run_rate,
                            phase, is_powerplay, is_middle, is_death, pid_val, batter_name, non_striker_name
                        ))
                        
                        # --- UPDATE MATCH LEVEL ACCUMULATORS ---
                        
                        # 1. Batting statistics
                        if batter_id not in batting_stats:
                            batting_stats[batter_id] = {'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0, 'dismissal_type': None, 'dismissed_by': None}
                        if not is_wide:
                            batting_stats[batter_id]['balls'] += 1
                        batting_stats[batter_id]['runs'] += runs_batter
                        if boundary_type == 4:
                            batting_stats[batter_id]['fours'] += 1
                        elif boundary_type == 6:
                            batting_stats[batter_id]['sixes'] += 1
                            
                        # Crediting bowler for wicket
                        is_bowler_credited = is_wicket and dismissal_type in ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled', 'hit wicket')
                        if is_wicket and player_out_id == batter_id:
                            batting_stats[batter_id]['dismissal_type'] = dismissal_type
                            if is_bowler_credited:
                                batting_stats[batter_id]['dismissed_by'] = bowler_id
                                
                        # 2. Bowling statistics
                        if bowler_id not in bowling_stats:
                            bowling_stats[bowler_id] = {'legal_balls': 0, 'runs': 0, 'wickets': 0, 'overs_by_over': {}}
                        if not is_wide and not is_noball:
                            bowling_stats[bowler_id]['legal_balls'] += 1
                        runs_conceded = runs_batter + wides + noballs
                        bowling_stats[bowler_id]['runs'] += runs_conceded
                        if is_bowler_credited:
                            bowling_stats[bowler_id]['wickets'] += 1
                            
                        o_stats = bowling_stats[bowler_id]['overs_by_over']
                        if over_no not in o_stats:
                            o_stats[over_no] = {'legal_balls': 0, 'runs_conceded': 0}
                        if not is_wide and not is_noball:
                            o_stats[over_no]['legal_balls'] += 1
                        o_stats[over_no]['runs_conceded'] += runs_conceded
                        
                        # 3. Partnerships
                        if current_pair not in partnership_stats:
                            partnership_stats[current_pair] = {'runs': 0, 'balls': 0}
                        partnership_stats[current_pair]['runs'] += runs_total
                        if not is_wide:
                            partnership_stats[current_pair]['balls'] += 1
                            
                        # 4. Fall of Wickets
                        if is_wicket and player_out_id is not None:
                            try:
                                over_float = float(actual_delivery)
                            except ValueError:
                                over_float = over_no + (del_idx / 6.0)
                            fall_of_wickets_list.append((total_wickets, current_score, over_float, player_out_id))
                            
                        # 5. Over Summary
                        if over_no not in over_summary_stats:
                            over_summary_stats[over_no] = {'runs': 0, 'wickets': 0, 'extras': 0}
                        over_summary_stats[over_no]['runs'] += runs_total
                        if is_wicket:
                            over_summary_stats[over_no]['wickets'] += 1
                        over_summary_stats[over_no]['extras'] += runs_extras
                        
                        # 6. Global Matchup contrib
                        m_key = (batter_id, bowler_id)
                        if m_key not in match_matchups_contrib:
                            match_matchups_contrib[m_key] = {'balls': 0, 'runs': 0, 'dots': 0, 'fours': 0, 'sixes': 0, 'dismissals': 0}
                        if not is_wide:
                            match_matchups_contrib[m_key]['balls'] += 1
                        match_matchups_contrib[m_key]['runs'] += runs_batter
                        if runs_total == 0:
                            match_matchups_contrib[m_key]['dots'] += 1
                        if boundary_type == 4:
                            match_matchups_contrib[m_key]['fours'] += 1
                        elif boundary_type == 6:
                            match_matchups_contrib[m_key]['sixes'] += 1
                        if is_wicket and player_out_id == batter_id and is_bowler_credited:
                            match_matchups_contrib[m_key]['dismissals'] += 1
                            
                        # 7. Global Player phase stats contrib
                        pp_key = (batter_id, phase)
                        if pp_key not in match_player_phase_contrib:
                            match_player_phase_contrib[pp_key] = {'balls': 0, 'runs': 0, 'outs': 0}
                        if not is_wide:
                            match_player_phase_contrib[pp_key]['balls'] += 1
                        match_player_phase_contrib[pp_key]['runs'] += runs_batter
                        if is_wicket and player_out_id == batter_id:
                            match_player_phase_contrib[pp_key]['outs'] += 1
                            
                        # 8. Global Bowler phase stats contrib
                        bp_key = (bowler_id, phase)
                        if bp_key not in match_bowler_phase_contrib:
                            match_bowler_phase_contrib[bp_key] = {'legal_balls': 0, 'runs': 0, 'wickets': 0}
                        if not is_wide and not is_noball:
                            match_bowler_phase_contrib[bp_key]['legal_balls'] += 1
                        match_bowler_phase_contrib[bp_key]['runs'] += runs_conceded
                        if is_wicket and is_bowler_credited:
                            match_bowler_phase_contrib[bp_key]['wickets'] += 1

                # Update team score contributions
                match_teams_contrib[batting_team_id]['total_runs_scored'] += total_runs
                match_teams_contrib[bowling_team_id]['total_runs_conceded'] += total_runs

                # Inning total overs calculation
                total_overs = legal_balls_count / 6.0
                
                # Update Venue runs
                if inn_idx == 1:
                    match_venues_contrib[venue_id]['first_inn_runs'] = total_runs
                elif inn_idx == 2:
                    match_venues_contrib[venue_id]['second_inn_runs'] = total_runs
                    
                match_venues_contrib[venue_id]['highest_score'] = max(match_venues_contrib[venue_id]['highest_score'], total_runs)
                match_venues_contrib[venue_id]['lowest_score'] = min(match_venues_contrib[venue_id]['lowest_score'], total_runs)

                # Insert Innings
                db.execute(
                    """
                    INSERT INTO innings (
                        match_id, innings_no, batting_team_id, bowling_team_id,
                        target_runs, target_overs, total_runs, total_wickets, total_overs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        match_id, inn_idx, batting_team_id, bowling_team_id,
                        target_runs, target_overs, total_runs, total_wickets, total_overs
                    )
                )
                innings_id = db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                # Update deliveries with the innings_id and insert
                final_deliveries = []
                for row in deliveries_to_insert:
                    lst = list(row)
                    lst[1] = innings_id
                    final_deliveries.append(tuple(lst))
                    
                db.executemany(
                    """
                    INSERT INTO deliveries (
                        match_id, innings_id, over_no, ball_no, ball_sequence, actual_delivery,
                        legal_delivery, batting_team_id, bowling_team_id, batter_id, bowler_id, non_striker_id,
                        runs_batter, runs_extras, runs_total, extras_type, is_boundary, boundary_type, is_dot_ball,
                        is_wicket, dismissal_type, player_out_id, fielder1_id, fielder2_id,
                        current_score, current_wickets, target_runs, required_runs, required_balls, required_run_rate,
                        phase, is_powerplay, is_middle, is_death, partnership_id, striker_end, non_striker_end
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    final_deliveries
                )
                deliveries_inserted += len(final_deliveries)

                # Insert Batting Innings
                batting_rows = []
                for b_id, b_stats in batting_stats.items():
                    runs = b_stats['runs']
                    balls = b_stats['balls']
                    sr = (runs * 100.0 / balls) if balls > 0 else 0.0
                    batting_rows.append((
                        match_id, innings_id, b_id, runs, balls, b_stats['fours'], b_stats['sixes'],
                        sr, b_stats['dismissal_type'], b_stats['dismissed_by']
                    ))
                    
                    if b_id not in match_player_career_contrib:
                        match_player_career_contrib[b_id] = {
                            'matches': 0, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                            'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
                        }
                    match_player_career_contrib[b_id]['innings'] += 1
                    match_player_career_contrib[b_id]['runs'] += runs
                    match_player_career_contrib[b_id]['balls'] += balls
                    match_player_career_contrib[b_id]['fours'] += b_stats['fours']
                    match_player_career_contrib[b_id]['sixes'] += b_stats['sixes']
                    if runs >= 100:
                        match_player_career_contrib[b_id]['hundreds'] += 1
                    elif runs >= 50:
                        match_player_career_contrib[b_id]['fifties'] += 1
                        
                db.executemany(
                    """
                    INSERT INTO batting_innings (
                        match_id, innings_id, batter_id, runs, balls, fours, sixes,
                        strike_rate, dismissal_type, dismissed_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batting_rows
                )

                # Insert Bowling Innings
                bowling_rows = []
                for b_id, b_stats in bowling_stats.items():
                    l_balls = b_stats['legal_balls']
                    overs_val = l_balls / 6.0
                    runs = b_stats['runs']
                    econ = runs / overs_val if overs_val > 0 else 0.0
                    
                    maidens = 0
                    for o_no, o_data in b_stats['overs_by_over'].items():
                        if o_data['runs_conceded'] == 0 and o_data['legal_balls'] == 6:
                            maidens += 1
                            
                    bowling_rows.append((
                        match_id, innings_id, b_id, overs_val, maidens, runs, b_stats['wickets'], econ
                    ))
                    
                    if b_id not in match_player_career_contrib:
                        match_player_career_contrib[b_id] = {
                            'matches': 0, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                            'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
                        }
                    match_player_career_contrib[b_id]['wickets'] += b_stats['wickets']
                    
                db.executemany(
                    """
                    INSERT INTO bowling_innings (
                        match_id, innings_id, bowler_id, overs, maidens, runs, wickets, economy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    bowling_rows
                )

                # Insert Partnerships
                partnership_rows = []
                for (p1, p2), p_stats in partnership_stats.items():
                    partnership_rows.append((match_id, innings_id, p1, p2, p_stats['runs'], p_stats['balls']))
                db.executemany(
                    """
                    INSERT INTO partnerships (match_id, innings_id, player1_id, player2_id, runs, balls)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    partnership_rows
                )

                # Insert Fall of Wickets
                fow_rows = []
                for wicket_no, fow_score, fow_over, out_id in fall_of_wickets_list:
                    fow_rows.append((match_id, innings_id, wicket_no, fow_score, fow_over, out_id))
                db.executemany(
                    """
                    INSERT INTO fall_of_wickets (match_id, innings_id, wicket_no, score, over, player_out_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    fow_rows
                )

                # Insert Over Summary
                over_rows = []
                for o_no, o_data in over_summary_stats.items():
                    over_rows.append((match_id, innings_id, o_no, o_data['runs'], o_data['wickets'], o_data['extras']))
                db.executemany(
                    """
                    INSERT INTO over_summary (match_id, innings_id, over, runs, wickets, extras)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    over_rows
                )

            # Update venues with results
            if winner_team_id:
                if len(innings_list) >= 2:
                    team2_name = innings_list[1].get("team")
                    team2_id_resolved = db.get_or_insert_team(team2_name)
                    if winner_team_id == team2_id_resolved:
                        match_venues_contrib[venue_id]['successful_chases'] = 1
                        match_venues_contrib[venue_id]['bowl_first_wins'] = 1
                    else:
                        match_venues_contrib[venue_id]['bat_first_wins'] = 1
                else:
                    match_venues_contrib[venue_id]['bat_first_wins'] = 1

            db.commit()
            matches_inserted += 1
            
            # --- TRANSACTION COMPLETE: MERGE INTO GLOBAL IN-MEMORY ACCUMULATORS ---
            
            for t_id, contrib in match_teams_contrib.items():
                if t_id not in global_teams:
                    global_teams[t_id] = {'matches': 0, 'wins': 0, 'losses': 0, 'ties': 0, 'runs_scored': 0, 'runs_conceded': 0}
                global_teams[t_id]['matches'] += contrib['matches']
                global_teams[t_id]['wins'] += contrib['wins']
                global_teams[t_id]['losses'] += contrib['losses']
                global_teams[t_id]['ties'] += contrib['ties']
                global_teams[t_id]['runs_scored'] += contrib['total_runs_scored']
                global_teams[t_id]['runs_conceded'] += contrib['total_runs_conceded']
                
            for v_id, contrib in match_venues_contrib.items():
                if v_id not in global_venues:
                    global_venues[v_id] = {
                        'matches': 0, 'first_inn_runs': [], 'second_inn_runs': [],
                        'highest_score': 0, 'lowest_score': 9999, 'successful_chases': 0,
                        'bat_first_wins': 0, 'bowl_first_wins': 0
                    }
                v_data = global_venues[v_id]
                v_data['matches'] += contrib['matches']
                if contrib['first_inn_runs'] is not None:
                    v_data['first_inn_runs'].append(contrib['first_inn_runs'])
                if contrib['second_inn_runs'] is not None:
                    v_data['second_inn_runs'].append(contrib['second_inn_runs'])
                v_data['highest_score'] = max(v_data['highest_score'], contrib['highest_score'])
                if contrib['lowest_score'] < 9999:
                    v_data['lowest_score'] = min(v_data['lowest_score'], contrib['lowest_score'])
                v_data['successful_chases'] += contrib['successful_chases']
                v_data['bat_first_wins'] += contrib['bat_first_wins']
                v_data['bowl_first_wins'] += contrib['bowl_first_wins']
                
            for p_id, contrib in match_player_career_contrib.items():
                if p_id not in global_player_career:
                    global_player_career[p_id] = {
                        'matches': 0, 'innings': 0, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0,
                        'hundreds': 0, 'fifties': 0, 'wickets': 0, 'catches': 0, 'run_outs': 0
                    }
                p_data = global_player_career[p_id]
                for key in p_data:
                    p_data[key] += contrib[key]
                    
            for m_key, contrib in match_matchups_contrib.items():
                if m_key not in global_matchups:
                    global_matchups[m_key] = {'balls': 0, 'runs': 0, 'dots': 0, 'fours': 0, 'sixes': 0, 'dismissals': 0}
                m_data = global_matchups[m_key]
                for key in m_data:
                    m_data[key] += contrib[key]
                    
            for pp_key, contrib in match_player_phase_contrib.items():
                if pp_key not in global_player_phase:
                    global_player_phase[pp_key] = {'balls': 0, 'runs': 0, 'outs': 0}
                pp_data = global_player_phase[pp_key]
                for key in pp_data:
                    pp_data[key] += contrib[key]
                    
            for bp_key, contrib in match_bowler_phase_contrib.items():
                if bp_key not in global_bowler_phase:
                    global_bowler_phase[bp_key] = {'legal_balls': 0, 'runs': 0, 'wickets': 0}
                bp_data = global_bowler_phase[bp_key]
                for key in bp_data:
                    bp_data[key] += contrib[key]

        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed for match {match_id}: {e}")
            skipped_matches.append(filename)
            continue
            
    logger.info("Ingestion loop completed. Writing global career aggregates...")
    
    try:
        db.begin_transaction()
        
        # 1. Player Career Table
        logger.info("Writing player career summaries...")
        player_career_rows = []
        for p_id, data in global_player_career.items():
            player_career_rows.append((
                p_id, data['matches'], data['innings'], data['runs'], data['balls'],
                data['fours'], data['sixes'], data['hundreds'], data['fifties'],
                data['wickets'], data['catches'], data['run_outs']
            ))
        db.executemany(
            """
            INSERT OR REPLACE INTO player_career (
                player_id, matches, innings, runs, balls, fours, sixes, hundreds, fifties, wickets, catches, run_outs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            player_career_rows
        )
        
        # 2. Player Ball Matchup Table
        logger.info("Writing player matchup summaries...")
        matchup_rows = []
        for (bat_id, bowl_id), data in global_matchups.items():
            matchup_rows.append((
                bat_id, bowl_id, data['balls'], data['runs'], data['dots'], data['fours'], data['sixes'], data['dismissals']
            ))
        db.executemany(
            """
            INSERT OR REPLACE INTO player_ball_matchup (
                batter_id, bowler_id, balls, runs, dots, fours, sixes, dismissals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            matchup_rows
        )
        
        # 3. Player Phase Stats Table
        logger.info("Writing player phase summaries...")
        player_phase_rows = []
        for (p_id, phase), data in global_player_phase.items():
            balls = data['balls']
            sr = (data['runs'] * 100.0 / balls) if balls > 0 else 0.0
            player_phase_rows.append((p_id, phase, balls, data['runs'], data['outs'], sr))
        db.executemany(
            """
            INSERT OR REPLACE INTO player_phase_stats (player_id, phase, balls, runs, outs, strike_rate)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            player_phase_rows
        )
        
        # 4. Bowler Phase Stats Table
        logger.info("Writing bowler phase summaries...")
        bowler_phase_rows = []
        for (p_id, phase), data in global_bowler_phase.items():
            overs = data['legal_balls'] / 6.0
            econ = data['runs'] / overs if overs > 0 else 0.0
            bowler_phase_rows.append((p_id, phase, overs, data['runs'], data['wickets'], econ))
        db.executemany(
            """
            INSERT OR REPLACE INTO bowler_phase_stats (player_id, phase, overs, runs, wkts, economy)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            bowler_phase_rows
        )
        
        # 5. Venue Statistics Table
        logger.info("Writing venue statistics...")
        venue_rows = []
        for v_id, data in global_venues.items():
            matches = data['matches']
            avg_1 = (sum(data['first_inn_runs']) / len(data['first_inn_runs'])) if data['first_inn_runs'] else 0.0
            avg_2 = (sum(data['second_inn_runs']) / len(data['second_inn_runs'])) if data['second_inn_runs'] else 0.0
            low_score = data['lowest_score'] if data['lowest_score'] < 9999 else 0
            venue_rows.append((
                v_id, matches, avg_1, avg_2, data['highest_score'], low_score,
                data['successful_chases'], data['bat_first_wins'], data['bowl_first_wins']
            ))
        db.executemany(
            """
            INSERT OR REPLACE INTO venue_statistics (
                venue_id, matches, avg_first_innings, avg_second_innings, highest_score, lowest_score,
                successful_chases, bat_first_wins, bowl_first_wins
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            venue_rows
        )
        
        # 6. Team Statistics Table
        logger.info("Writing team statistics...")
        team_rows = []
        for t_id, data in global_teams.items():
            matches = data['matches']
            avg_score = (data['runs_scored'] / matches) if matches > 0 else 0.0
            avg_conceded = (data['runs_conceded'] / matches) if matches > 0 else 0.0
            team_rows.append((
                t_id, matches, data['wins'], data['losses'], data['ties'], avg_score, avg_conceded
            ))
        db.executemany(
            """
            INSERT OR REPLACE INTO team_statistics (
                team_id, matches, wins, losses, ties, avg_score, avg_conceded
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            team_rows
        )
        
        db.commit()
        logger.info("Global career aggregates written successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to write global career aggregates: {e}")
        raise e
    finally:
        db.close()
        
    execution_time = time.time() - start_time
    
    db_size_bytes = 0
    if os.path.exists(db_path):
        db_size_bytes = os.path.getsize(db_path)
    db_size_mb = db_size_bytes / (1024 * 1024)
    
    total_players = len(db.player_cache)
    total_teams = len(db.team_cache)
    total_venues = len(db.venue_cache)
    
    print("\n" + "="*50)
    print("INGESTION PIPELINE COMPLETE")
    print("="*50)
    print(f"Matches inserted:        {matches_inserted}")
    print(f"Deliveries inserted:     {deliveries_inserted}")
    print(f"Players:                 {total_players}")
    print(f"Teams:                   {total_teams}")
    print(f"Venues:                  {total_venues}")
    print(f"Database size:           {db_size_mb:.2f} MB")
    print(f"Skipped matches:         {len(skipped_matches)}")
    if skipped_matches:
        print(f"  Skipped files: {', '.join(skipped_matches[:10])}" + ("..." if len(skipped_matches) > 10 else ""))
    print(f"Total execution time:    {execution_time:.2f} seconds")
    print("="*50 + "\n")

if __name__ == "__main__":
    parse_and_populate()
