from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from datetime import datetime, timedelta, timezone

# my environment that specifies password hashing algorithm and JWT settings types
pwd_context =CryptContext(schemes=["bcrypt"], deprecated= "auto")

load_dotenv()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password length exceeds maximum limit of 72 characters.")
    return pwd_context.hash(password)

def create_access_token(data:dict) -> str:
    expire= datetime.now(timezone.utc) + timedelta(minutes= settings.access_token_expire_minutes)

    data.update({"exp": expire})
    encoded_jwt =jwt.encode(data, settings.secret_key, algorithm= settings.algorithm)
    return encoded_jwt

def verify_token(token:str)-> str:
    try:
        payload= jwt.decode(token, settings.secret_key, algorithms= [settings.algorithm])
        email= payload.get("sub")
        return email    
    except JWTError:
        return None

