# app/core/config.py
# Import necessary modules
from pydantic_settings import BaseSettings  # Import BaseSettings for settings management
import os  # Import os to access environment variables
from dotenv import load_dotenv  # Import to load .env file

# Load environment variables from .env file
load_dotenv()

# Define a Settings class that inherits from BaseSettings
# Pydantic will automatically validate and convert environment variables
class Settings(BaseSettings):
    # Database connection URL
    # = os.getenv("DATABASE_URL") gets the value from environment variable
    database_url: str = os.getenv("DATABASE_URL")
    
    # Secret key for JWT token encryption
    # Provide a fallback value in case the environment variable is not set
    secret_key: str = os.getenv("SECRET_KEY", "fallback-secret-key")
    
    # Algorithm to use for JWT token encoding/decoding
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    
    # Token expiration time in minutes
    # Convert string to integer, with default value of 30 minutes
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Configuration class for Pydantic settings
    class Config:
        # Allow case-insensitive environment variable names
        case_sensitive = False

# Create an instance of Settings that can be imported throughout the application
settings = Settings()