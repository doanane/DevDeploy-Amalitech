from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class WebhookEventType(str, Enum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    WORKFLOW_RUN = "workflow_run"
    CHECK_RUN = "check_run"
    DEPLOYMENT = "deployment"
    PING = "ping"

class WebhookEventStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class WebhookEventBase(BaseModel):
    event_type: str
    action: Optional[str] = None
    delivery_id: Optional[str] = None
    status: WebhookEventStatus = WebhookEventStatus.RECEIVED

class WebhookEventCreate(WebhookEventBase):
    payload: Dict[str, Any]
    headers: Dict[str, str]
    project_id: int
    signature: Optional[str] = None

class WebhookEvent(WebhookEventBase):
    id: int
    project_id: int
    payload: Dict[str, Any]
    headers: Dict[str, str]
    received_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class WebhookConfig(BaseModel):
    webhook_url: str
    secret: Optional[str] = None
    events: List[str] = ["push", "workflow_run"]

class GitHubWebhookPayload(BaseModel):
    """
    Simplified GitHub webhook payload for common events
    """
    ref: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None
    workflow_run: Optional[Dict[str, Any]] = None
    check_run: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    
    class Config:
        extra = "allow"

class WebhookTestRequest(BaseModel):
    event_type: WebhookEventType = WebhookEventType.PING
    payload: Optional[Dict[str, Any]] = None
