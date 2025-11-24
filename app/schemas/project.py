from pydantic import BaseModel
from datetime import datetime
from typing import List

class ProjectBase(BaseModel):
    name: str
    repository_url: str
    branch: str = "main"
    status: str = "active"

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True