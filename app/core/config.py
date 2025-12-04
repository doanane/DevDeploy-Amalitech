# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Use different default based on environment
    database_url: str = "postgresql+psycopg2://postgres:password@localhost:5432/DevDeploy"
    secret_key: str = "your-fallback-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Detect if running in Docker
    in_docker: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Detect Docker environment
        self.in_docker = os.path.exists("/.dockerenv")
        
        # If in Docker and using default localhost URL, switch to Docker URL
        if self.in_docker and "localhost" in self.database_url:
            self.database_url = "postgresql+psycopg2://postgres:password@db:5432/DevDeploy"

settings = Settings()