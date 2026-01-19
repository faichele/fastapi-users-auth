"""
FastAPI Dependencies for the fastapi_users_auth module.

This module contains all dependencies for the fastapi_users_auth module.
It includes:
- Current user authentication
- Checkings for user permissions
- Token extraction
- Session management
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.user_models import User
from ..services.auth_service import AuthService
from ..services.user_service import UserService, BaseUserService


# Globale Dependency-Factories, die in create_user_router über Closures gebunden werden
#UserServiceDep = Annotated[BaseUserService, Depends(lambda: None)]
#CurrentUserDep = Annotated[User, Depends(lambda: None)]
#CurrentActiveUserDep = Annotated[User, Depends(lambda: None)]
#CurrentSuperuserDep = Annotated[User, Depends(lambda: None)]


class AuthDependencies:
    """
    Class for providing FastAPI dependencies for authentication.

    This class encapsulates all authentication-related dependencies
    that can be used in FastAPI endpoints.
    """

    def __init__(self, auth_service: AuthService, user_service: UserService):
        """
        Initializes AuthDependencies with required services.

        Args:
            auth_service: AuthService instance
            user_service: UserService instance
        """
        self.auth_service = auth_service
        self.user_service = user_service
        self.security = HTTPBearer()

    def get_token(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]
    ) -> str:
        """
        Extracts a token from the HTTP Authorization header.

        Args:
            credentials: HTTP Bearer Credentials

        Returns:
            The extracted token

        Raises:
            HTTPException: When no valid token is found in the header
        """
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials

    def get_user_by_id(self, user_id: UUID) -> User:
        """
        Dependency to get a user by their UUID.

        Args:
            user_id: The UUID of the user

        Returns:
            The user with the given UUID

        Raises:
            HTTPException: When no user with the given UUID is found
        """
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def verify_user_access(
        self,
        target_user_id: UUID,
        current_user: User,
    ) -> User:
        """
        Verifies that the current user has access to a specific user's data.

        Users can only access their own data, unless they are superusers.

        Args:
            target_user_id: ID of the target user
            current_user: The current active user

        Returns:
            The target user

        Raises:
            HTTPException: When access is denied, or the target user does not exist
        """
        # Superusers can access all users' data
        if current_user.is_superuser:
            return self.get_user_by_id(target_user_id)

        # Regular users can only access their own data
        if current_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this user",
            )

        return current_user

    def require_permission(self, permission: str):
        """
        Creates a FastAPI Dependency to check for a specific permission.

        Args:
            permission: The required permission as a string

        Returns:
            FastAPI dependency that checks for the permission
        """

        def check_permission(
            current_user: Annotated[User, Depends(get_current_active_user)],
        ) -> User:
            user_permissions = self.auth_service.get_user_permissions(current_user)
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )
            return current_user

        return check_permission

    def optional_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    ) -> Optional[User]:
        """
        Retrieves the current user from the token, if available.

        This dependency does not raise an error if no token is provided.

        Args:
            credentials: Optional HTTP Bearer Credentials

        Returns:
            The current user if authenticated, otherwise None
        """
        if not credentials or credentials.scheme.lower() != "bearer":
            return None

        user = self.auth_service.get_current_user(credentials.credentials)
        return user if user and user.is_active else None


def get_current_user(auth_deps: AuthDependencies):
    def dependency(token: Annotated[str, Depends(auth_deps.get_token)]) -> User:
        user = auth_deps.auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    return dependency

def get_current_active_user(auth_deps: AuthDependencies):
    def dependency(current_user: Annotated[User, Depends(get_current_user(auth_deps))]) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )
        return current_user
    return dependency

def get_current_active_superuser(auth_deps: AuthDependencies):
    def dependency(current_user: Annotated[User, Depends(get_current_active_user(auth_deps))]) -> User:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user
    return dependency


# --- Globale Dependency-Typen für den Router ---
# Diese werden jetzt im Router mit den korrekten Funktionen initialisiert.
UserServiceDep = Annotated[BaseUserService, Depends(lambda: None)]
CurrentUserDep = Annotated[User, Depends(lambda: None)]
CurrentActiveUserDep = Annotated[User, Depends(lambda: None)]
CurrentSuperuserDep = Annotated[User, Depends(lambda: None)]


# Convenience-Funktionen für einfache Verwendung

def create_auth_dependencies(auth_service: AuthService, user_service: UserService) -> AuthDependencies:
    """
    Factory function to create an AuthDependencies instance.

    Args:
        auth_service: AuthService instance
        user_service: UserService instance

    Returns:
        An initialized AuthDependencies instance
    """
    return AuthDependencies(auth_service, user_service)


# Hinweis:
# Die früher hier definierten globalen Type-Aliases
#   CurrentUser, CurrentActiveUser, CurrentSuperuser
# wurden entfernt, da sie mit Lambdas arbeiteten, die zu
# ungültigen OpenAPI-Parametern (query.self / query.deps)
# und Laufzeitfehlern führen konnten. Stattdessen sollten
# Router explizit Depends(auth_deps.get_current_*...) nutzen.
