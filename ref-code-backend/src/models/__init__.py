"""
Data models and Pydantic schemas for the application.
"""

from .user import (
    User,
    UserCreate,
    UserUpdate,
    UserProfile,
    UserProfileUpdate,
    UserInDB,
    UserWithProfile
)

from .group import (
    Group,
    GroupCreate,
    GroupUpdate,
    Role,
    RoleCreate,
    UserGroup,
    GroupRole
)

from .agent import (
    Agent,
    AgentCreate,
    UserAgentAccess,
    AgentWithAccess
)

from .corpus import (
    Corpus,
    CorpusCreate,
    CorpusUpdate,
    GroupCorpusAccess,
    CorpusWithAccess
)

from .session import (
    SessionData,
    SessionCreate,
    SessionUpdate,
    SessionCorpusSelection
)

from .admin import (
    AuditLogEntry,
    CorpusMetadata,
    CorpusMetadataUpdate,
    GroupAccessInfo,
    AdminCorpusDetail,
    BulkGrantRequest,
    BulkStatusUpdate,
    BulkOperationResult,
    PermissionGrantRequest,
    SyncResult,
    CorpusSyncSchedule,
)

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "UserProfile",
    "UserProfileUpdate",
    "UserInDB",
    "UserWithProfile",
    "Group",
    "GroupCreate",
    "GroupUpdate",
    "Role",
    "RoleCreate",
    "UserGroup",
    "GroupRole",
    "Agent",
    "AgentCreate",
    "UserAgentAccess",
    "AgentWithAccess",
    "Corpus",
    "CorpusCreate",
    "CorpusUpdate",
    "GroupCorpusAccess",
    "CorpusWithAccess",
    "SessionData",
    "SessionCreate",
    "SessionUpdate",
    "SessionCorpusSelection",
]
