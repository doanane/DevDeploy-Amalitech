# app/api/webhooks.py - Clean version
import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    Request, 
    Header, 
    BackgroundTasks,
    status
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.webhook import WebhookEvent
from app.models.user import User
from app.schemas.webhook import WebhookConfig, WebhookTestRequest, WebhookEventResponse
from app.api.auth import get_current_user
from app.services.webhook_service import WebhookService
from app.core.security import verify_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

# At the top of app/api/webhooks.py, add this:
try:
    from app.services.webhook_service import WebhookService
    webhook_service_available = True
except ImportError as e:
    logger.error(f"Failed to import WebhookService: {e}")
    webhook_service_available = False
except Exception as e:
    logger.error(f"Error importing WebhookService: {e}")
    webhook_service_available = False

# Then modify the endpoints that use WebhookService:
@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
    db: Session = Depends(get_db)
):
    """Receive GitHub webhooks."""
    if not webhook_service_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook service not available"
        )
    
    
@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
    db: Session = Depends(get_db)
):
    """
    Receive GitHub webhooks with signature verification and async processing.
    """
    # Read raw body for signature verification
    raw_body = await request.body()
    
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(
        "GitHub webhook received from %s - Event: %s, Delivery: %s",
        client_ip, x_github_event, x_github_delivery
    )
    
    try:
        # Parse JSON payload
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON payload: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Get event type
        event_type = x_github_event or "ping"
        
        # Store headers for logging
        headers = {
            "user_agent": user_agent,
            "delivery_id": x_github_delivery,
            "client_ip": client_ip
        }
        
        # Try to find project for signature verification
        repository = payload.get("repository", {})
        repo_url = repository.get("html_url", "")
        
        project = None
        if repo_url:
            project = db.query(Project).filter(
                Project.repository_url.ilike(f"%{repo_url}%"),
                Project.webhook_enabled == True
            ).first()
        
        # Verify signature if project has secret
        if project and project.webhook_secret and x_hub_signature_256:
            try:
                is_valid = WebhookService.verify_github_signature(
                    raw_body,
                    x_hub_signature_256,
                    project.webhook_secret
                )
                
                if not is_valid:
                    logger.warning(
                        "Invalid signature for webhook from %s (Project: %s, IP: %s)",
                        repo_url, project.name, client_ip
                    )
                    
                    # Log failed verification attempt
                    webhook_event = WebhookEvent(
                        event_type=f"github.{event_type}",
                        payload=payload,
                        headers=headers,
                        signature=x_hub_signature_256,
                        delivery_id=x_github_delivery or f"failed_{hash(raw_body)}",
                        status="failed_verification",
                        project_id=project.id if project else None
                    )
                    
                    db.add(webhook_event)
                    db.commit()
                    
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid webhook signature"
                    )
                    
            except ValueError as e:
                logger.error("Signature verification error: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        # Process webhook in background
        background_tasks.add_task(
            process_webhook_async,
            db,
            payload,
            event_type,
            x_hub_signature_256,
            headers,
            project.id if project else None
        )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "accepted",
                "message": "Webhook received and queued for processing",
                "event_type": event_type,
                "delivery_id": x_github_delivery,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing GitHub webhook: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/test", response_model=Dict[str, Any])
async def test_webhook(
    test_request: WebhookTestRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test webhook endpoint with validation and security.
    """
    # Get user's first active project
    project = db.query(Project).filter(
        Project.owner_id == current_user.id,
        Project.status == "active"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active projects found for testing. Create a project first."
        )
    
    # Generate test payload
    test_payload = test_request.payload or {
        "action": "test",
        "repository": {
            "id": 123456789,
            "name": project.name,
            "full_name": f"{current_user.username}/{project.name}",
            "html_url": project.repository_url,
            "private": True
        },
        "sender": {
            "login": current_user.username,
            "id": current_user.id
        },
        "organization": {
            "login": "test-org"
        },
        "zen": "Keep it logically awesome.",
        "hook_id": 123456,
        "hook": {
            "type": "Repository",
            "id": 123456,
            "active": True
        }
    }
    
    # Generate test signature
    base_url = str(request.base_url).rstrip("/")
    config = WebhookService.get_webhook_config(project, base_url)
    secret = config["secret"]
    
    # Create signature for test
    payload_bytes = json.dumps(test_payload).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Process test webhook
    try:
        webhook_event = WebhookService.process_github_webhook(
            db=db,
            payload=test_payload,
            event_type=test_request.event_type.value,
            signature=f"sha256={signature}",
            headers={"test": "true", "user_id": str(current_user.id)}
        )
        
        return {
            "status": "success",
            "message": f"Test webhook '{test_request.event_type.value}' processed successfully",
            "event_id": webhook_event.id,
            "project_id": project.id,
            "project_name": project.name,
            "webhook_url": f"{base_url}/webhooks/github",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Test webhook failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test webhook processing failed: {str(e)}"
        )

@router.get("/config/{project_id}", response_model=WebhookConfig)
async def get_webhook_config(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get webhook configuration for secure GitHub integration.
    """
    # Verify project ownership and access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
        Project.status == "active"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Get base URL
    base_url = str(request.base_url).rstrip("/")
    
    # Generate configuration
    config = WebhookService.get_webhook_config(project, base_url)
    
    return WebhookConfig(
        url=config["webhook_url"],
        secret=config["secret"],
        events=config["events"],
        active=True,
        content_type=config["content_type"],
        insecure_ssl=config["insecure_ssl"]
    )

@router.get("/events/{project_id}", response_model=Dict[str, Any])
async def get_webhook_events(
    project_id: int,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get webhook events with filtering, pagination, and statistics.
    """
    # Validate ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Validate pagination
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be >= 0"
        )
    
    # Build query
    query = db.query(WebhookEvent).filter(
        WebhookEvent.project_id == project_id
    )
    
    # Apply filters
    if status:
        query = query.filter(WebhookEvent.status == status)
    
    if event_type:
        query = query.filter(WebhookEvent.event_type.ilike(f"%{event_type}%"))
    
    # Get total count
    total_count = query.count()
    
    # Get paginated results
    events = query.order_by(
        WebhookEvent.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Get statistics
    stats = db.query(
        WebhookEvent.status,
        db.func.count(WebhookEvent.id)
    ).filter(
        WebhookEvent.project_id == project_id
    ).group_by(WebhookEvent.status).all()
    
    return {
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "status": event.status,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "processed_at": event.processed_at.isoformat() if event.processed_at else None,
                "delivery_attempts": event.delivery_attempts,
                "payload_summary": event.get_payload_summary(),
                "build_id": event.build_id
            }
            for event in events
        ],
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        },
        "statistics": {
            status: count for status, count in stats
        }
    }

@router.post("/{webhook_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_webhook(
    webhook_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry a failed webhook delivery with validation and background processing.
    """
    # Get webhook event
    webhook_event = db.query(WebhookEvent).get(webhook_id)
    
    if not webhook_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook event not found"
        )
    
    # Verify access through project ownership
    if webhook_event.project_id:
        project = db.query(Project).filter(
            Project.id == webhook_event.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this webhook event"
            )
    
    # Validate webhook can be retried
    if webhook_event.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry webhook with status: {webhook_event.status}"
        )
    
    if webhook_event.delivery_attempts >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum retry attempts exceeded"
        )
    
    # Queue retry in background
    background_tasks.add_task(
        retry_webhook_async,
        db,
        webhook_id,
        current_user.id
    )
    
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "accepted",
            "message": "Webhook retry queued",
            "webhook_id": webhook_id,
            "attempt": webhook_event.delivery_attempts + 1,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Background task functions
async def process_webhook_async(
    db: Session,
    payload: Dict[str, Any],
    event_type: str,
    signature: Optional[str],
    headers: Dict[str, str],
    project_id: Optional[int]
):
    """Process webhook asynchronously."""
    from app.database import SessionLocal
    local_db = SessionLocal()
    
    try:
        WebhookService.process_github_webhook(
            db=local_db,
            payload=payload,
            event_type=event_type,
            signature=signature,
            headers=headers
        )
    except Exception as e:
        logger.error("Background webhook processing failed: %s", e, exc_info=True)
    finally:
        local_db.close()

async def retry_webhook_async(db: Session, webhook_id: int, user_id: int):
    """Retry webhook asynchronously."""
    from app.database import SessionLocal
    local_db = SessionLocal()
    
    try:
        success = WebhookService.retry_failed_webhook(local_db, webhook_id)
        if success:
            logger.info("User %s retried webhook %s", user_id, webhook_id)
        else:
            logger.warning("User %s failed to retry webhook %s", user_id, webhook_id)
    except Exception as e:
        logger.error("Webhook retry failed: %s", e, exc_info=True)
    finally:
        local_db.close()
