# app/services/webhook_parser.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from typing import Dict, Any, Optional

from app.models import Build, Project, WebhookEvent
from app.services.build_runner import BuildRunner
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)

async def parse_github_webhook(
    payload: Dict[str, Any],
    event_type: str,
    project: Optional[Project],
    db: AsyncSession
):
    """Parse GitHub webhook payload and update builds."""
    try:
        if event_type == "push":
            await handle_github_push(payload, project, db)
        elif event_type == "workflow_run":
            await handle_github_workflow_run(payload, project, db)
        elif event_type == "pull_request":
            await handle_github_pull_request(payload, project, db)
        
        logger.info(f"Processed GitHub {event_type} webhook")
        
    except Exception as e:
        logger.error(f"Error parsing GitHub webhook: {str(e)}")
        raise

async def handle_github_push(
    payload: Dict[str, Any],
    project: Optional[Project],
    db: AsyncSession
):
    """Handle GitHub push event."""
    if not project or not project.active:
        return
    
    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "")
    
    # Check if this push is for the monitored branch
    if branch != project.branch:
        logger.info(f"Push to branch {branch}, monitoring {project.branch}, skipping")
        return
    
    after_sha = payload.get("after", "")
    if not after_sha:
        return
    
    # Create a new build
    build = Build(
        project_id=project.id,
        trigger_type="webhook",
        trigger_ref=ref,
        commit_hash=after_sha,
        status="pending",
        branch=branch
    )
    
    db.add(build)
    await db.commit()
    await db.refresh(build)
    
    # Trigger build runner
    runner = BuildRunner(db)
    await runner.run_build(build)
    
    # Send notification
    notification_service = NotificationService(db)
    await notification_service.send_build_started(
        user_id=project.user_id,
        project_id=project.id,
        build_id=build.id,
        commit_hash=after_sha[:8]
    )

async def handle_github_workflow_run(
    payload: Dict[str, Any],
    project: Optional[Project],
    db: AsyncSession
):
    """Handle GitHub workflow_run event."""
    workflow_run = payload.get("workflow_run", {})
    if not workflow_run:
        return
    
    conclusion = workflow_run.get("conclusion")
    status = workflow_run.get("status")
    html_url = workflow_run.get("html_url", "")
    
    if status == "completed" and conclusion:
        # Find build by commit hash
        head_sha = workflow_run.get("head_sha", "")
        if not head_sha:
            return
        
        stmt = select(Build).where(
            Build.commit_hash == head_sha,
            Build.project_id == project.id if project else True
        ).order_by(Build.created_at.desc())
        
        result = await db.execute(stmt)
        build = result.scalar_one_or_none()
        
        if build:
            # Update build status based on workflow conclusion
            if conclusion == "success":
                build.status = "success"
                build.completed_at = datetime.utcnow()
            else:
                build.status = "failed"
                build.completed_at = datetime.utcnow()
                build.error_message = f"GitHub Actions workflow failed: {conclusion}"
            
            build.external_url = html_url
            await db.commit()
            
            # Send notification
            if project:
                notification_service = NotificationService(db)
                if conclusion == "success":
                    await notification_service.send_build_success(
                        user_id=project.user_id,
                        project_id=project.id,
                        build_id=build.id
                    )
                else:
                    await notification_service.send_build_failed(
                        user_id=project.user_id,
                        project_id=project.id,
                        build_id=build.id,
                        error_message=conclusion
                    )

async def parse_gitlab_webhook(
    payload: Dict[str, Any],
    event_type: str,
    project: Optional[Project],
    db: AsyncSession
):
    """Parse GitLab webhook payload."""
    try:
        if event_type == "Push Hook":
            await handle_gitlab_push(payload, project, db)
        elif event_type == "Pipeline Hook":
            await handle_gitlab_pipeline(payload, project, db)
        
        logger.info(f"Processed GitLab {event_type} webhook")
        
    except Exception as e:
        logger.error(f"Error parsing GitLab webhook: {str(e)}")
        raise

async def parse_test_webhook(
    payload: Dict[str, Any],
    project: Project,
    db: AsyncSession
):
    """Parse test webhook payload."""
    logger.info(f"Processing test webhook for project {project.name}")
    # Create a test build
    build = Build(
        project_id=project.id,
        trigger_type="test",
        status="pending"
    )
    
    db.add(build)
    await db.commit()
    await db.refresh(build)
    
    # Run test build
    runner = BuildRunner(db)
    await runner.run_build(build, test_mode=True)
    
    return build