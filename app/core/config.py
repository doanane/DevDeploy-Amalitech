from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DevDeploy"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/devdeploy"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_QUEUE_DB: int = 0
    REDIS_CACHE_DB: int = 1
    
    # GitHub Integration
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_ACCESS_TOKEN: Optional[str] = None
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@devdeploy.com"
    
    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Build System
    MAX_CONCURRENT_BUILDS: int = 3
    BUILD_TIMEOUT_SECONDS: int = 1800
    BUILD_LOG_RETENTION_DAYS: int = 90
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 900
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # This allows extra environment variables

settings = Settings()