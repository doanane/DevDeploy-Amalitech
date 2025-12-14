# app/api/monitoring.py - SIMPLIFIED SYNC VERSION
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import psutil
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = logging.getLogger(__name__)

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database health check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # System metrics
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent if hasattr(psutil, 'disk_usage') else 0
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@router.get("/metrics")
def get_metrics():
    """Get application metrics."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
        }
    }

@router.get("/queue")
def get_queue_status():
    """Get build queue status."""
    return {
        "queue_status": {
            "pending": 0,
            "running": 0,
            "max_concurrent": 3
        }
    }

__all__ = ["router"]