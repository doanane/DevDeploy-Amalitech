# app/api/webhooks.py - PRODUCTION READY VERSION
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import json
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.models.project import Project
from app.models.build import Build
from app.models.webhook import WebhookEvent as WebhookEventModel
from app.schemas.webhook import (
    WebhookConfig,
    WebhookTestRequest,
    GitHubWebhookPayload
)
from app.services.webhook_parser import WebhookVerifier, GitHubWebhookParser
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# ========== REAL GITHUB WEBHOOK ENDPOINT (PRODUCTION) ==========
@router.post("/github", status_code=202)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    GitHub Webhook Receiver - Production Endpoint
    
    Receives GitHub webhooks with these standard headers:
    - X-GitHub-Event: Type of event (push, ping, workflow_run, etc.)
    - X-GitHub-Delivery: Unique delivery ID
    - X-Hub-Signature-256: HMAC signature for security (optional in testing)
    
    This endpoint accepts ANY JSON payload from GitHub.
    """
    try:
        # Read raw body for signature verification
        raw_body = await request.body()
        
        # Try to parse JSON (allow empty)
        try:
            if raw_body:
                body_json = json.loads(raw_body)
            else:
                body_json = {}
        except json.JSONDecodeError:
            # If invalid JSON, still accept it but log
            body_json = {"raw_body": raw_body.decode('utf-8', errors='ignore')}
        
        # Get GitHub headers
        headers = dict(request.headers)
        event_type = headers.get("X-GitHub-Event", "ping")
        delivery_id = headers.get("X-GitHub-Delivery", str(uuid.uuid4()))
        signature = headers.get("X-Hub-Signature-256")
        
        # Create webhook event
        webhook_event = WebhookEventModel(
            event_type=event_type,
            delivery_id=delivery_id,
            signature=signature,
            status="received",
            payload=body_json,
            headers=headers,
            project_id=None,
        )
        
        db.add(webhook_event)
        db.commit()
        db.refresh(webhook_event)
        
        # Process in background
        background_tasks.add_task(
            process_github_webhook_background,
            webhook_event.id,
            raw_body,
            signature,
            event_type,
            delivery_id,
        )
        
        return {
            "status": "accepted",
            "message": "Webhook received and queued for processing",
            "event_id": webhook_event.id,
            "event_type": event_type,
            "delivery_id": delivery_id,
            "received_at": webhook_event.received_at.isoformat(),
        }
        
    except Exception as e:
        # Log error but still return 202 (GitHub expects 2xx for successful receipt)
        print(f"Error in webhook receiver: {e}")
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted_with_errors",
                "message": "Webhook received but encountered processing errors",
                "error": str(e)
            }
        )

# ========== SIMPLE TEST ENDPOINT (FOR DEVELOPERS) ==========
@router.post("/github/test", status_code=200)
async def github_webhook_test(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Simple Webhook Test Endpoint - For Developer Testing
    
    Does NOT require GitHub headers. Just send JSON.
    
    Example:
    ```json
    {
      "event": "ping",
      "message": "Test webhook"
    }
    ```
    """
    try:
        # Get JSON payload
        try:
            body = await request.json()
        except:
            body = {}
        
        event = body.get("event", "ping")
        delivery_id = str(uuid.uuid4())
        
        # Create and process immediately
        webhook = WebhookEventModel(
            event_type=event,
            delivery_id=delivery_id,
            status="received",
            payload=body,
            headers=dict(request.headers),
            project_id=None,
        )
        
        db.add(webhook)
        db.commit()
        
        # Process immediately
        webhook.status = "processed"
        webhook.processed_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Test webhook '{event}' processed successfully",
            "event_id": webhook.id,
            "delivery_id": delivery_id,
            "processed_at": webhook.processed_at.isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing test webhook: {str(e)}"
        )

# ========== EXISTING ENDPOINTS (UNCHANGED) ==========
@router.post("/test", response_model=dict)
async def test_webhook(
    test_request: WebhookTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Authenticated webhook test endpoint"""
    project = db.query(Project).filter(
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No projects found for testing"
        )
    
    test_payload = test_request.payload or {
        "action": "test",
        "repository": {
            "name": project.name,
            "html_url": project.repository_url,
        },
        "sender": {
            "login": "test_user",
        },
        "zen": "Keep it logically awesome.",
    }
    
    webhook_event = WebhookEventModel(
        event_type=test_request.event_type.value,
        delivery_id=str(uuid.uuid4()),
        status="received",
        payload=test_payload,
        headers={"x-test-event": "true"},
        project_id=project.id,
    )
    
    db.add(webhook_event)
    db.commit()
    db.refresh(webhook_event)
    
    process_test_webhook(webhook_event.id, db)
    
    return {
        "status": "success",
        "message": f"Test webhook {test_request.event_type.value} processed",
        "event_id": webhook_event.id,
        "project_id": project.id,
    }

@router.get("/config/{project_id}", response_model=WebhookConfig)
async def get_webhook_config(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get webhook configuration for a project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.webhook_url:
        project.webhook_url = f"{request.base_url}webhooks/github"
        db.commit()
    
    if not project.webhook_secret:
        import secrets
        project.webhook_secret = secrets.token_hex(32)
        db.commit()
    
    return WebhookConfig(
        webhook_url=project.webhook_url,
        secret=project.webhook_secret,
        events=["push", "workflow_run", "check_run"]
    )

@router.get("/events/{project_id}", response_model=List[dict])
async def get_webhook_events(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    """Get webhook events for a project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    events = db.query(WebhookEventModel).filter(
        WebhookEventModel.project_id == project_id
    ).order_by(
        WebhookEventModel.received_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "action": event.action,
            "delivery_id": event.delivery_id,
            "status": event.status,
            "project_id": event.project_id,
            "received_at": event.received_at,
            "processed_at": event.processed_at,
        }
        for event in events
    ]

