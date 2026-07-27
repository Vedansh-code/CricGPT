import os
from typing import List

class Settings:
    PROJECT_NAME: str = "CricGPT API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # Allow custom CORS origins through environment variables
    env_origins = os.environ.get("CRICGPT_CORS_ORIGINS")
    if env_origins:
        CORS_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()]

settings = Settings()
