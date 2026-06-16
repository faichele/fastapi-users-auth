"""
Zentrale Authentifizierungs-Provider für das fastapi_users_auth-Modul.

Dieser Provider verwaltet die AuthDependencies-Instanz zentral und stellt sie
allen Routern über das Factory-Pattern zur Verfügung.
"""
from typing import Optional
from fastapi import HTTPException

from .auth_deps import AuthDependencies, get_current_user, get_current_active_user, get_current_active_superuser
from fastapi_logging_manager import logger_manager

# Logger für dieses Modul
logger = logger_manager.get_logger(name="auth_provider", to_file=True)


class AuthProvider:
    """
    Zentraler Provider für Authentifizierungs-Dependencies.

    Implementiert das Singleton-Pattern, um eine einzige AuthDependencies-Instanz
    in der gesamten Anwendung zu verwalten.
    """

    _instance: Optional[AuthDependencies] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, auth_deps: AuthDependencies) -> None:
        """
        Initialisiert den globalen AuthProvider mit einer AuthDependencies-Instanz.

        Diese Methode sollte beim App-Start einmalig aufgerufen werden.

        Args:
            auth_deps: Konfigurierte AuthDependencies-Instanz

        Raises:
            RuntimeError: Wenn der Provider bereits initialisiert wurde
        """
        if cls._initialized:
            logger.warning("AuthProvider is already initialized. Skipping re-initialization.")
            return

        cls._instance = auth_deps
        cls._initialized = True
        logger.info("AuthProvider successfully initialized")

    @classmethod
    def get_instance(cls) -> AuthDependencies:
        """
        Gibt die AuthDependencies-Instanz zurück.

        Returns:
            AuthDependencies: Die konfigurierte AuthDependencies-Instanz

        Raises:
            HTTPException: Wenn der Provider nicht initialisiert wurde
        """
        if not cls._initialized or cls._instance is None:
            logger.error("AuthProvider not initialized. Call initialize() first.")
            raise HTTPException(
                status_code=500,
                detail="Authentication provider not initialized. Contact system administrator."
            )
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Prüft, ob der Provider initialisiert wurde.

        Returns:
            bool: True wenn initialisiert, False sonst
        """
        return cls._initialized and cls._instance is not None

    @classmethod
    def reset(cls) -> None:
        """
        Setzt den Provider zurück (hauptsächlich für Tests).
        """
        cls._instance = None
        cls._initialized = False
        logger.debug("AuthProvider reset")


# FastAPI Dependency Functions

def get_auth_deps() -> AuthDependencies:
    """
    FastAPI Dependency Function zum Holen der AuthDependencies.

    Diese Funktion kann direkt in FastAPI-Endpunkten als Dependency verwendet werden.

    Returns:
        AuthDependencies: Die konfigurierte AuthDependencies-Instanz
    """
    return AuthProvider.get_instance()


def get_current_user_dependency():
    """
    Factory-Funktion für die get_current_user Dependency.

    Returns:
        Callable: Die get_current_user Dependency-Funktion
    """
    return get_current_user


def get_current_active_user_dependency():
    """
    Factory-Funktion für die get_current_active_user Dependency.

    Returns:
        Callable: Die get_current_active_user Dependency-Funktion
    """
    return get_current_active_user


def get_current_active_superuser_dependency():
    """
    Factory-Funktion für die get_current_active_superuser Dependency.

    Returns:
        Callable: Die get_current_active_superuser Dependency-Funktion
    """
    return get_current_active_superuser


def get_current_superuser_dependency():
    """
    Alias-Factory für Superuser-Dependency (Rückwärtskompatibilität).

    Returns:
        Callable: Die get_current_active_superuser Dependency-Funktion
    """
    return get_current_active_superuser_dependency()

