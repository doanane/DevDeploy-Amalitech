from datetime import datetime, timedelta, timezone  # Add timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Enforce bcrypt's 72-byte limit for UTF-8 encoded passwords
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password too long (maximum 72 bytes in UTF-8 encoding)")
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    # Use timezone-aware datetime (not deprecated utcnow)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    data.update({"exp": expire})
    return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        return email
    except JWTError:
        return None