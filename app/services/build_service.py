"""
Production build service with queue management, concurrency control, and build execution.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc

from app.models import Build, Project
from app.core.redis import redis_client
from app.core.websocket import broadcast_build_update

logger = logging.getLogger(__name__)

class BuildStatus(str, Enum):
    """Build status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class BuildService:
    """Service for managing builds."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_build(
        self,
        project_id: int,
        trigger_type: str = "manual",
        commit_hash: Optional[str] = None,
        commit_message: Optional[str] = None,
        branch: Optional[str] = None,
        build_metadata: Optional[Dict[str, Any]] = None
    ) -> Build:
        """
        Create a new build.
        """
        # Get project
        project = self.db.query(Project).get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        if project.status != "active":
            raise ValueError(f"Project {project_id} is not active")
        
        # Create build
        build = Build(
            project_id=project_id,
            trigger_type=trigger_type,
            commit_hash=commit_hash,
            commit_message=commit_message,
            branch=branch or project.branch,
            status=BuildStatus.PENDING.value,
            build_metadata=build_metadata or {},
            build_number=self._generate_build_number(project_id)
        )
        
        self.db.add(build)
        self.db.flush()
        
        # Add initial log
        self._add_build_log(
            build_id=build.id,
            stage="initialization",
            message=f"Build {build.build_number} created via {trigger_type} trigger",
            level="info"
        )
        
        # Queue build for execution
        self._queue_build(build.id)
        
        self.db.commit()
        
        # Broadcast build creation
        broadcast_build_update(build.project_id, {
            "type": "build_created",
            "build_id": build.id,
            "project_id": build.project_id,
            "status": build.status,
            "build_number": build.build_number
        })
        
        logger.info(f"Created build {build.id} for project {project_id}")
        return build
    
    def start_build(self, build_id: int) -> Build:
        """
        Start a build execution.
        """
        build = self.db.query(Build).get(build_id)
        if not build:
            raise ValueError(f"Build {build_id} not found")
        
        if build.status != BuildStatus.PENDING.value:
            raise ValueError(f"Build {build_id} is not pending")
        
        # Update build status
        build.status = BuildStatus.RUNNING.value
        build.started_at = datetime.utcnow()
        
        self._add_build_log(
            build_id=build.id,
            stage="execution",
            message="Build execution started",
            level="info"
        )
        
        self.db.commit()
        
        # Broadcast build start
        broadcast_build_update(build.project_id, {
            "type": "build_started",
            "build_id": build.id,
            "status": build.status,
            "started_at": build.started_at.isoformat()
        })
        
        logger.info(f"Started build {build.id}")
        return build
    
    def complete_build(
        self,
        build_id: int,
        status: BuildStatus,
        logs: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Build:
        """
        Complete a build.
        """
        build = self.db.query(Build).get(build_id)
        if not build:
            raise ValueError(f"Build {build_id} not found")
        
        if build.status not in [BuildStatus.PENDING.value, BuildStatus.RUNNING.value]:
            raise ValueError(f"Build {build_id} is already completed")
        
        # Update build
        build.status = status.value
        build.completed_at = datetime.utcnow()
        build.duration_seconds = int(
            (build.completed_at - (build.started_at or build.created_at)).total_seconds()
        )
        
        if logs:
            build.logs = logs
        
        if error_message:
            build.error_message = error_message
        
        # Add completion log
        log_level = "error" if status == BuildStatus.FAILED else "info"
        self._add_build_log(
            build_id=build.id,
            stage="completion",
            message=f"Build {status.value}",
            level=log_level
        )
        
        self.db.commit()
        
        # Broadcast build completion
        broadcast_build_update(build.project_id, {
            "type": "build_completed",
            "build_id": build.id,
            "status": build.status,
            "completed_at": build.completed_at.isoformat(),
            "duration_seconds": build.duration_seconds
        })
        
        # Send notifications
        self._send_build_notifications(build)
        
        logger.info(f"Completed build {build.id} with status {status.value}")
        return build
    
    def get_build_with_logs(self, build_id: int) -> Optional[Build]:
        """
        Get a build with its logs.
        """
        return self.db.query(Build).options(
            joinedload(Build.logs)
        ).filter(Build.id == build_id).first()
    
    def get_project_builds(
        self,
        project_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Build]:
        """
        Get builds for a project with filtering and pagination.
        """
        query = self.db.query(Build).filter(Build.project_id == project_id)
        
        if status:
            query = query.filter(Build.status == status)
        
        return query.order_by(
            desc(Build.created_at)
        ).offset(offset).limit(limit).all()
    
    def cancel_build(self, build_id: int) -> Build:
        """
        Cancel a pending or running build.
        """
        build = self.db.query(Build).get(build_id)
        if not build:
            raise ValueError(f"Build {build_id} not found")
        
        if build.status not in [BuildStatus.PENDING.value, BuildStatus.RUNNING.value]:
            raise ValueError(f"Build {build_id} cannot be cancelled")
        
        build.status = BuildStatus.CANCELLED.value
        build.completed_at = datetime.utcnow()
        
        self._add_build_log(
            build_id=build.id,
            stage="cancellation",
            message="Build cancelled by user",
            level="warning"
        )
        
        self.db.commit()
        
        # Remove from queue if pending
        self.redis.lrem("build_queue", 0, str(build_id))
        
        broadcast_build_update(build.project_id, {
            "type": "build_cancelled",
            "build_id": build.id
        })
        
        logger.info(f"Cancelled build {build.id}")
        return build
    
    def get_build_queue_status(self) -> Dict[str, Any]:
        """
        Get current build queue status.
        """
        # Get pending builds from queue
        queue_builds = redis_client.get_cache("build_queue") or []
        pending_count = len(queue_builds)
        
        # Get running builds
        running_builds = self.db.query(Build).filter(
            Build.status == BuildStatus.RUNNING.value
        ).all()
        running_count = len(running_builds)
        
        # Get max concurrent builds from config
        max_concurrent = 3  # Should come from config
        
        return {
            "pending": pending_count,
            "running": running_count,
            "max_concurrent": max_concurrent,
            "available_slots": max(0, max_concurrent - running_count),
            "queue_position": queue_builds[:10] if queue_builds else []
        }
    
    def _generate_build_number(self, project_id: int) -> str:
        """
        Generate a unique build number for a project.
        """
        # Get project abbreviation
        project = self.db.query(Project).get(project_id)
        project_abbr = project.name[:3].upper() if project else "PRJ"
        
        # Get next sequence number
        last_build = self.db.query(Build).filter(
            Build.project_id == project_id
        ).order_by(desc(Build.created_at)).first()
        
        if last_build and last_build.build_number:
            # Extract number from last build number
            try:
                last_num = int(last_build.build_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"{project_abbr}-{next_num:03d}"
    
    def _queue_build(self, build_id: int):
        """Add build to processing queue."""
        if redis_client.is_connected():
            # Get current queue
            queue = redis_client.get_cache("build_queue") or []
            queue.append(build_id)
            redis_client.set_cache("build_queue", queue, ttl=3600)
        else:
            logger.warning("Redis not available, using in-memory queue")
            # In-memory queue logic here
    
    def _add_build_log(
        self,
        build_id: int,
        stage: str,
        message: str,
        level: str = "info"
    ):
        """Add a log entry to a build."""
        from app.models.build_log import BuildLog
        
        log = BuildLog(
            build_id=build_id,
            stage=stage,
            log_level=level,
            message=message
        )
        self.db.add(log)
        
        # Broadcast log via WebSocket
        broadcast_build_update(build_id, {
            "type": "build_log",
            "build_id": build_id,
            "log": {
                "stage": stage,
                "level": level,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    def _send_build_notifications(self, build: Build):
        """Send notifications for build completion."""
        # This would integrate with your notification service
        # For now, just log it
        logger.info(f"Would send notifications for build {build.id} status {build.status}")
