# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """
    Smart database URL detection:
    - Check DATABASE_URL from .env first
    - If not found, build URL based on environment
    """
    # First, try to get DATABASE_URL from .env
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    
    # If no DATABASE_URL, build it based on environment
    in_docker = os.path.exists("/.dockerenv")
    
    if in_docker:
        # Docker environment
        host = "db"
        password = "password123"  # Docker password
    else:
        # Local development
        host = "localhost"
        password = "S%400570263170s"  # Your encoded password
    
    # Build URL
    return f"postgresql+psycopg2://postgres:{password}@{host}:5432/DevDeploy"

DATABASE_URL = get_database_url()
print(f"🔗 Database URL: {DATABASE_URL}")  # Debug logging

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()