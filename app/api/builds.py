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

router = APIRouter(prefix="", tags=["builds"])

@router.post("/projects/{project_id}/builds", response_model=BuildSchema, operation_id="trigger_build")
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
    
    new_build = trigger_build(
        db=db,
        project_id=project_id,
        commit_hash=build_data.commit_hash,
        commit_message=build_data.commit_message
    )
    
    background_tasks.add_task(simulate_build, new_build.id)
    
    return new_build

@router.get("/projects/{project_id}/builds", response_model=List[BuildSummary], operation_id="list_project_builds")
def get_project_builds(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """
    Get all builds for a specific project
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
    
    builds = db.query(Build).filter(
        Build.project_id == project_id
    ).order_by(
        Build.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return builds

@router.get("/builds/{build_id}", response_model=BuildSchema, operation_id="get_build")  # Added /builds prefix
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

@router.get("/builds/{build_id}/logs", operation_id="get_build_logs")  # Added /builds prefix
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