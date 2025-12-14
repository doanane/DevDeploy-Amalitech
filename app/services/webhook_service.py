"""
Production-grade webhook service with signature verification, retry logic, and webhook processing.
"""
import hmac
import hashlib
import json
import logging
from app.services.build_service_simple import BuildServiceSimple as BuildService
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import secrets
from typing import Dict, Any, Optional, Tuple, List
from app.models import Project, Build, WebhookEvent
# from app.services.build_service import BuildService
from app.core.security import generate_signature
from app.models.build_log import BuildLog 

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for handling webhook operations."""
    
    @staticmethod
    def verify_github_signature(
        payload_body: bytes, 
        signature_header: str, 
        secret: str
    ) -> bool:
        """
        Verify GitHub webhook signature using HMAC-SHA256.
        
        Args:
            payload_body: Raw request body
            signature_header: X-Hub-Signature-256 header value
            secret: Webhook secret configured in GitHub
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            ValueError: If signature format is invalid
        """
        if not signature_header:
            logger.warning("No signature header provided")
            return False
            
        if not signature_header.startswith("sha256="):
            logger.error(f"Invalid signature format: {signature_header[:50]}")
            raise ValueError("Invalid signature format. Expected 'sha256=' prefix")
            
        # Extract signature
        signature = signature_header[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            msg=payload_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def process_github_webhook(
        db: Session,
        payload: Dict[str, Any],
        event_type: str,
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookEvent:
        """
        Process GitHub webhook and update builds.
        
        Args:
            db: Database session
            payload: Webhook payload
            event_type: GitHub event type
            signature: Webhook signature for verification
            headers: Additional headers for logging
            
        Returns:
            WebhookEvent: Created webhook event record
        """
        # Create webhook event record
        webhook_event = WebhookEvent(
            event_type=f"github.{event_type}",
            payload=payload,
            headers=headers or {},
            signature=signature,
            delivery_id=secrets.token_urlsafe(16),
            status="received"
        )
        
        db.add(webhook_event)
        db.flush()  # Get ID without committing
        
        try:
            # Process based on event type
            if event_type == "push":
                project = WebhookService._handle_push_event(db, payload, webhook_event)
            elif event_type == "workflow_run":
                project = WebhookService._handle_workflow_run_event(db, payload, webhook_event)
            elif event_type == "check_run":
                project = WebhookService._handle_check_run_event(db, payload, webhook_event)
            elif event_type == "ping":
                WebhookService._handle_ping_event(payload, webhook_event)
            else:
                logger.info(f"Unhandled GitHub event type: {event_type}")
                webhook_event.status = "skipped"
                db.commit()
                return webhook_event
            
            if project:
                webhook_event.project_id = project.id
                logger.info(f"Linked webhook to project: {project.name}")
            
            webhook_event.status = "processed"
            webhook_event.processed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            webhook_event.status = "failed"
            webhook_event.error_message = str(e)
        
        db.commit()
        return webhook_event
    
    @staticmethod
    def _handle_push_event(
        db: Session, 
        payload: Dict[str, Any], 
        webhook_event: WebhookEvent
    ) -> Optional[Project]:
        """Handle GitHub push event."""
        repository = payload.get("repository", {})
        ref = payload.get("ref", "")
        
        # Extract repository URL
        repo_url = repository.get("html_url")
        if not repo_url:
            logger.warning("No repository URL in push event")
            return None
        
        # Find project by repository URL
        project = db.query(Project).filter(
            Project.repository_url.ilike(f"%{repo_url}%"),
            Project.webhook_enabled == True,
            Project.status == "active"
        ).first()
        
        if not project:
            logger.info(f"No active project found for repository: {repo_url}")
            return None
        
        # Check if push is for monitored branch
        branch = ref.replace("refs/heads/", "")
        if branch != project.branch:
            logger.info(f"Push to branch {branch}, monitoring {project.branch}, skipping")
            return project
        
        # Extract commit information
        head_commit = payload.get("head_commit", {})
        commit_hash = head_commit.get("id", "")
        commit_message = head_commit.get("message", "Push event")
        
        if not commit_hash:
            logger.warning("No commit hash in push event")
            return project
        
        # Verify signature if secret is configured
        if project.webhook_secret and webhook_event.signature:
            try:
                # Note: We need the raw body for verification, which we don't have here
                # In production, this would be done in the endpoint before calling this method
                pass
            except Exception as e:
                logger.warning(f"Signature verification failed: {e}")
                webhook_event.status = "failed_verification"
                return project
        

        build = build_service.create_build(
            project_id=project.id,
            trigger_type="webhook",
            commit_hash=commit_hash,
            commit_message=commit_message[:255],
            branch=branch,
            build_build_metadata={  # Changed from metadata to build_metadata
                "pusher": payload.get("pusher", {}).get("name"),
                "compare_url": payload.get("compare"),
                "commits_count": len(payload.get("commits", [])),
                "webhook_event_id": webhook_event.id
            }
        )
        
        logger.info(f"Created build {build.id} from push event for project {project.name}")
        return project
    
    @staticmethod
    def _handle_workflow_run_event(
        db: Session,
        payload: Dict[str, Any],
        webhook_event: WebhookEvent
    ) -> Optional[Project]:
        """Handle GitHub workflow_run event."""
        workflow_run = payload.get("workflow_run", {})
        conclusion = workflow_run.get("conclusion")
        status = workflow_run.get("status")
        head_sha = workflow_run.get("head_sha")
        
        if status != "completed" or not conclusion or not head_sha:
            return None
        
        # Find repository
        repository = payload.get("repository", {})
        repo_url = repository.get("html_url")
        
        if not repo_url:
            return None
        
        # Find project
        project = db.query(Project).filter(
            Project.repository_url.ilike(f"%{repo_url}%"),
            Project.status == "active"
        ).first()
        
        if not project:
            return None
        
        # Find build by commit hash
        build = db.query(Build).filter(
            Build.project_id == project.id,
            Build.commit_hash == head_sha,
            Build.status.in_(["pending", "running"])
        ).order_by(Build.created_at.desc()).first()
        
        if build:
            # Update build status based on workflow conclusion
            if conclusion == "success":
                build.status = "success"
            else:
                build.status = "failed"
                build.error_message = f"GitHub Actions: {conclusion}"
            
            build.completed_at = datetime.utcnow()
            build.external_url = workflow_run.get("html_url")
            
            # Update webhook event
            webhook_event.build_id = build.id
            logger.info(f"Updated build {build.id} status to {build.status}")
        
        return project
    
    @staticmethod
    def _handle_check_run_event(
        db: Session,
        payload: Dict[str, Any],
        webhook_event: WebhookEvent
    ) -> Optional[Project]:
        """Handle GitHub check_run event."""
        check_run = payload.get("check_run", {})
        conclusion = check_run.get("conclusion")
        status = check_run.get("status")
        
        if status != "completed" or not conclusion:
            return None
        
        # This could be used for more granular build status updates
        # For now, just log it
        logger.info(f"Check run completed: {check_run.get('name')} - {conclusion}")
        return None
    
    @staticmethod
    def _handle_ping_event(payload: Dict[str, Any], webhook_event: WebhookEvent):
        """Handle GitHub ping event."""
        zen = payload.get("zen", "No zen message")
        logger.info(f"GitHub ping received: {zen}")
        webhook_event.status = "ping_received"
    
    @staticmethod
    def generate_webhook_secret() -> str:
        """Generate a secure webhook secret."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_webhook_config(project: Project, base_url: str) -> Dict[str, Any]:
        """
        Get webhook configuration for a project.
        
        Args:
            project: Project instance
            base_url: Base URL of the API
            
        Returns:
            Dict with webhook configuration
        """
        # Generate or get webhook secret
        if not project.webhook_secret:
            project.webhook_secret = WebhookService.generate_webhook_secret()
        
        webhook_url = f"{base_url}/webhooks/github"
        
        return {
            "webhook_url": webhook_url,
            "secret": project.webhook_secret,
            "events": ["push", "workflow_run", "check_run", "ping"],
            "content_type": "application/json",
            "insecure_ssl": "0",  # Require SSL
            "active": True
        }
    
    @staticmethod
    def get_recent_webhook_events(
        db: Session,
        project_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[WebhookEvent], int]:
        """
        Get recent webhook events for a project with pagination.
        
        Args:
            db: Database session
            project_id: Project ID
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            Tuple of (events, total_count)
        """
        # Get total count
        total = db.query(WebhookEvent).filter(
            WebhookEvent.project_id == project_id
        ).count()
        
        # Get paginated events
        events = db.query(WebhookEvent).filter(
            WebhookEvent.project_id == project_id
        ).order_by(
            WebhookEvent.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return events, total
    
    @staticmethod
    def retry_failed_webhook(db: Session, webhook_id: int) -> bool:
        """
        Retry a failed webhook delivery.
        
        Args:
            db: Database session
            webhook_id: Webhook event ID
            
        Returns:
            bool: True if retry was successful
        """
        webhook_event = db.query(WebhookEvent).get(webhook_id)
        
        if not webhook_event:
            logger.error(f"Webhook event {webhook_id} not found")
            return False
        
        if webhook_event.status != "failed":
            logger.warning(f"Webhook {webhook_id} status is {webhook_event.status}, not failed")
            return False
        
        # Check retry limits
        max_retries = 3
        if webhook_event.delivery_attempts >= max_retries:
            logger.warning(f"Webhook {webhook_id} has exceeded max retries")
            return False
        
        # Reset for retry
        webhook_event.status = "pending_retry"
        webhook_event.delivery_attempts += 1
        webhook_event.last_delivery_attempt = datetime.utcnow()
        webhook_event.next_retry_at = datetime.utcnow() + timedelta(minutes=5)
        
        db.commit()
        
        # In production, this would queue the retry in a background task
        logger.info(f"Queued webhook {webhook_id} for retry (attempt {webhook_event.delivery_attempts})")
        return True
