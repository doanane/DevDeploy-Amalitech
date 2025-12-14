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

# Custom login form that shows "email" instead of "username"
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
        self.username = email  # Map email to username for OAuth2 compatibility
        self.password = password
        self.grant_type = grant_type
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret