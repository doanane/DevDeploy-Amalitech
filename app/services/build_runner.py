import time
import random
from sqlalchemy.orm import Session
from app.models.build import Build
from datetime import datetime

def simulate_build(db: Session, build_id: int):
    """
    Simulate a CI/CD build process for a build
    
    This function runs in the background and updates the build status
    It simulates different build stages and randomly fails some builds
    
    Args:
        db: Database session for updating build status
        build_id: ID of the build to simulate
    """
    # Get the build from database using the build_id
    build = db.query(Build).filter(Build.id == build_id).first()
    
    # If build doesn't exist, stop the function
    if not build:
        return
    
    # Update build status to "running" and set start time
    build.status = "running"
    build.started_at = datetime.utcnow()
    
    # Save the changes to database
    db.commit()
    
    # Initialize logs string to collect build output
    logs = []
    
    try:
        # Simulate different build stages
        # log messages
        # Stage 1: Fetching source code
        logs.append("Starting build process...")
        logs.append("Stage 1: Fetching source code from repository")
        time.sleep(2)  # Simulate time taken to fetch code
        logs.append(" Source code fetched successfully")
        
        # Stage 2: Installing dependencies
        logs.append("Stage 2: Installing dependencies")
        time.sleep(3)
        logs.append(" Dependencies installed (15 packages)")
        
        # Stage 3: Running tests
        logs.append("Stage 3: Running tests")
        time.sleep(4)
        
        # Randomly fail some tests (20% chance of failure)
        # This makes the simulation more realistic
        if random.random() < 0.2:  # 20% chance
            logs.append(" Tests failed! Some tests did not pass")
            build.status = "failed"
            build.logs = "\n".join(logs)
        else:
            logs.append(" All tests passed (25/25 tests)")
            
            # Stage 4: Building application
            logs.append("Stage 4: Building application")
            time.sleep(3)
            logs.append(" Application built successfully")
            
            # Stage 5: Deployment
            logs.append("Stage 5: Deploying to server")
            time.sleep(2)
            logs.append(" Deployment completed successfully")
            
            # Mark build as successful
            build.status = "success"
            build.logs = "\n".join(logs)
    
    except Exception as e:
        # If any error occurs during build simulation
        logs.append(f"Build error: {str(e)}")
        build.status = "failed"
        build.logs = "\n".join(logs)
    
    # Set completion time and save final status
    build.completed_at = datetime.utcnow()
    db.commit()

def trigger_build(db: Session, project_id: int, commit_hash: str = None, commit_message: str = None) -> Build:
    """
    Create a new build and start the build process
    
    This function is called when a user manually triggers a build
    It creates the build record and starts the simulation in the background
    
    Args:
        db: Database session
        project_id: ID of the project to build
        commit_hash: Optional git commit hash
        commit_message: Optional git commit message
    
    Returns:
        Build: The created build object
    """
    # Create a new Build instance with the provided data
    new_build = Build(
        project_id=project_id,
        status="pending",  # Initial status
        commit_hash=commit_hash,
        commit_message=commit_message,
        logs="Build created and queued for execution..."  # Initial log message
    )
    
    # Add the new build to database session
    db.add(new_build)
    
    # Save the build to database
    db.commit()
    
    # Refresh the build to get the auto-generated ID
    db.refresh(new_build)
    
    # Return the created build
    return new_build