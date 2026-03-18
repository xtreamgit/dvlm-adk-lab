"""
Group and Role data models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    """Base group model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Model for creating a new group."""
    pass


class GroupUpdate(BaseModel):
    """Model for updating a group."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Group(GroupBase):
    """Group model returned to clients."""
    id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role model."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleCreate(RoleBase):
    """Model for creating a new role."""
    pass


class Role(RoleBase):
    """Role model returned to clients."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserGroup(BaseModel):
    """User-Group association."""
    id: int
    user_id: int
    group_id: int
    assigned_at: datetime

    class Config:
        from_attributes = True


class GroupRole(BaseModel):
    """Group-Role association."""
    id: int
    group_id: int
    role_id: int
    assigned_at: datetime

    class Config:
        from_attributes = True
