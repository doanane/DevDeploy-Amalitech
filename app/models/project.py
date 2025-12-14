
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    repository_url = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Webhook config
    webhook_secret = Column(String(255), nullable=True)
    webhook_enabled = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User")
    builds = relationship("Build", back_populates="project")
    webhook_events = relationship("WebhookEvent", back_populates="project")
