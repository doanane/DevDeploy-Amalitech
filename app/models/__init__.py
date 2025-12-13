# app/models/__init__.py
from .user import User
from .project import Project
from .build import Build
from .webhook import WebhookEvent
from .notification import Notification
from .build_log import BuildLog

# Make sure all models are registered
__all__ = [
    "User", 
    "Project", 
    "Build", 
    "WebhookEvent", 
    "Notification",
    "BuildLog"
]