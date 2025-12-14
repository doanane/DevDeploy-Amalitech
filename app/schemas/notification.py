# app/schemas/notification.py - FIXED
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    BUILD_FAILED = "build_failed"
    BUILD_SUCCESS = "build_success"
    BUILD_STARTED = "build_started"
    DEPLOYMENT_FAILED = "deployment_failed"
    DEPLOYMENT_SUCCESS = "deployment_success"
    SYSTEM_ALERT = "system_alert"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEB = "web"
    WEBHOOK = "webhook"

class NotificationCreate(BaseModel):
    type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    channel: NotificationChannel = NotificationChannel.WEB
    user_id: int
    project_id: Optional[int] = None
    build_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    channel: str
    status: str
    read: bool
    created_at: datetime
    read_at: Optional[datetime]
    project: Optional[Dict[str, Any]] = None
    build: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class NotificationPreferences(BaseModel):
    email_enabled: bool = True
    slack_enabled: bool = False
    web_enabled: bool = True
    webhook_url: Optional[str] = None
    notify_on_build_fail: bool = True
    notify_on_build_success: bool = False
    notify_on_deployment: bool = True
    notify_on_system_alerts: bool = True