# ========== BACKGROUND TASK FUNCTIONS ==========
async def process_github_webhook_background(
    event_id: int,
    raw_body: bytes,
    signature: Optional[str],
    event_type: str,
    delivery_id: str,
):
    """Process webhook in background"""
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        webhook_event = db.query(WebhookEventModel).filter(
            WebhookEventModel.id == event_id
        ).first()
        
        if not webhook_event:
            return
        
        webhook_event.status = "processing"
        db.commit()
        
        # Try to find matching project
        payload = webhook_event.payload
        project = find_project_from_webhook(db, payload)
        
        if project:
            webhook_event.project_id = project.id
            
            # Verify signature if available
            if project.webhook_secret and signature:
                try:
                    is_valid = WebhookVerifier.verify_github_signature(
                        raw_body,
                        signature,
                        project.webhook_secret
                    )
                    if not is_valid:
                        webhook_event.status = "failed_verification"
                        db.commit()
                        return
                except Exception as e:
                    print(f"Signature verification error: {e}")
        
        # Process based on event type
        try:
            if event_type == "workflow_run":
                process_workflow_run_event(db, project, payload) if project else None
            elif event_type == "check_run":
                process_check_run_event(db, project, payload) if project else None
            elif event_type == "push":
                process_push_event(db, project, payload) if project else None
        except Exception as e:
            print(f"Error processing {event_type} event: {e}")
        
        webhook_event.status = "processed"
        webhook_event.processed_at = datetime.now(timezone.utc)
        db.commit()
        
    except Exception as e:
        print(f"Error in background webhook processing: {e}")
        if db and 'webhook_event' in locals():
            webhook_event.status = "failed"
            db.commit()
    finally:
        if db:
            db.close()

def process_test_webhook(event_id: int, db: Session):
    """Process test webhook"""
    webhook_event = db.query(WebhookEventModel).filter(
        WebhookEventModel.id == event_id
    ).first()
    
    if webhook_event:
        webhook_event.status = "processed"
        webhook_event.processed_at = datetime.now(timezone.utc)
        db.commit()

def find_project_from_webhook(db: Session, payload: Dict[str, Any]) -> Optional[Project]:
    """Find project matching webhook repository"""
    repo_url = payload.get("repository", {}).get("html_url")
    if not repo_url:
        return None
    
    project = db.query(Project).filter(
        Project.repository_url.ilike(f"%{repo_url}%")
    ).first()
    
    return project

def process_workflow_run_event(db: Session, project: Project, payload: Dict[str, Any]):
    """Process GitHub workflow_run event"""
    workflow_run = payload.get("workflow_run", {})
    conclusion = workflow_run.get("conclusion")
    head_sha = workflow_run.get("head_sha")
    
    if conclusion in ["success", "failure", "cancelled"] and head_sha:
        build = db.query(Build).filter(
            Build.project_id == project.id,
            Build.commit_hash == head_sha
        ).first()
        
        if build:
            build.status = "success" if conclusion == "success" else "failed"
            build.completed_at = datetime.now(timezone.utc)
            db.commit()

def process_check_run_event(db: Session, project: Project, payload: Dict[str, Any]):
    """Process GitHub check_run event"""
    check_run = payload.get("check_run", {})
    conclusion = check_run.get("conclusion")
    head_sha = check_run.get("head_sha")
    
    if conclusion in ["success", "failure"] and head_sha:
        build = db.query(Build).filter(
            Build.project_id == project.id,
            Build.commit_hash == head_sha
        ).first()
        
        if build:
            build.status = "success" if conclusion == "success" else "failed"
            db.commit()

def process_push_event(db: Session, project: Project, payload: Dict[str, Any]):
    """Process GitHub push event"""
    head_commit = payload.get("head_commit", {})
    commit_hash = head_commit.get("id")
    commit_message = head_commit.get("message")
    
    if commit_hash and project.status == "active":
        from app.services.build_runner import trigger_build
        trigger_build(db, project.id, commit_hash, commit_message)