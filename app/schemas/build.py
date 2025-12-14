# app/schemas/build.py - FIXED
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BuildBase(BaseModel):
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None

class BuildCreate(BuildBase):
    pass

class Build(BuildBase):
    id: int
    project_id: int
    status: str
    logs: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class BuildSummary(BaseModel):
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