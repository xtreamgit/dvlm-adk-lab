"""
User data models and schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Model for creating a new user via IAP.
    
    Note: Users are auto-created on first IAP login.
    No password needed - IAP handles authentication.
    """
    pass


class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    default_agent_id: Optional[int] = None


class User(UserBase):
    """User model returned to clients."""
    id: int
    is_active: bool = True
    default_agent_id: Optional[int] = None
    google_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model for internal database operations.
    
    Note: No password hash - IAP handles all authentication.
    """
    pass


class UserProfile(BaseModel):
    """User profile with preferences."""
    id: int
    user_id: int
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    preferences: Optional[dict] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Model for updating user profile."""
    theme: Optional[str] = Field(None, pattern="^(light|dark)$")
    language: Optional[str] = Field(None, min_length=2, max_length=5)
    timezone: Optional[str] = None
    preferences: Optional[dict] = None


class UserWithProfile(User):
    """User model with profile information."""
    profile: Optional[UserProfile] = None
