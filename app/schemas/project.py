from pydantic import BaseModel, field_validator
import re
from datetime import datetime
from typing import List

class ProjectBase(BaseModel):
    name: str
    repository_url: str
    branch: str = "main"
    status: str = "active"

    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v):
        # Basic GitHub/GitLab URL validation
        url_pattern = r'^https?://(github\.com|gitlab\.com)/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
        if not re.match(url_pattern, v):
            raise ValueError('Repository URL must be a valid GitHub or GitLab URL')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['active', 'archived']:
            raise ValueError('Status must be either "active" or "archived"')
        return v

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True