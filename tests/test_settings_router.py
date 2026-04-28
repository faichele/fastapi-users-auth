from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import RedirectResponse

from fastapi_users_auth.routers.settings_router import create_auth_settings_router


class DummyUser:
    def __init__(self, email: str = "admin@example.com", is_superuser: bool = True):
        self.email = email
        self.is_superuser = is_superuser


def superuser_or_redirect_ok():
    return DummyUser()


def superuser_or_redirect_redirect():
    return RedirectResponse(url="/login")


def test_settings_page_renders_html(tmp_path):
    app = FastAPI()

    # Wichtig: Templates müssen existieren; wir verwenden das package-template.
    templates_dir = "packages/fastapi_users_auth/templates"

    app.include_router(
        create_auth_settings_router(
            templates_dir=templates_dir,
            api_prefix="/api",
            auth_prefix="/api/auth",
            settings_prefix="/api/auth/settings",
            superuser_or_redirect=superuser_or_redirect_ok,
        )
    )

    client = TestClient(app)
    resp = client.get("/api/auth/settings")
    assert resp.status_code == 200
    assert "Auth Einstellungen" in resp.text


def test_settings_data_requires_auth(tmp_path):
    app = FastAPI()

    templates_dir = "packages/fastapi_users_auth/templates"

    app.include_router(
        create_auth_settings_router(
            templates_dir=templates_dir,
            api_prefix="/api",
            auth_prefix="/api/auth",
            settings_prefix="/api/auth/settings",
            superuser_or_redirect=superuser_or_redirect_redirect,
        )
    )

    client = TestClient(app)
    resp = client.get("/api/auth/settings/data")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("error") == "not_authenticated"
