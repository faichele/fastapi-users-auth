"""Regressionstests: späte Auflösung der User-ORM-Klasse im UserService.

Hintergrund: ``from ..models.user_models import User`` bindet zur Importzeit.
Wird ein Konsument-Modul (z. B. über die Dependency-Kette der Anwendung)
importiert, BEVOR ``configure_auth_models()`` die Modelle patcht, bleibt das
lokale Binding für immer ``None``. Der DatabaseUserService muss die Klasse
deshalb über ``get_user_model()`` zum Aufrufzeitpunkt auflösen.
"""

from datetime import datetime, timezone
from pathlib import Path
from importlib import import_module

import sys
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

repo_root = Path(__file__).resolve().parents[3]
packages_root = repo_root / "packages"
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(packages_root))

fastapi_users_auth = import_module("packages.fastapi_users_auth")
create_auth_models = fastapi_users_auth.create_auth_models
configure_auth_models = fastapi_users_auth.configure_auth_models
user_models = import_module("packages.fastapi_users_auth.models.user_models")
user_service_module = import_module("packages.fastapi_users_auth.services.user_service")

SharedBase = import_module("packages.fastapi_shared_orm").Base


def test_get_user_model_raises_helpful_error_when_unconfigured():
    original_user = user_models.User
    try:
        user_models.User = None
        with pytest.raises(RuntimeError, match="configure_auth_models"):
            user_models.get_user_model()
    finally:
        user_models.User = original_user


def test_user_service_works_despite_stale_import_binding():
    """Simuliert: user_service wurde vor configure_auth_models() importiert.

    Vor dem Fix schlug get_user_by_email mit
    ``AttributeError: 'NoneType' object has no attribute 'email'`` fehl,
    weil das Modul-Binding ``user_service.User`` None blieb.
    """
    TestBase = declarative_base()
    default_models = create_auth_models(SharedBase)
    stale_binding = user_service_module.User

    try:
        configure_auth_models(TestBase, table_prefix="stale_")

        # Stale-Situation erzwingen: Import-Binding im Konsumenten-Modul ist None
        user_service_module.User = None

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
        user_service_module.User = stale_binding
        configure_auth_models(SharedBase, table_prefix=default_models.table_prefix)
