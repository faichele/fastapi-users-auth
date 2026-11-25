"""Regressionstests: späte Auflösung der User-ORM-Klasse im UserService.

Hintergrund: ``from ..models.user_models import User`` bindet zur Importzeit.
Wird ein Konsument-Modul (z. B. über die Dependency-Kette der Anwendung)
importiert, BEVOR ``configure_auth_models()`` die Modelle patcht, bleibt das
lokale Binding für immer ``None``. Der DatabaseUserService muss die Klasse
deshalb über ``get_user_model()`` zum Aufrufzeitpunkt auflösen.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Annotated, Any
from uuid import uuid4

import pytest
import sqlalchemy as sa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from fastapi_users_auth import configure_auth_models, create_auth_models
from fastapi_users_auth.dependencies import (
    AuthProvider,
    CurrentActiveUserDep,
    CurrentSuperuserDep,
    CurrentUserDep,
)
from fastapi_users_auth.dependencies.auth_deps import (
    AuthDependencies,
    UserServiceDep,
    get_current_active_superuser,
)
from fastapi_users_auth.models import user_models
from fastapi_users_auth.services import user_service as user_service_module
from sqlalchemy.orm import declarative_base, sessionmaker


def test_get_user_model_raises_helpful_error_when_unconfigured():
    original_user = user_models.User
    try:
        user_models.User = None
        with pytest.raises(RuntimeError, match="configure_auth_models"):
            user_models.get_user_model()
    finally:
        user_models.User = original_user


def test_user_service_works_despite_stale_import_binding(monkeypatch):
    """Simuliert: user_service wurde vor configure_auth_models() importiert.

    Vor dem Fix schlug get_user_by_email mit
    ``AttributeError: 'NoneType' object has no attribute 'email'`` fehl,
    weil das Modul-Binding ``user_service.User`` None blieb.
    """
    TestBase = declarative_base()
    SharedBase = declarative_base()
    default_models = create_auth_models(SharedBase)

    try:
        configure_auth_models(TestBase, table_prefix="stale_")

        # Stale-Situation erzwingen: Import-Binding im Konsumenten-Modul ist None
        monkeypatch.setattr(user_service_module, "User", None, raising=False)

        engine = sa.create_engine("sqlite://")
        TestBase.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()

        try:
            service = user_service_module.DatabaseUserService(session)

            # Query-Pfade (schlugen vor dem Fix fehl)
            assert service.get_user_by_email("missing@example.com") is None
            assert service.is_email_available("missing@example.com") is True
            users, total = service.get_users()
            assert users == []
            assert total == 0

            # Konstruktor-Pfad
            created = service.create_user(
                user_models.UserCreate(
                    id=uuid4(),
                    created_at=datetime.now(timezone.utc),
                    email="lazy@example.com",
                    password="supersecret",
                    full_name="Lazy Binding",
                    is_active=True,
                    is_superuser=False,
                )
            )
            assert created.email == "lazy@example.com"

            # ID-Normalisierung (User.id.type) + Lookup über die ID
            fetched = service.get_user_by_id(str(created.id))
            assert fetched is not None
            assert fetched.id == created.id
        finally:
            session.close()
            engine.dispose()
    finally:
        configure_auth_models(SharedBase, table_prefix=default_models.table_prefix)


def test_dependency_factory_uses_configured_model_and_enforces_access():
    models = configure_auth_models(declarative_base(), table_prefix="access_")
    user = models.User(is_active=True, is_superuser=True)
    auth_service = SimpleNamespace(get_current_user=lambda token: user)
    deps = AuthDependencies(auth_service, None)
    app = FastAPI()

    @app.get("/protected")
    def protected(current_user: Annotated[Any, Depends(get_current_active_superuser(deps))]):
        return {"active": current_user.is_active}

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {uuid4()}"}
    assert client.get("/protected").status_code == 401
    assert client.get("/protected", headers=headers).status_code == 200
    user.is_superuser = False
    assert client.get("/protected", headers=headers).status_code == 403
    user.is_active = False
    assert client.get("/protected", headers=headers).status_code == 400


def test_public_dependency_aliases_use_initialized_provider(monkeypatch):
    models = configure_auth_models(declarative_base(), table_prefix="aliases_")
    user = models.User(is_active=True, is_superuser=True)
    token = str(uuid4())
    auth_service = SimpleNamespace(get_current_user=lambda value: user if value == token else None)
    user_service = SimpleNamespace()
    deps = AuthDependencies(auth_service, user_service)
    monkeypatch.setattr(AuthProvider, "_initialized", False)
    monkeypatch.setattr(AuthProvider, "_instance", None)
    app = FastAPI()

    @app.get("/user")
    def current(current_user: CurrentUserDep):
        return {"active": current_user.is_active}

    @app.get("/active")
    def active(current_user: CurrentActiveUserDep):
        return {"active": current_user.is_active}

    @app.get("/admin")
    def admin(current_user: CurrentSuperuserDep):
        return {"admin": current_user.is_superuser}

    @app.get("/service")
    def service(current_service: UserServiceDep):
        return {"matches": current_service is user_service}

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/user", headers=headers).status_code == 500
    AuthProvider.initialize(deps)
    assert client.get("/user").status_code == 401
    assert client.get("/user", headers={"Authorization": f"Bearer {uuid4()}"}).status_code == 401
    assert client.get("/user", headers=headers).json() == {"active": True}
    assert client.get("/active", headers=headers).status_code == 200
    assert client.get("/admin", headers=headers).status_code == 200
    assert client.get("/service").json() == {"matches": True}
    user.is_superuser = False
    assert client.get("/admin", headers=headers).status_code == 403
    user.is_active = False
    assert client.get("/active", headers=headers).status_code == 400
