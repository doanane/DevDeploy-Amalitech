# app/models/__init__.py
# Import all model classes so they can be discovered by SQLAlchemy
# When SQLAlchemy looks for models, it will find these imports
from app.models.user import User  # Import User model
from app.models.project import Project  # Import Project model
from app.models.build import Build  # Import Build model