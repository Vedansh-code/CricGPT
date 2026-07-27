import os
import sqlite3

# The database path can be overridden by environment variable for testing
DEFAULT_DB_PATH = os.path.join("data", "database", "cricgpt.db")
DB_PATH = os.environ.get("CRICGPT_DB_PATH", DEFAULT_DB_PATH)


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Establish and return a new SQLite database connection.
    Configures Row factory and enables foreign key constraints.
    
    Args:
        db_path (str, optional): Custom path to SQLite DB file. Defaults to DB_PATH.
        
    Returns:
        sqlite3.Connection: A configured sqlite3 Connection object.
    """
    target_path = db_path if db_path is not None else DB_PATH
    
    # Ensure database file exists before trying to connect
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Database file not found at: {os.path.abspath(target_path)}")
        
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    
    return conn
