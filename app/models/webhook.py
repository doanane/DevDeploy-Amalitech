# app/models/webhook.py - New model
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import json

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=False)
    signature = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, processed, failed
    status_code = Column(Integer, nullable=True)
    response = Column(Text, nullable=True)
    delivery_attempts = Column(Integer, default=0)
    last_delivery_attempt = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="webhook_events")
    
    __table_args__ = (
        Index("ix_webhook_events_project_status", "project_id", "status"),
        Index("ix_webhook_events_created_at", "created_at"),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "event_type": self.event_type,
            "status": self.status,
            "status_code": self.status_code,
            "delivery_attempts": self.delivery_attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }
    
    def get_payload_summary(self):
        """Get a summary of the payload for logging."""
        payload = self.payload or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
                payload = {}
        
        summary = {
            "action": payload.get("action"),
            "ref": payload.get("ref"),
            "sha": payload.get("sha", payload.get("after", ""))[:8],
            "repository": payload.get("repository", {}).get("full_name"),
            "sender": payload.get("sender", {}).get("login")
        }
        return {k: v for k, v in summary.items() if v}