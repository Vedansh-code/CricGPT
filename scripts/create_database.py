import os
import sys


scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir in sys.path:
    sys.path.remove(scripts_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scripts.database import DatabaseManager
from scripts.models import CREATE_TABLES_SQL, CREATE_INDEXES_SQL
from scripts.logging import logger

def create_database(db_path="data/database/cricgpt.db"):
    logger.info(f"Initializing database at: {db_path}")
    db = DatabaseManager(db_path)
    
    try:
        # Create Tables
        logger.info("Creating tables...")
        for sql in CREATE_TABLES_SQL:
            db.execute(sql)
            
        # Create Indexes
        logger.info("Creating indexes...")
        for sql in CREATE_INDEXES_SQL:
            db.execute(sql)
            
        db.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    create_database()
