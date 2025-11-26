from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class BuildBase(BaseModel):
    """
    Base schema for build data with common fields
    
    These fields can be provided when creating a build
    """
    # Git commit hash (optional - can be provided when triggering build)
    commit_hash: Optional[str] = None
    
    # Git commit message (optional)
    commit_message: Optional[str] = None

class BuildCreate(BuildBase):
    """
    Schema for creating a new build
    
    Inherits all fields from BuildBase
    Used when a user triggers a new build
    """
    # 'pass' means this class doesn't add any new fields
    # It uses all the fields from BuildBase ok
    pass

class Build(BuildBase):
    """
    Schema for returning complete build information
    
    Includes all database fields including auto-generated ones
    Used when returning build data to the client
    """
    # Auto-generated build ID from database
    id: int
    
    # ID of the project this build belongs to
    project_id: int
    
    # Current build status
    status: str
    
    # Build logs/output
    logs: str
    
    # When the build was created
    created_at: datetime
    
    # When the build started running (optional until build starts)
    started_at: Optional[datetime]
    
    # When the build completed (optional until build finishes)
    completed_at: Optional[datetime]
    
    # Pydantic configuration
    class Config:
        # This allows creating Build instances from SQLAlchemy model instances
        # Without this, we couldn't return SQLAlchemy objects directly from our API
        from_attributes = True

class BuildSummary(BaseModel):
    """
    Simplified build schema for listing builds
    
    Contains only essential information for displaying in lists
    More efficient than returning full build data with logs
    """
    id: int
    project_id: int
    status: str
    commit_hash: Optional[str]
    commit_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True