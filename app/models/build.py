
# app/models/build.py - Updated with logs relationship
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Build(Base):
    __tablename__ = "builds"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default="pending")
    logs = Column(Text, default="")
    commit_hash = Column(String(100))
    commit_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    project_id = Column(Integer, ForeignKey("projects.id"))
    build_number = Column(String(50), nullable=True)
    trigger_type = Column(String(20), default="manual")
    branch = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    external_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    archived = Column(Boolean, default=False)
    build_metadata = Column(JSON, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="builds")
    logs_relationship = relationship("BuildLog", back_populates="build", cascade="all, delete-orphan")
