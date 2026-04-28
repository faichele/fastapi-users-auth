"""
Routers-Package für das fastapi_users_auth Modul.
"""

from .auth_router import AuthRouter, create_auth_router
from .user_router import UserRouter, create_user_router
from .settings_router import AuthSettingsRouter, create_auth_settings_router

__all__ = [
    "AuthRouter",
    "create_auth_router",
    "UserRouter",
    "create_user_router",
    "AuthSettingsRouter",
    "create_auth_settings_router",
]
