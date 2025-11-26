import time
import random
from sqlalchemy.orm import Session
from app.models.build import Build
from datetime import datetime, timezone
from app.database import SessionLocal  # Add this import

def simulate_build(build_id: int):  # Remove db parameter
    """
    Simulate a CI/CD build process for a build
    
    This function runs in the background and updates the build status
    It simulates different build stages and randomly fails some builds
    
    Args:
        build_id: ID of the build to simulate
    """
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        # Get the build from database using the build_id
        build = db.query(Build).filter(Build.id == build_id).first()
        
        # If build doesn't exist, stop the function
        if not build:
            return
        
        # Update build status to "running" and set start time
        build.status = "running"
        build.started_at = datetime.now(timezone.utc)  # Use timezone-aware datetime
        db.commit()
        
        logs = []
        
        try:
            # Simulate different build stages
            
            # Stage 1: Fetching source code
            logs.append("Starting build process...")
            logs.append("Stage 1: Fetching source code from repository")
            time.sleep(2)
            logs.append("✓ Source code fetched successfully")
            
            # Stage 2: Installing dependencies
            logs.append("Stage 2: Installing dependencies")
            time.sleep(3)
            logs.append("✓ Dependencies installed (15 packages)")
            
            # Stage 3: Running tests
            logs.append("Stage 3: Running tests")
            time.sleep(4)
            
            # Randomly fail some tests (20% chance of failure)
            if random.random() < 0.2:
                logs.append("✗ Tests failed! Some tests did not pass")
                build.status = "failed"
                build.logs = "\n".join(logs)
            else:
                logs.append("✓ All tests passed (25/25 tests)")
                
                # Stage 4: Building application
                logs.append("Stage 4: Building application")
                time.sleep(3)
                logs.append("✓ Application built successfully")
                
                # Stage 5: Deployment
                logs.append("Stage 5: Deploying to server")
                time.sleep(2)
                logs.append("✓ Deployment completed successfully")
                
                # Mark build as successful
                build.status = "success"
                build.logs = "\n".join(logs)
        
        except Exception as e:
            # If any error occurs during build simulation
            logs.append(f"Build error: {str(e)}")
            build.status = "failed"
            build.logs = "\n".join(logs)
        
        # Set completion time and save final status
        build.completed_at = datetime.now(timezone.utc)  # Use timezone-aware datetime
        db.commit()
    
    finally:
        # Always close the database session
        db.close()

def trigger_build(db: Session, project_id: int, commit_hash: str = None, commit_message: str = None) -> Build:
    """
    Create a new build and start the build process
    
    Args:
        db: Database session
        project_id: ID of the project to build
        commit_hash: Optional git commit hash
        commit_message: Optional git commit message
    
    Returns:
        Build: The created build object
    """
    new_build = Build(
        project_id=project_id,
        status="pending",
        commit_hash=commit_hash,
        commit_message=commit_message,
        logs="Build created and queued for execution..."
    )
    
    db.add(new_build)
    db.commit()
    db.refresh(new_build)
    
    return new_build