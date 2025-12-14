# app/services/webhook_service.py - SIMPLIFIED WORKING VERSION
import hmac
import hashlib
import json
import logging
import secrets
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Project, Build, WebhookEvent

logger = logging.getLogger(__name__)

class WebhookService:
    """Simple webhook service."""
    
    @staticmethod
    def verify_github_signature(
        payload_body: bytes, 
        signature_header: str, 
        secret: str
    ) -> bool:
        """Verify GitHub webhook signature."""
        if not signature_header or not secret:
            return False
            
        if not signature_header.startswith("sha256="):
            return False
            
        signature = signature_header[7:]
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            msg=payload_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def process_github_webhook(
        db: Session,
        payload: Dict[str, Any],
        event_type: str,
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookEvent:
        """Process GitHub webhook."""
        webhook_event = WebhookEvent(
            event_type=f"github.{event_type}",
            payload=payload,
            headers=headers or {},
            signature=signature,
            status="received",
            created_at=datetime.utcnow()
        )
        
        db.add(webhook_event)
        db.flush()
        
        try:
            # For push events, create a build
            if event_type == "push":
                repository = payload.get("repository", {})
                ref = payload.get("ref", "")
                repo_url = repository.get("html_url")
                
                if repo_url and ref:
                    project = db.query(Project).filter(
                        Project.repository_url.ilike(f"%{repo_url}%"),
                        Project.status == "active"
                    ).first()
                    
                    if project:
                        webhook_event.project_id = project.id
                        
                        branch = ref.replace("refs/heads/", "")
                        head_commit = payload.get("head_commit", {})
                        commit_hash = head_commit.get("id", "")
                        
                        if commit_hash and branch == project.branch:
                            # Create build
                            build = Build(
                                project_id=project.id,
                                trigger_type="webhook",
                                commit_hash=commit_hash,
                                commit_message=head_commit.get("message", "Push event"),
                                branch=branch,
                                status="pending",
                                created_at=datetime.utcnow(),
                                build_metadata={
                                    "webhook_event_id": webhook_event.id
                                }
                            )
                            db.add(build)
            
            webhook_event.status = "processed"
            webhook_event.processed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            webhook_event.status = "failed"
        
        db.commit()
        return webhook_event
    
    @staticmethod
    def get_webhook_config(project: Project, base_url: str) -> Dict[str, Any]:
        """Get webhook configuration."""
        if not project.webhook_secret:
            project.webhook_secret = secrets.token_urlsafe(32)
        
        return {
            "webhook_url": f"{base_url}/webhooks/github",
            "secret": project.webhook_secret,
            "events": ["push", "workflow_run", "ping"],
            "content_type": "application/json",
            "insecure_ssl": "0",
            "active": True
        }
    
    @staticmethod
    def get_recent_webhook_events(
        db: Session,
        project_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[WebhookEvent], int]:
        """Get recent webhook events."""
        total = db.query(WebhookEvent).filter(
            WebhookEvent.project_id == project_id
        ).count()
        
        events = db.query(WebhookEvent).filter(
            WebhookEvent.project_id == project_id
        ).order_by(
            WebhookEvent.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return events, total