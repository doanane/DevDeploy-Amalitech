from app.core.config import settings
from jose import JWTError, jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import timezone, datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated= "auto")

load_dotenv()

def verify_password(plain_password:str, hashed_password:str)-> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str)-> str:
    if len(password.encode('utf-8')) >72:
        raise ValueError("password is too long")
    return pwd_context.hash(password)

def create_access_token(data: dict)-> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    date.update=({"exp": expire})

    encoded_jwt=jwt.encode(data, settings.secret_key, algotithm=settings.algorithm)

    return encoded_jwt

def verify_token(token: str)-> str:
    try:
        payload= jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email= payload.get("sub")
        return email

    except JWTError:
        None
