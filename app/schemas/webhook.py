# app/schemas/webhook.py - FIXED
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class WebhookEventType(str, Enum):
    PUSH = "push"
    WORKFLOW_RUN = "workflow_run"
    PING = "ping"
    PULL_REQUEST = "pull_request"
    CHECK_RUN = "check_run"

class WebhookTestRequest(BaseModel):
    event_type: WebhookEventType = WebhookEventType.PING
    payload: Optional[Dict[str, Any]] = None

class WebhookConfig(BaseModel):
    url: HttpUrl
    secret: str
    events: List[str] = ["push", "workflow_run", "ping"]
    active: bool = True

class WebhookEventResponse(BaseModel):
    id: int
    event_type: str
    status: str
    project_id: Optional[int]
    created_at: datetime
    processed_at: Optional[datetime]
    delivery_attempts: int
    payload_summary: Dict[str, Any]
    
    class Config:
        from_attributes = True

class GitHubWebhookPayload(BaseModel):
    ref: Optional[str] = None
    after: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    workflow_run: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None
    action: Optional[str] = None