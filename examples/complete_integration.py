"""
Vollständiges Beispiel für die Integration des Multi-Provider-Auth-Systems.

Dieses Beispiel zeigt, wie die verschiedenen Services und Router
in einer FastAPI-Anwendung zusammengeführt werden.
"""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Angenommen, diese Imports existieren bereits in Ihrer Anwendung
from backend.database.base import get_db_session  # Ihre DB-Session-Factory
from backend.app.config import get_settings  # Ihre App-Konfiguration

# Neue Multi-Provider-Imports
from .config.auth_config import get_config_for_environment
from .services.service_factory import create_services_from_config
from .dependencies.multi_provider_auth_deps import create_auth_dependencies
from .routers.multi_provider_auth_router import create_multi_provider_auth_router
from .routers.user_router import UserRouter


class AuthenticationSystem:
    """
    Hauptklasse für das Authentifizierungssystem.

    Verwaltet die Initialisierung und Konfiguration aller Auth-Komponenten.
    """

    def __init__(self, app: FastAPI, environment: str = "development"):
        """
        Initialisiert das Authentifizierungssystem.

        Args:
            app: FastAPI-Anwendungsinstanz
            environment: Umgebung ("development", "production", "testing")
        """
        self.app = app
        self.environment = environment
        self.config = get_config_for_environment(environment)

        # Services werden bei der ersten Verwendung initialisiert
        self._user_service = None
        self._auth_manager = None
        self._auth_deps = None

    def initialize(self, db_session_factory=get_db_session):
        """
        Initialisiert alle Services und Router.

        Args:
            db_session_factory: Factory-Funktion für DB-Sessions
        """
        # Services erstellen (wird bei der ersten DB-Session-Erstellung gemacht)
        self.db_session_factory = db_session_factory

        # Router hinzufügen
        self._setup_routers()

        print(f"🔐 Authentication system initialized for {self.environment}")
        self._print_provider_info()

    def get_services(self, db_session: Session):
        """
        Lazy-Loading der Services mit DB-Session.

        Args:
            db_session: SQLAlchemy Session

        Returns:
            Tuple aus (user_service, auth_manager, auth_deps)
        """
        if self._user_service is None:
            self._user_service, self._auth_manager = create_services_from_config(
                self.config,
                db_session
            )
            self._auth_deps = create_auth_dependencies(
                self._auth_manager,
                self._user_service
            )

        return self._user_service, self._auth_manager, self._auth_deps

    def _setup_routers(self):
        """Fügt alle Auth-Router zur FastAPI-App hinzu."""

        # Dependency für Services mit DB-Session
        def get_auth_services(db: Session = Depends(self.db_session_factory)):
            return self.get_services(db)

        # Multi-Provider Auth Router
        def get_multi_auth_router(services=Depends(get_auth_services)):
            user_service, auth_manager, auth_deps = services
            return create_multi_provider_auth_router(
                auth_manager, user_service, auth_deps, "/auth"
            )

        # User Management Router
        def get_user_router(services=Depends(get_auth_services)):
            user_service, auth_manager, auth_deps = services
            user_router = UserRouter(user_service, auth_deps, "/users")
            return user_router.router

        # Router zur App hinzufügen
        @self.app.get("/auth/info")
        def get_auth_info(services=Depends(get_auth_services)):
            """Informationen über verfügbare Auth-Provider."""
            user_service, auth_manager, auth_deps = services
            return {
                "environment": self.environment,
                "providers": auth_manager.list_auth_providers(),
                "stats": auth_manager.get_stats()
            }

        # Dynamische Router-Registrierung
        self._register_dynamic_routers()

    def _register_dynamic_routers(self):
        """Registriert Router dynamisch zur Laufzeit."""

        # Auth Router
        @self.app.on_event("startup")
        async def setup_auth_routes():
            # Dummy DB-Session für Setup (in echten Apps würden Sie Ihre DB-Factory verwenden)
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            # Beispiel: In-Memory SQLite für Demo
            engine = create_engine("sqlite:///./demo_auth.db")
            SessionLocal = sessionmaker(bind=engine)

            with SessionLocal() as db:
                user_service, auth_manager, auth_deps = self.get_services(db)

                # Multi-Provider Auth Router
                multi_auth_router = create_multi_provider_auth_router(
                    auth_manager, user_service, auth_deps, "/auth"
                )
                self.app.include_router(multi_auth_router)

                # User Router
                user_router = UserRouter(user_service, auth_deps, "/users")
                self.app.include_router(user_router.router)

    def _print_provider_info(self):
        """Gibt Informationen über konfigurierte Provider aus."""
        providers = self.config.get("auth_providers", [])
        enabled_providers = [p for p in providers if p.get("enabled", True)]

        print(f"📋 Configured auth providers ({len(enabled_providers)} enabled):")
        for provider in sorted(enabled_providers, key=lambda x: x.get("priority", 0), reverse=True):
            priority = provider.get("priority", 0)
            provider_type = provider.get("type", "unknown")
            print(f"  • {provider_type} (priority: {priority})")

    def add_custom_provider(self, provider_config: dict):
        """
        Fügt einen benutzerdefinierten Provider hinzu.

        Args:
            provider_config: Provider-Konfiguration
        """
        if "auth_providers" not in self.config:
            self.config["auth_providers"] = []

        self.config["auth_providers"].append(provider_config)

        # Services neu initialisieren bei der nächsten Verwendung
        self._user_service = None
        self._auth_manager = None
        self._auth_deps = None

    def get_config(self):
        """Gibt die aktuelle Konfiguration zurück."""
        return self.config.copy()


