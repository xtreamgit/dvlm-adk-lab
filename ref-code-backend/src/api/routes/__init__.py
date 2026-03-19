"""
API route modules.
"""

from .users import router as users_router
from .agents import router as agents_router
from .corpora import router as corpora_router
from .admin import router as admin_router
from .iap_auth import router as iap_auth_router
from .documents import router as documents_router
from .chatbot_admin import router as chatbot_admin_router
from .google_groups_admin import router as google_groups_admin_router
from .model_armor import router as model_armor_router

__all__ = [
    "users_router",
    "agents_router",
    "corpora_router",
    "admin_router",
    "iap_auth_router",
    "documents_router",
    "chatbot_admin_router",
    "google_groups_admin_router",
    "model_armor_router",
]
