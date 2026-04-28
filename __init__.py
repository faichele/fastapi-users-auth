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

from importlib import import_module

from .model_factory import AuthORMModels, create_auth_models, configure_auth_models
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

from .models.group_models import (
    Group,
    UserGroupMembership,
    GroupBase,
    GroupCreate,
    GroupUpdate,
    GroupInDB,
    GroupPublic,
    GroupsPublic,
    UserGroupMembershipBase,
    UserGroupMembershipCreate,
    UserGroupMembershipUpdate,
    UserGroupMembershipInDB,
    UserGroupMembershipPublic,
    UserGroupMembershipsPublic,
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

__version__ = "ß.0.2"

_LAZY_IMPORTS = {
    "AuthService": (".services.auth_service", "AuthService"),
    "UserService": (".services.user_service", "UserService"),
    "SecurityUtils": (".utils.security", "SecurityUtils"),
    "TokenUtils": (".utils.token_utils", "TokenUtils"),
    "AuthDependencies": (".dependencies.auth_deps", "AuthDependencies"),
    "AuthProvider": (".dependencies.auth_provider", "AuthProvider"),
    "AuthRouter": (".routers.auth_router", "AuthRouter"),
    "UserRouter": (".routers.user_router", "UserRouter"),
    "AuthSettingsRouter": (".routers.settings_router", "AuthSettingsRouter"),
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module_name, attribute_name = _LAZY_IMPORTS[name]
        module = import_module(module_name, __name__)
        value = getattr(module, attribute_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Factory
    "AuthORMModels",
    "create_auth_models",
    "configure_auth_models",

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

    # Group Models
    "Group",
    "UserGroupMembership",
    "GroupBase",
    "GroupCreate",
    "GroupUpdate",
    "GroupInDB",
    "GroupPublic",
    "GroupsPublic",
    "UserGroupMembershipBase",
    "UserGroupMembershipCreate",
    "UserGroupMembershipUpdate",
    "UserGroupMembershipInDB",
    "UserGroupMembershipPublic",
    "UserGroupMembershipsPublic",

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
    "AuthProvider",

    # Routers
    "AuthRouter",
    "UserRouter",
    "AuthSettingsRouter",
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

        auth_service_class = __getattr__("AuthService")
        user_service_class = __getattr__("UserService")
        auth_dependencies_class = __getattr__("AuthDependencies")
        auth_router_class = __getattr__("AuthRouter")
        user_router_class = __getattr__("UserRouter")

        # Services initialisieren
        self.user_service = user_service_class(database_session)
        self.auth_service = auth_service_class(database_session, config)

        # Dependencies initialisieren
        self.auth_deps = auth_dependencies_class(self.auth_service, self.user_service)

        # Router initialisieren und einbinden
        self.auth_router = auth_router_class(self.auth_service, self.auth_deps)
        self.user_router = user_router_class(self.user_service, self.auth_deps)

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
