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
]
