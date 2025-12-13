# app/models/build_log.py - Updated version
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class BuildLog(Base):
    __tablename__ = "build_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    build_id = Column(Integer, ForeignKey("builds.id"))
    stage = Column(String(50))  # Added this
    log_level = Column(String(20), default="info")  # Added this
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    build = relationship("Build", back_populates="logs_relationship")  # Added this