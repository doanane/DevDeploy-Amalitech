from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
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

    project = relationship("Project", back_populates="builds")