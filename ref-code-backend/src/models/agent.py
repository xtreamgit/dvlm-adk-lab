"""
Agent data models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Base agent model."""
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config_path: str = Field(..., min_length=1)


class AgentCreate(AgentBase):
    """Model for creating a new agent."""
    pass


class Agent(AgentBase):
    """Agent model returned to clients."""
    id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserAgentAccess(BaseModel):
    """User-Agent access association."""
    id: int
    user_id: int
    agent_id: int
    granted_at: datetime

    class Config:
        from_attributes = True


class AgentWithAccess(Agent):
    """Agent model with user access information."""
    has_access: bool = False
    is_default: bool = False
    agent_type: Optional[str] = None
    tools: List[str] = []
