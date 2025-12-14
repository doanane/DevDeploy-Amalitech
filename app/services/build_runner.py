# app/services/build_runner.py - FIXED
import asyncio
import random
import logging
from datetime import datetime
from typing import Optional
from threading import Thread

from app.database import SessionLocal
from app.models import Build

logger = logging.getLogger(__name__)

def start_build_process(build_id: int):
    """Start a build process in a separate thread."""
    thread = Thread(target=run_build_sync, args=(build_id,))
    thread.daemon = True
    thread.start()

def run_build_sync(build_id: int):
    """Run build in a sync wrapper."""
    asyncio.run(simulate_build(build_id))

async def simulate_build(build_id: int):
    """Simulate a build process with realistic stages."""
    db = SessionLocal()
    try:
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build:
            logger.error(f"Build {build_id} not found")
            return
        
        # Update to running
        build.status = "running"
        build.started_at = datetime.utcnow()
        db.commit()
        
        # Simulate build stages (unchanged from your original code)
        stages = [
            {"name": "clone", "duration": 2, "success_rate": 0.99},
            {"name": "install", "duration": 5, "success_rate": 0.95},
            {"name": "test", "duration": 10, "success_rate": 0.90},
            {"name": "build", "duration": 8, "success_rate": 0.92},
            {"name": "deploy", "duration": 5, "success_rate": 0.98},
        ]
        
        logs = []
        for stage in stages:
            stage_name = stage["name"]
            duration = stage["duration"]
            
            # Add stage start log
            logs.append(f"[{datetime.utcnow().isoformat()}] Starting {stage_name} stage...")
            build.logs = "\n".join(logs)
            db.commit()
            
            # Simulate progress
            for i in range(duration):
                await asyncio.sleep(1)
                
                # Add progress logs
                if i % 2 == 0:
                    progress = (i + 1) / duration * 100
                    logs.append(f"[{datetime.utcnow().isoformat()}] {stage_name} in progress... {int(progress)}%")
                    build.logs = "\n".join(logs)
                    db.commit()
            
            # Stage completed
            logs.append(f"[{datetime.utcnow().isoformat()}] {stage_name} stage completed successfully")
            build.logs = "\n".join(logs)
            db.commit()
            
            # Check if build should fail at this stage
            if random.random() > stage["success_rate"]:
                logs.append(f"[{datetime.utcnow().isoformat()}] ERROR: Build failed at {stage_name} stage")
                build.logs = "\n".join(logs)
                build.status = "failed"
                build.completed_at = datetime.utcnow()
                db.commit()
                return
        
        # All stages completed successfully
        logs.append(f"[{datetime.utcnow().isoformat()}] Build completed successfully!")
        build.logs = "\n".join(logs)
        build.status = "success"
        build.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error simulating build {build_id}: {e}")
        try:
            build.status = "failed"
            build.logs = f"{build.logs or ''}\nError: {str(e)}"
            build.completed_at = datetime.utcnow()
            db.commit()
        except:
            pass
    finally:
        db.close()

def trigger_build(db, project_id: int, commit_hash: Optional[str] = None, commit_message: Optional[str] = None):
    """Trigger a new build."""
    try:
        build = Build(
            project_id=project_id,
            commit_hash=commit_hash,
            commit_message=commit_message,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(build)
        db.commit()
        db.refresh(build)
        
        # Start build in background using thread
        start_build_process(build.id)
        
        return build
    except Exception as e:
        db.rollback()
        raise e