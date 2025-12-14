# app/api/builds.py - UPDATED with proper auth import
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.build import Build
from app.schemas.build import BuildCreate, Build as BuildSchema, BuildSummary
from app.api.auth import get_current_user
from app.services.build_runner import simulate_build, trigger_build

router = APIRouter(prefix="/builds", tags=["builds"])

# In app/api/builds.py
@router.post("/projects/{project_id}/builds", response_model=BuildSchema)
def create_build(
    project_id: int,
    build_data: BuildCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger a new build for a project
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create build for archived project"
        )
    
    # Create the build
    build = Build(
        project_id=project_id,
        commit_hash=build_data.commit_hash,
        commit_message=build_data.commit_message,
        status="pending",
        created_at=datetime.utcnow()
    )
    
    db.add(build)
    db.commit()
    db.refresh(build)
    
    # Add to background tasks
    background_tasks.add_task(simulate_build_sync, build.id)
    
    return build

def simulate_build_sync(build_id: int):
    """Sync wrapper for simulate_build."""
    asyncio.run(simulate_build(build_id))
    
@router.get("/{build_id}", response_model=BuildSchema)
def get_build(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific build by ID
    """
    build = db.query(Build).join(Project).filter(
        Build.id == build_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not build:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build not found"
        )
    
    return build

@router.get("/{build_id}/logs")
def get_build_logs(
    build_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get only the logs for a specific build
    """
    build = db.query(Build).join(Project).filter(
        Build.id == build_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not build:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build not found"
        )
    
    return {"logs": build.logs}