import os
import sys

# Prevent shadowing of standard logging library
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir in sys.path:
    sys.path.remove(scripts_dir)

import logging

def setup_logging(log_file="data/database/ingestion.log"):
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    logger = logging.getLogger("CricGPT")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.WARNING) # Log warnings and errors to file
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

logger = setup_logging()
