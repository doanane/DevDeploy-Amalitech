# app/api/notifications.py - SIMPLIFIED SYNC VERSION
from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/")
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get notifications for the current user."""
    return {
        "notifications": [],
        "total": 0,
        "unread": 0,
        "limit": limit,
        "offset": offset
    }

@router.get("/preferences")
def get_notification_preferences():
    """Get notification preferences."""
    return {
        "email_enabled": True,
        "slack_enabled": False,
        "web_enabled": True,
        "notify_on_build_fail": True
    }

@router.get("/stats")
def get_notification_stats():
    """Get notification statistics."""
    return {
        "total": 0,
        "unread": 0,
        "by_type": {}
    }

__all__ = ["router"]