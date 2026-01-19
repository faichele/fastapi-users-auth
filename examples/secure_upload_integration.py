"""
Beispiel für die Integration der abgesicherten Router in die Hauptanwendung.

Dieses Beispiel zeigt, wie Sie den upload_router mit Authentifizierung
in Ihre FastAPI-Anwendung integrieren.
"""

from fastapi import FastAPI

from backend.app.config import settings
from backend.database.base import get_db
from packages.fastapi_users_auth import UserAuthModule
from packages.fastapi_users_auth.services import AuthService, UserService
from packages.fastapi_users_auth.dependencies import AuthDependencies

# Import der Router
from backend.routes.upload_router import router as upload_router, init_upload_router_auth
from backend.routes.albums_router import router as albums_router
from backend.routes.images_router import router as images_router


def setup_authenticated_app():
    """
    Erstellt eine FastAPI-App mit Authentifizierung für alle Router.
    """

    app = FastAPI(
        title="Rideto Gallery",
        description="Gallery-Anwendung mit Authentifizierung",
        version="1.0.0"
    )

    # Konfiguration für fastapi_users_auth
    class AuthConfig:
        SECRET_KEY = settings.SECRET_KEY
        ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    auth_config = AuthConfig()

    # Session-Dependency
    def get_session():
        return next(get_db())

    # Services initialisieren
    db_session = get_session()
    auth_service = AuthService(db_session, auth_config)
    user_service = UserService(db_session)

    # Dependencies initialisieren
    auth_deps = AuthDependencies(auth_service, user_service)

    # 1. Methode: UserAuthModule verwenden (einfachste Variante)
    auth_module = UserAuthModule()
    auth_module.init_app(app, db_session, auth_config)

    # 2. Upload Router mit Authentifizierung initialisieren
    init_upload_router_auth(auth_deps)

    # Router hinzufügen
    app.include_router(upload_router, prefix="/api")
    app.include_router(albums_router, prefix="/api")
    app.include_router(images_router, prefix="/api")

    return app


# Alternative: Manuelle Router-Konfiguration
def setup_manual_auth_integration():
    """
    Alternative Methode zur manuellen Integration der Authentifizierung.
    """

    app = FastAPI()

    # Auth-Setup
    class AuthConfig:
        SECRET_KEY = settings.SECRET_KEY
        ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    auth_config = AuthConfig()
    db_session = next(get_db())

    # Services
    auth_service = AuthService(db_session, auth_config)
    user_service = UserService(db_session)
    auth_deps = AuthDependencies(auth_service, user_service)

    # Auth-Router manuell erstellen
    from packages.fastapi_users_auth.routers import create_auth_router, create_user_router

    auth_router = create_auth_router(auth_service, auth_deps, prefix="/api/auth")
    user_router = create_user_router(user_service, auth_deps, prefix="/api/users")

    app.include_router(auth_router)
    app.include_router(user_router)

    # Upload Router initialisieren
    init_upload_router_auth(auth_deps)
    app.include_router(upload_router, prefix="/api")

    return app


if __name__ == "__main__":
    # App mit Authentifizierung starten
    app = setup_authenticated_app()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
