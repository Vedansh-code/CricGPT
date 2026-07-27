import sqlite3
import os
import sys
# Ensure root directory is in python path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scripts.logging import logger
from scripts.utils import get_stable_player_id
from scripts.normalization import normalize_venue_name, normalize_city


class DatabaseManager:
    def __init__(self, db_path="data/database/cricgpt.db"):
        self.db_path = db_path
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self.conn = None
        self.connect()
        
        # In-memory caches for fast entity lookups
        self.team_cache = {}      # team_name -> team_id
        self.venue_cache = {}     # (venue_name, city) -> venue_id
        self.player_cache = {}    # player_name -> player_id
        self.official_cache = {}  # official_name -> official_id
        
        self.load_caches()

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, isolation_level=None)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON;")
            # Performance optimization
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.conn.execute("PRAGMA synchronous = NORMAL;")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def load_caches(self):
        """Pre-populate in-memory lookup caches from existing DB entries."""
        try:
            cursor = self.conn.cursor()
            
            # Load Teams
            cursor.execute("SELECT team_id, team_name FROM teams")
            for tid, name in cursor.fetchall():
                self.team_cache[name] = tid
                
            # Load Venues
            cursor.execute("SELECT venue_id, venue_name, city FROM venues")
            for vid, name, city in cursor.fetchall():
                self.venue_cache[(name, city)] = vid
                
            # Load Players
            cursor.execute("SELECT player_id, player_name FROM players")
            for pid, name in cursor.fetchall():
                self.player_cache[name] = pid
                
            # Load Officials
            cursor.execute("SELECT official_id, official_name FROM officials")
            for oid, name in cursor.fetchall():
                self.official_cache[name] = oid
                
        except sqlite3.OperationalError:
            # Tables might not be created yet, which is fine
            pass

    # --- LOOKUP AND INSERT HELPERS ---

    def get_or_insert_team(self, team_name: str) -> int:
        if team_name in self.team_cache:
            return self.team_cache[team_name]
            
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO teams (team_name) VALUES (?)", (team_name,))
        
        # If ignore occurred, select it
        cursor.execute("SELECT team_id FROM teams WHERE team_name = ?", (team_name,))
        row = cursor.fetchone()
        if row:
            team_id = row[0]
            self.team_cache[team_name] = team_id
            return team_id
        raise Exception(f"Failed to insert team: {team_name}")

    def get_or_insert_venue(self, venue_name: str, city: str = None) -> int:
        venue_name = normalize_venue_name(venue_name, city)
        city = normalize_city(venue_name, city)
        
        key = (venue_name, city)
        if key in self.venue_cache:
            return self.venue_cache[key]
            
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO venues (venue_name, city) VALUES (?, ?)", (venue_name, city))
        
        cursor.execute("SELECT venue_id FROM venues WHERE venue_name = ? AND (city = ? OR (city IS NULL AND ? IS NULL))", (venue_name, city, city))
        row = cursor.fetchone()
        if row:
            venue_id = row[0]
            self.venue_cache[key] = venue_id
            return venue_id
        raise Exception(f"Failed to insert venue: {venue_name}, {city}")

    def get_or_insert_player(self, player_name: str, registry: dict = None) -> str:
        """
        Get or insert player. If registry is provided, use it to resolve ID.
        Otherwise generate stable ID.
        """
        if player_name in self.player_cache:
            return self.player_cache[player_name]
            
        # Determine player ID
        registry_id = None
        if registry and player_name in registry:
            registry_id = registry[player_name]
            player_id = registry_id
        else:
            player_id = get_stable_player_id(player_name)
            
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO players (player_id, registry_id, player_name) VALUES (?, ?, ?)",
            (player_id, registry_id, player_name)
        )
        self.player_cache[player_name] = player_id
        return player_id

    def get_or_insert_official(self, official_name: str, role: str) -> int:
        if official_name in self.official_cache:
            return self.official_cache[official_name]
            
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO officials (official_name, role) VALUES (?, ?)", (official_name, role))
        
        cursor.execute("SELECT official_id FROM officials WHERE official_name = ?", (official_name,))
        row = cursor.fetchone()
        if row:
            official_id = row[0]
            self.official_cache[official_name] = official_id
            return official_id
        raise Exception(f"Failed to insert official: {official_name}")

    # --- TRANSACTION MANAGEMENT ---

    def begin_transaction(self):
        self.conn.execute("BEGIN TRANSACTION;")

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
        
    def execute(self, sql, params=()):
        return self.conn.execute(sql, params)

    def executemany(self, sql, params_list):
        return self.conn.executemany(sql, params_list)
