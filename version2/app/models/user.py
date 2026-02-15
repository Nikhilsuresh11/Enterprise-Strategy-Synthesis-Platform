"""User models for authentication and user management."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Registration request model."""
    
    name: str = Field(..., min_length=2, max_length=100, description="User's display name")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password")


class UserLogin(BaseModel):
    """Login request model."""
    
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Public user response model (no password)."""
    
    id: str = Field(..., description="User ID")
    name: str = Field(..., description="Display name")
    email: str = Field(..., description="Email address")
    created_at: datetime = Field(..., description="Account creation date")


class TokenResponse(BaseModel):
    """JWT token response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User info")


class UserInDB(BaseModel):
    """Internal user model with hashed password (for DB storage)."""
    
    id: str
    name: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
