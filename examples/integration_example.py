"""
Beispiel für die Integration des fastapi_users_auth Moduls in eine FastAPI-Anwendung.

Dieses Beispiel zeigt, wie das fastapi_users_auth Modul in eine bestehende
FastAPI-Anwendung integriert werden kann.
"""

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import des fastapi_users_auth Moduls
from users_auth import UserAuthModule
from users_auth.models.user_models import User
from users_auth.services import AuthService, UserService
from users_auth.dependencies import AuthDependencies
from users_auth.routers import create_auth_router, create_user_router


def create_app_with_auth(database_url: str, secret_key: str) -> FastAPI:
    """
    Erstellt eine FastAPI-App mit integriertem Authentifizierungsmodul.

    Args:
        database_url: SQLAlchemy Database URL
        secret_key: Secret Key für JWT-Token

    Returns:
        Konfigurierte FastAPI-App
    """

    # FastAPI-App erstellen
    app = FastAPI(
        title="Rideto Gallery with Authentication",
        description="Gallery-Anwendung mit wiederverwendbarem Authentifizierungsmodul",
        version="1.0.0"
    )

    # Datenbank-Setup
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Tabellen erstellen (in Produktion würde man Alembic verwenden)
    User.metadata.create_all(bind=engine)

    # Konfigurationsobjekt (vereinfacht)
    class Config:
        SECRET_KEY = secret_key
        ACCESS_TOKEN_EXPIRE_MINUTES = 30

    config = Config()

    # Dependency für Datenbank-Session
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Services initialisieren
    def get_auth_service(db: Session = next(get_db())):
        return AuthService(db, config)

    def get_user_service(db: Session = next(get_db())):
        return UserService(db)

    # Dependencies initialisieren
    auth_service = get_auth_service()
    user_service = get_user_service()
    auth_deps = AuthDependencies(auth_service, user_service)

    # Router erstellen und einbinden
    auth_router = create_auth_router(auth_service, auth_deps, prefix="/api/auth")
    user_router = create_user_router(user_service, auth_deps, prefix="/api/users")

    app.include_router(auth_router)
    app.include_router(user_router)

    return app


def integrate_with_existing_app(app: FastAPI, db_session, config):
    """
    Integriert das fastapi_users_auth Modul in eine bestehende FastAPI-App.

    Args:
        app: Bestehende FastAPI-App
        db_session: SQLAlchemy Session
        config: Konfigurationsobjekt
    """

    # UserAuthModule verwenden (Convenience-Klasse)
    auth_module = UserAuthModule()
    auth_module.init_app(app, db_session, config)

    # Alternative: Manuelle Integration
    # auth_service = AuthService(db_session, config)
    # user_service = UserService(db_session)
    # auth_deps = AuthDependencies(auth_service, user_service)

    # auth_router = create_auth_router(auth_service, auth_deps)
    # user_router = create_user_router(user_service, auth_deps)

    # app.include_router(auth_router)
    # app.include_router(user_router)


# Beispiel für die Verwendung in der bestehenden Rideto-App
def integrate_rideto_app():
    """
    Beispiel für die Integration in die bestehende Rideto-App.
    """
    from fastapi import FastAPI
    from backend.app.config import settings
    from backend.database.base import get_db

    app = FastAPI()

    # Config-Objekt für fastapi_users_auth
    class AuthConfig:
        SECRET_KEY = settings.SECRET_KEY
        ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    auth_config = AuthConfig()

    # fastapi_users_auth Modul integrieren
    auth_module = UserAuthModule()

    # Session-Dependency
    def get_session():
        return next(get_db())

    auth_module.init_app(app, get_session(), auth_config)

    return app


if __name__ == "__main__":
    # Beispiel-Anwendung starten
    import uvicorn

    app = create_app_with_auth(
        database_url="sqlite:///./test.db",
        secret_key="your-secret-key-here"
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
