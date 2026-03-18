"""
Admin panel data models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: int
    corpus_id: Optional[int] = None
    corpus_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    changes: Optional[Any] = None  # Can be JSON string or dict
    metadata: Optional[Any] = None  # Can be JSON string or dict
    timestamp: datetime

    class Config:
        from_attributes = True


class CorpusMetadataBase(BaseModel):
    """Base corpus metadata model."""
    tags: Optional[Any] = None  # Can be text string or JSON array (jsonb)
    notes: Optional[str] = None


class CorpusMetadata(CorpusMetadataBase):
    """Corpus metadata model."""
    id: int
    corpus_id: int
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    last_synced_at: Optional[datetime] = None
    last_synced_by: Optional[int] = None
    last_synced_by_name: Optional[str] = None
    document_count: int = 0
    last_document_count_update: Optional[datetime] = None
    sync_status: str = "active"
    sync_error_message: Optional[str] = None

    class Config:
        from_attributes = True


class CorpusMetadataUpdate(BaseModel):
    """Model for updating corpus metadata."""
    tags: Optional[str] = None
    notes: Optional[str] = None
    sync_status: Optional[str] = None


class GroupAccessInfo(BaseModel):
    """Group access information."""
    group_id: int
    group_name: str
    permission: str


class AdminCorpusDetail(BaseModel):
    """Detailed corpus information for admin panel."""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    gcs_bucket: Optional[str] = None
    vertex_corpus_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    metadata: Optional[CorpusMetadata] = None
    groups_with_access: List[GroupAccessInfo] = []
    recent_activity: List[AuditLogEntry] = []
    document_count: int = 0


class BulkGrantRequest(BaseModel):
    """Request to grant access to multiple corpora."""
    corpus_ids: List[int] = Field(..., min_items=1)
    group_id: int
    permission: str = "read"


class BulkStatusUpdate(BaseModel):
    """Request to update status of multiple corpora."""
    corpus_ids: List[int] = Field(..., min_items=1)
    is_active: bool


class BulkOperationResult(BaseModel):
    """Result of bulk operation."""
    success: bool
    processed_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = []


class PermissionGrantRequest(BaseModel):
    """Request to grant permission to a corpus."""
    group_id: int
    permission: str = "read"


class SyncResult(BaseModel):
    """Result of corpus sync operation."""
    success: bool
    total_corpora: int
    added_count: int
    deactivated_count: int
    updated_count: int
    errors: List[str] = []
    message: str


class CorpusSyncSchedule(BaseModel):
    """Sync schedule configuration."""
    id: int
    corpus_id: int
    frequency: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class AdminUserDetail(BaseModel):
    """Detailed user information for admin panel."""
    id: int
    username: Optional[str] = None  # username column dropped by migration 014; derived from email where needed
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    groups: List[Dict[str, Any]] = []  # List of group info

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """Model for admin creating a new user (IAP-only; no username/password)."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    group_ids: List[int] = []  # Initial group assignments


class AdminUserUpdate(BaseModel):
    """Model for admin updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class UserGroupAssignment(BaseModel):
    """Model for assigning/removing user from groups."""
    user_id: int
    group_id: int
