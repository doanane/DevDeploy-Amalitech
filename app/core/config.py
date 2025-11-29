from pydantic_settings import BaseSettings
import os 
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    database_url:str= os.getenv("DATABASE_URL")
    secret_key:str=os.getenv("SECRET_KEY", "fallback_secret_key")
    algorithm:str=os.getenv("Algorithm", "HS256")
    access_token_expire_minutes:int=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


class Config:
    case_sensitive = False

settings = Settings()