# Factory-Funktionen für einfache Integration

def create_auth_system(app: FastAPI, environment: str = "development") -> AuthenticationSystem:
    """
    Erstellt und konfiguriert ein komplettes Authentifizierungssystem.

    Args:
        app: FastAPI-Anwendung
        environment: Umgebung

    Returns:
        Konfiguriertes AuthenticationSystem
    """
    auth_system = AuthenticationSystem(app, environment)
    auth_system.initialize()
    return auth_system


# Beispiel für die Verwendung in main.py
def example_integration():
    """
    Beispiel, wie das System in eine FastAPI-App integriert wird.
    """

    app = FastAPI(title="Multi-Provider Auth Demo")

    # Einfache Integration
    auth_system = create_auth_system(app, "development")

    # Zusätzlichen OAuth-Provider hinzufügen
    custom_provider = {
        "type": "oauth_discord",
        "priority": 5,
        "enabled": True
    }
    auth_system.add_custom_provider(custom_provider)

    # Root-Endpunkt
    @app.get("/")
    def root():
        return {
            "message": "Multi-Provider Authentication Demo",
            "auth_info_url": "/auth/info",
            "providers_url": "/auth/providers"
        }

    return app


# Beispiel für erweiterte Konfiguration
def example_advanced_integration():
    """
    Beispiel für erweiterte Integration mit benutzerdefinierten Services.
    """

    app = FastAPI(title="Advanced Multi-Provider Auth")

    # Benutzerdefinierte Konfiguration
    custom_config = {
        "SECRET_KEY": "advanced-secret-key",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 60,
        "REFRESH_TOKEN_EXPIRE_DAYS": 30,
        "user_provider": "database",
        "auth_providers": [
            {
                "type": "database",
                "priority": 10,
                "enabled": True
            },
            {
                "type": "oauth_google",
                "priority": 8,
                "enabled": True
            }
        ],
        "oauth_providers": {
            "google": {
                "client_id": "your-google-client-id",
                "client_secret": "your-google-client-secret",
                "redirect_uri": "http://localhost:8000/auth/oauth/callback/google",
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile"
            }
        }
    }

    # System mit benutzerdefinierter Konfiguration
    auth_system = AuthenticationSystem(app, "development")
    auth_system.config = custom_config
    auth_system.initialize()

    # Benutzerdefinierte Middleware hinzufügen
    @app.middleware("http")
    async def auth_middleware(request, call_next):
        # Hier könnten Sie benutzerdefinierte Auth-Logik hinzufügen
        response = await call_next(request)
        return response

    return app


if __name__ == "__main__":
    # Beispiel-App starten
    app = example_integration()

    # Mit uvicorn starten
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
