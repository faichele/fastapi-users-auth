"""
Dependencies-Package für das fastapi_users_auth Modul.
"""

from .auth_deps import (
    AuthDependencies,
    create_auth_dependencies,
    CurrentUserDep,
    CurrentActiveUserDep,
    CurrentSuperuserDep
)
from .auth_provider import (
    AuthProvider,
    get_auth_deps,
    get_current_active_superuser_dependency,
    get_current_active_user_dependency,
    get_current_user_dependency,
    get_current_superuser_dependency,
)

from .web_auth_deps import auth_or_redirect, get_mandatory_current_user, get_optional_current_user


__all__ = [
    "AuthDependencies",
    "create_auth_dependencies",
    "CurrentUserDep",
    "CurrentActiveUserDep",
    "CurrentSuperuserDep",
    "AuthProvider",
    "get_auth_deps",
    "get_current_active_superuser_dependency",
    "get_current_active_user_dependency",
    "get_current_user_dependency",
    "get_current_superuser_dependency",
    "auth_or_redirect",
    "get_optional_current_user",
    "get_mandatory_current_user"
]
