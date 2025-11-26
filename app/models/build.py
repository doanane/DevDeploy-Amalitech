# app/models/build.py
# Import necessary SQLAlchemy components
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey  # Import column types
from sqlalchemy.orm import relationship  # Import relationship
from sqlalchemy.sql import func  # Import func for SQL functions
from app.database import Base  # Import Base class

# Define Build model class
class Build(Base):
    """
    Build model representing a CI/CD pipeline execution
    
    This model tracks individual build runs for projects,
    including status, logs, and timing information
    """
    
    # Table name in database
    __tablename__ = "builds"

    # Define columns
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Build status: "pending", "running", "success", "failed"
    # default="pending": New builds start as pending
    status = Column(String(20), default="pending")
    
    # Build logs/output - can be very long
    # Text: For large text content (unlimited length compared to String)
    # default="": Empty string by default
    logs = Column(Text, default="")
    
    # Git commit hash that triggered this build
    # Optional: Can be null if not provided
    commit_hash = Column(String(100))
    
    # Git commit message
    # Optional: Can be null if not provided
    commit_message = Column(Text)
    
    # Automatic timestamp when build record is created
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # When build actually started running
    # Optional: Will be null until build starts
    started_at = Column(DateTime(timezone=True))
    
    # When build completed (success or failure)
    # Optional: Will be null until build finishes
    completed_at = Column(DateTime(timezone=True))
    
    # Foreign key to link build to project
    # ForeignKey("projects.id"): References id column in projects table
    # This creates relationship: each build belongs to one project
    project_id = Column(Integer, ForeignKey("projects.id"))

    # Relationship back to Project model
    # "Project": The related model class
    # back_populates="builds": Matches the relationship in Project model
    # This allows us to access the project from a build: build.project
    project = relationship("Project", back_populates="builds")