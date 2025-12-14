from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.services.build_runner import BuildRunner
from app.services.webhook_parser import parse_github_webhook, parse_gitlab_webhook
from app.database import get_db, AsyncSessionLocal
from app.models import Build, WebhookEvent, Project

# Configure Celery
celery_app = Celery(
    "devdeploy",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_webhook_event_task(self, event_id: int):
    """Process webhook event asynchronously."""
    try:
        # Run async function in sync context
        asyncio.run(_process_webhook_event(event_id))
    except Exception as exc:
        logger.error(f"Failed to process webhook event {event_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

async def _process_webhook_event(event_id: int):
    """Async function to process webhook event."""
    async with AsyncSessionLocal() as db:
        try:
            # Get webhook event
            from sqlalchemy import select
            stmt = select(WebhookEvent).where(WebhookEvent.id == event_id)
            result = await db.execute(stmt)
            event = result.scalar_one()
            
            if not event:
                logger.error(f"Webhook event {event_id} not found")
                return
            
            # Update status to processing
            event.status = "processing"
            await db.commit()
            
            # Parse based on event type
            if event.event_type.startswith("github."):
                event_type = event.event_type.replace("github.", "")
                await parse_github_webhook(
                    event.payload,
                    event_type,
                    event.project,
                    db
                )
            elif event.event_type.startswith("gitlab."):
                event_type = event.event_type.replace("gitlab.", "")
                await parse_gitlab_webhook(
                    event.payload,
                    event_type,
                    event.project,
                    db
                )
            
            # Update status to processed
            event.status = "processed"
            event.processed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Webhook event {event_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing webhook event {event_id}: {str(e)}")
            event.status = "failed"
            event.response = str(e)
            await db.commit()
            raise

@celery_app.task
def run_build_task(build_id: int):
    """Run a build asynchronously."""
    try:
        asyncio.run(_run_build(build_id))
    except Exception as exc:
        logger.error(f"Failed to run build {build_id}: {str(exc)}")

async def _run_build(build_id: int):
    """Async function to run a build."""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            stmt = select(Build).where(Build.id == build_id)
            result = await db.execute(stmt)
            build = result.scalar_one()
            
            if not build:
                logger.error(f"Build {build_id} not found")
                return
            
            runner = BuildRunner(db)
            await runner.run_build(build)
            
        except Exception as e:
            logger.error(f"Error running build {build_id}: {str(e)}")
            raise

@celery_app.task
def cleanup_old_builds():
    """Clean up old builds and logs."""
    try:
        asyncio.run(_cleanup_old_builds())
    except Exception as exc:
        logger.error(f"Cleanup failed: {str(exc)}")

async def _cleanup_old_builds():
    """Async function to clean up old builds."""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import delete, and_
            from datetime import datetime, timedelta
            
            # Delete build logs older than retention period
            retention_days = settings.BUILD_LOG_RETENTION_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Archive old builds instead of deleting
            from sqlalchemy import update
            stmt = update(Build).where(
                and_(
                    Build.created_at < cutoff_date,
                    Build.status.in_(["success", "failed"]),
                    Build.archived == False
                )
            ).values(archived=True)
            
            await db.execute(stmt)
            await db.commit()
            
            logger.info("Old builds archived successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up old builds: {str(e)}")
            raise

@celery_app.task
def check_queued_builds():
    """Check for pending builds and process them."""
    try:
        asyncio.run(_check_queued_builds())
    except Exception as exc:
        logger.error(f"Failed to check queued builds: {str(exc)}")

async def _check_queued_builds():
    """Async function to check queued builds."""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select, and_
            from app.core.config import settings
            
            # Get pending builds
            stmt = select(Build).where(
                and_(
                    Build.status == "pending",
                    Build.archived == False
                )
            ).order_by(Build.created_at.asc()).limit(settings.MAX_CONCURRENT_BUILDS)
            
            result = await db.execute(stmt)
            pending_builds = result.scalars().all()
            
            # Start builds
            for build in pending_builds:
                runner = BuildRunner(db)
                await runner.run_build(build)
            
        except Exception as e:
            logger.error(f"Error checking queued builds: {str(e)}")
            raise

# Periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-builds": {
        "task": "app.workers.tasks.cleanup_old_builds",
        "schedule": timedelta(hours=24),  # Daily
    },
    "check-queued-builds": {
        "task": "app.workers.tasks.check_queued_builds",
        "schedule": timedelta(seconds=30),  # Every 30 seconds
    },
    "health-check": {
        "task": "app.workers.tasks.health_check",
        "schedule": timedelta(minutes=5),  # Every 5 minutes
    },
}

@celery_app.task
def health_check():
    """Perform system health check."""
    logger.info("Health check performed")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}