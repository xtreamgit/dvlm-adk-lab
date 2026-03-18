"""
Session data models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SessionBase(BaseModel):
    """Base session model."""
    session_id: str
    user_id: int


class SessionCreate(SessionBase):
    """Model for creating a new session."""
    active_agent_id: Optional[int] = None
    active_corpora: Optional[List[int]] = None


class SessionUpdate(BaseModel):
    """Model for updating a session."""
    active_agent_id: Optional[int] = None
    active_corpora: Optional[List[int]] = None
    last_activity: Optional[datetime] = None
    is_active: Optional[bool] = None


class SessionData(SessionBase):
    """Session model returned to clients."""
    id: int
    active_agent_id: Optional[int] = None
    active_agent_name: Optional[str] = None
    active_agent_display_name: Optional[str] = None
    active_corpora: Optional[List[int]] = None
    created_at: datetime
    last_activity: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class SessionCorpusSelection(BaseModel):
    """Session corpus selection for restoration."""
    id: int
    user_id: int
    corpus_id: int
    last_selected_at: datetime

    class Config:
        from_attributes = True
