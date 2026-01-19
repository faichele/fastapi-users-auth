"""
Wiederverwendbares Benutzer- und Authentifizierungsmodul für FastAPI-Anwendungen.

Dieses Modul bietet eine vollständige Lösung für:
- Benutzerregistrierung und -verwaltung
- JWT-basierte Authentifizierung
- Passwort-Hashing und -Verifikation
- Rollen- und Berechtigungsverwaltung
- Password Reset Funktionalität

Usage:
    from fastapi_users_auth import UserAuthModule

    # In FastAPI-App einbinden
    auth_module = UserAuthModule(app, database_session, settings)
"""

from .models.user_models import (
    User,
    UserBase,
    UserCreate,
    UserUpdate,
    UserPublic,
    UserInDB,
    UserRegister,
    UserLogin,
    UsersPublic,
    UpdatePassword,
    UserUpdateMe
)

from .models.auth_models import (
    Token,
    TokenData,
    TokenPayload,
    TokenPayloadData,
    NewPassword,
    NewPasswordRequest,
    Message
)

from .services.auth_service import AuthService
from .services.user_service import UserService
from .utils.security import SecurityUtils
from .utils.token_utils import TokenUtils
from .dependencies.auth_deps import AuthDependencies
from .routers.auth_router import AuthRouter
from .routers.user_router import UserRouter

__version__ = "ß.0.2"

__all__ = [
    # User Models
    "User",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPublic",
    "UserInDB",
    "UserRegister",
    "UserLogin",
    "UsersPublic",
    "UpdatePassword",
    "UserUpdateMe",

    # Auth Models
    "Token",
    "TokenData",
    "TokenPayload",
    "TokenPayloadData",
    "NewPassword",
    "NewPasswordRequest",
    "Message",

    # Services
    "AuthService",
    "UserService",

    # Utils
    "SecurityUtils",
    "TokenUtils",

    # Dependencies
    "AuthDependencies",

    # Routers
    "AuthRouter",
    "UserRouter",
]


class UserAuthModule:
    """
    Hauptklasse zum Einbinden des Authentifizierungsmoduls in eine FastAPI-Anwendung.

    Diese Klasse bietet eine einfache Schnittstelle zur Integration des kompletten
    Authentifizierungssystems in bestehende FastAPI-Anwendungen.
    """

    def __init__(self, app=None, database_session=None, config=None):
        self.app = app
        self.database_session = database_session
        self.config = config

        if app is not None:
            self.init_app(app, database_session, config)

    def init_app(self, app, database_session, config):
        """Initialisiert das Modul mit einer FastAPI-App."""
        self.app = app
        self.database_session = database_session
        self.config = config

        # Services initialisieren
        self.user_service = UserService(database_session)
        self.auth_service = AuthService(database_session, config)

        # Dependencies initialisieren
        self.auth_deps = AuthDependencies(self.auth_service, self.user_service)

        # Router initialisieren und einbinden
        self.auth_router = AuthRouter(self.auth_service, self.auth_deps)
        self.user_router = UserRouter(self.user_service, self.auth_deps)

        # Router zur App hinzufügen
        app.include_router(self.auth_router.router)
        app.include_router(self.user_router.router)

    def get_current_user_dependency(self):
        """Gibt die Dependency für den aktuellen Benutzer zurück."""
        return self.auth_deps.get_current_user

    def get_current_active_user_dependency(self):
        """Gibt die Dependency für den aktuellen aktiven Benutzer zurück."""
        return self.auth_deps.get_current_active_user

    def get_superuser_dependency(self):
        """Gibt die Dependency für Superuser zurück."""
        return self.auth_deps.get_current_active_superuser
