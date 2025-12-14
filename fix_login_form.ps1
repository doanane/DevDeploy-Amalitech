# Fix login form to show "email" instead of "username"
Write-Host "Fixing login form to show email field..." -ForegroundColor Green

# 1. Update auth.py with custom form
Write-Host "1. Updating auth.py..." -ForegroundColor Yellow
$authContent = @'
# app/api/auth.py - Using custom form with email field
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, Token, TokenData
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_refresh_token,
    verify_token
)

router = APIRouter()

# Custom login form class
class LoginForm:
    def __init__(
        self,
        email: str = Form(..., description="User email address"),
        password: str = Form(..., description="User password"),
        grant_type: Optional[str] = Form(None, pattern="password"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.username = email  # Map to username for compatibility
        self.password = password
        self.grant_type = grant_type
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == user_data.email)
        result = db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        stmt = select(User).where(User.username == user_data.username)
        result = db.execute(stmt)
        existing_username = result.scalar_one_or_none()
        
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(
    form_data: LoginForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login user and return tokens.
    """
    try:
        # Use email (mapped to username in LoginForm)
        stmt = select(User).where(User.email == form_data.username)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token."""
    try:
        payload = verify_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        stmt = select(User).where(User.email == email)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        stmt = select(User).where(User.email == email)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

# Need to define oauth2_scheme for /me endpoint
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
'@

$authContent | Out-File -FilePath "app/api/auth.py" -Encoding UTF8
Write-Host "   Updated auth.py with custom form" -ForegroundColor Green

# 2. Update schemas/auth.py
Write-Host "2. Updating schemas/auth.py..." -ForegroundColor Yellow
$schemasDir = "app/schemas"
if (-not (Test-Path $schemasDir)) {
    New-Item -ItemType Directory -Path $schemasDir
}

$schemasContent = @'
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from fastapi import Form

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
'@

$schemasContent | Out-File -FilePath "app/schemas/auth.py" -Encoding UTF8
Write-Host "   Updated schemas/auth.py" -ForegroundColor Green

# 3. Rebuild
Write-Host "3. Rebuilding containers..." -ForegroundColor Cyan
docker-compose build

# 4. Restart
Write-Host "4. Restarting services..." -ForegroundColor Cyan
docker-compose restart

Write-Host "`nWaiting for restart (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 5. Test
Write-Host "5. Testing..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "   ✅ API is healthy" -ForegroundColor Green
    
    Write-Host "`nOpening API documentation..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000/docs"
    
    Write-Host "`n✅ Fix applied! Check the login form in the docs." -ForegroundColor Green
    Write-Host "   It should now show 'email' field instead of 'username'." -ForegroundColor Green
    
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Checking logs..." -ForegroundColor Yellow
    docker-compose logs api --tail=20
}