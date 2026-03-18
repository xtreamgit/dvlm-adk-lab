"""
Corpus data models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CorpusBase(BaseModel):
    """Base corpus model."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    gcs_bucket: Optional[str] = None


class CorpusCreate(CorpusBase):
    """Model for creating a new corpus."""
    vertex_corpus_id: Optional[str] = None


class CorpusUpdate(BaseModel):
    """Model for updating a corpus."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    gcs_bucket: Optional[str] = None
    vertex_corpus_id: Optional[str] = None
    is_active: Optional[bool] = None


class Corpus(CorpusBase):
    """Corpus model returned to clients."""
    id: int
    vertex_corpus_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


class GroupCorpusAccess(BaseModel):
    """Group-Corpus access association."""
    id: int
    group_id: int
    corpus_id: int
    permission: str = "read"  # read, write, admin
    granted_at: datetime

    class Config:
        from_attributes = True


class CorpusWithAccess(Corpus):
    """Corpus model with user access information."""
    has_access: bool = False
    permission: Optional[str] = None  # read, write, admin
    is_active_in_session: bool = False
