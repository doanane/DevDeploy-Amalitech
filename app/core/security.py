# app/core/security.py - Simple version for development
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os
import hashlib

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simple password hashing for development (NOT for production!)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Simple password verification for development."""
    # In development, we can use simple comparison
    # WARNING: This is INSECURE for production!
    if os.getenv("ENVIRONMENT") == "development":
        # For development only - compare directly
        return plain_password == hashed_password
    else:
        # Try bcrypt, fallback to sha256
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except:
            # Fallback to sha256
            test_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            return test_hash == hashed_password

def get_password_hash(password: str) -> str:
    """Simple password hashing for development."""
    # WARNING: This is INSECURE for production!
    if os.getenv("ENVIRONMENT") == "development":
        # For development only - no hashing
        return password
    else:
        # Try bcrypt, fallback to sha256
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.hash(password)
        except:
            # Fallback to sha256
            return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Create a refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """Verify a JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def generate_signature(payload: bytes, secret: str) -> str:
    """Generate HMAC SHA256 signature."""
    import hmac
    if not secret:
        return ""
    signature = hmac.new(
        secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC SHA256 signature."""
    if not signature or not secret:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = generate_signature(payload, secret)
    import hmac
    return hmac.compare_digest(expected, signature)
