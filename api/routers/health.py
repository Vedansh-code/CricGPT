from fastapi import APIRouter
from api.config import settings
from analytics.database import get_connection

router = APIRouter()

@router.get("", response_model=dict)
def get_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@router.get("/ready", response_model=dict)
def get_ready():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    finally:
        conn.close()
    return {
        "status": "ready",
        "database": "connected"
    }
