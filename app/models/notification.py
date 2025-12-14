# app/models/notification.py - New model
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    build_id = Column(Integer, ForeignKey("builds.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(50), nullable=False)  # build_failed, build_success, system_alert
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional data like error details
    channel = Column(String(50), nullable=False)  # email, slack, web, webhook
    status = Column(String(50), nullable=False, default="pending")  # pending, sent, failed, read
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    project = relationship("Project")
    build = relationship("Build")
    
    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_project_type", "project_id", "type"),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "channel": self.channel,
            "status": self.status,
            "read": self.read_at is not None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "project": {
                "id": self.project.id,
                "name": self.project.name
            } if self.project else None,
            "build": {
                "id": self.build.id,
                "status": self.build.status
            } if self.build else None
        }