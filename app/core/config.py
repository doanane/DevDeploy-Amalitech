import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()
class Settings(BaseSettings):
    database_url:str = os.getenv("DATABASE_URL")
    algorithm:str = os.getenv("ALGORITHM:, HS256")
    secret_key: str = os.getenv("SECRET_KEY", "fallback_secret_key")
    access_token_expire_minutes:int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

class Config:
    case_sensitive=False

settings = Settings()
