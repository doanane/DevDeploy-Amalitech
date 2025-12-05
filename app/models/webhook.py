from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class WebhookEvent(Base):
    """
    Model for storing webhook events from GitHub/GitLab
    """
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    
    event_type = Column(String(100))
    action = Column(String(100))
    
    delivery_id = Column(String(100), unique=True, index=True)
    signature = Column(String(255))
    status = Column(String(20), default="received")
    
    payload = Column(JSON)
    headers = Column(JSON)
    
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    project = relationship("Project", back_populates="webhook_events")
