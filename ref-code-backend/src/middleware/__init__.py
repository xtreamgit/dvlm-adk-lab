"""
Middleware for request processing and authentication.
"""

from .iap_auth_middleware import get_current_user_iap as get_current_user
from .iap_auth_middleware import get_current_user_optional_iap as get_current_user_optional

__all__ = [
    "get_current_user",
    "get_current_user_optional",
]
