"""
Erweiterte FastAPI Dependencies für das fastapi_users_auth Modul.

Dieses Modul enthält alle Dependencies für das fastapi_users_auth Modul mit
Unterstützung für Multi-Provider Authentication.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.user_models import User
from ..services.auth_service_manager import AuthServiceManager
from ..services.base_user_service import BaseUserService


class MultiProviderAuthDependencies:
    """
    Klasse für FastAPI Dependencies mit Multi-Provider-Unterstützung.

    Diese Klasse kapselt alle authentifizierungsbezogenen Dependencies
    für die Verwendung mit mehreren Auth-Providern.
    """

    def __init__(self, auth_manager: AuthServiceManager, user_service: BaseUserService):
        """
        Initialisiert MultiProviderAuthDependencies mit erforderlichen Services.

        Args:
            auth_manager: AuthServiceManager-Instanz
            user_service: UserService-Instanz
        """
        self.auth_manager = auth_manager
        self.user_service = user_service
        self.security = HTTPBearer()

    def get_token(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]
    ) -> str:
        """
        Extrahiert einen Token aus dem HTTP Authorization Header.

        Args:
            credentials: HTTP Bearer Credentials

        Returns:
            Der extrahierte Token

        Raises:
            HTTPException: Wenn Token-Format ungültig ist
        """
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials

    def get_current_user(self, token: Annotated[str, Depends(get_token)]) -> User:
        """
        Holt den aktuellen Benutzer anhand des Tokens.

        Args:
            token: JWT-Access-Token

        Returns:
            User-Objekt

        Raises:
            HTTPException: Wenn Token ungültig oder Benutzer nicht gefunden
        """
        user = self.auth_manager.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def get_current_active_user(
        self,
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        """
        Holt den aktuellen aktiven Benutzer.

        Args:
            current_user: Aktueller Benutzer aus get_current_user

        Returns:
            User-Objekt wenn aktiv

        Raises:
            HTTPException: Wenn Benutzer nicht aktiv ist
        """
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user

    def get_current_active_superuser(
        self,
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        """
        Holt den aktuellen aktiven Superuser.

        Args:
            current_user: Aktueller aktiver Benutzer

        Returns:
            User-Objekt wenn Superuser

        Raises:
            HTTPException: Wenn Benutzer kein Superuser ist
        """
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )
        return current_user

    def get_optional_current_user(
        self,
        token: Annotated[Optional[str], Depends(lambda: None)]
    ) -> Optional[User]:
        """
        Holt den aktuellen Benutzer optional (ohne Exception bei Fehler).

        Args:
            token: Optionaler JWT-Access-Token

        Returns:
            User-Objekt wenn Token gültig, None andernfalls
        """
        if not token:
            return None

        try:
            return self.auth_manager.get_current_user(token)
        except Exception:
            return None

    def require_permission(self, permission: str):
        """
        Dependency-Factory für spezifische Berechtigungen.

        Args:
            permission: Erforderliche Berechtigung

        Returns:
            FastAPI Dependency-Funktion
        """
        def check_permission(
            current_user: Annotated[User, Depends(self.get_current_active_user)]
        ) -> User:
            permissions = self.auth_manager.get_user_permissions(current_user)
            if permission not in permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            return current_user

        return check_permission

    def require_user_or_superuser(self, user_id_param: str = "user_id"):
        """
        Dependency-Factory für Zugriff auf eigene Daten oder Superuser-Rechte.

        Args:
            user_id_param: Name des Path-Parameters mit der Benutzer-ID

        Returns:
            FastAPI Dependency-Funktion
        """
        def check_user_access(
            current_user: Annotated[User, Depends(self.get_current_active_user)],
            user_id: UUID  # Dies wird vom Router als Path-Parameter übergeben
        ) -> User:
            if not current_user.is_superuser and current_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to access this user"
                )
            return current_user

        return check_user_access

    def get_auth_manager(self) -> AuthServiceManager:
        """
        Gibt den AuthServiceManager zurück.

        Returns:
            AuthServiceManager-Instanz
        """
        return self.auth_manager

    def get_user_service(self) -> BaseUserService:
        """
        Gibt den UserService zurück.

        Returns:
            UserService-Instanz
        """
        return self.user_service


# Rückwärtskompatibilität mit dem alten AuthDependencies
class AuthDependencies(MultiProviderAuthDependencies):
    """
    Kompatibilitäts-Wrapper für das alte AuthDependencies Interface.

    Ermöglicht die Verwendung des neuen Multi-Provider-Systems mit
    dem alten Interface für einfache Migration.
    """

    def __init__(self, auth_manager: AuthServiceManager, user_service: BaseUserService):
        """
        Initialisiert AuthDependencies mit Multi-Provider-Unterstützung.

        Args:
            auth_manager: AuthServiceManager-Instanz
            user_service: UserService-Instanz
        """
        super().__init__(auth_manager, user_service)

    def get_auth_service(self):
        """
        Gibt den primären AuthService zurück (für Rückwärtskompatibilität).

        Returns:
            Primärer AuthService oder AuthServiceManager
        """
        # Versuche den ersten verfügbaren Provider zu verwenden
        providers = self.auth_manager.auth_providers
        if providers:
            return providers[0]  # Primärer Provider
        return self.auth_manager  # Fallback auf Manager


def create_auth_dependencies(
    auth_manager: AuthServiceManager,
    user_service: BaseUserService
) -> AuthDependencies:
    """
    Factory-Funktion zur Erstellung von AuthDependencies.

    Args:
        auth_manager: AuthServiceManager-Instanz
        user_service: UserService-Instanz

    Returns:
        Konfigurierte AuthDependencies-Instanz
    """
    return AuthDependencies(auth_manager, user_service)
