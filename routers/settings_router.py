"""fastapi_users_auth Settings UI.

Dieses Modul stellt eine kleine Jinja2-basierte Seite bereit, die (analog zum
Admin-Template im fastapi_users_admin Paket) die wichtigsten Informationen
zur Auth-Router/Provider-Konfiguration sichtbar macht.

Wichtig: Diese UI ist bewusst read-only.
- Es werden keine Secrets angezeigt.
- Persistente Änderungen an Auth-Konfiguration sind stark app-spezifisch
  (ENV, Settings-Store, Vault, etc.) und deshalb hier nicht implementiert.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..dependencies.multi_provider_auth_deps import MultiProviderAuthDependencies
from ..services.auth_service import AuthService
from ..services.auth_service_manager import AuthServiceManager


def _safe_bool(val: Any) -> bool:
    return bool(val)


class AuthSettingsRouter:
    def __init__(
        self,
        *,
        templates_dir: str,
        api_prefix: str = "/api",
        auth_prefix: str = "/api/auth",
        settings_prefix: str = "/api/auth/settings",
        auth_service: AuthService | None = None,
        auth_manager: AuthServiceManager | None = None,
        auth_deps: MultiProviderAuthDependencies | None = None,
        superuser_or_redirect: Callable[..., Any] | None = None,
    ):
        self.templates = Jinja2Templates(directory=templates_dir)

        self.api_prefix = api_prefix
        self.auth_prefix = auth_prefix
        self.settings_prefix = settings_prefix

        self.auth_service = auth_service
        self.auth_manager = auth_manager
        self.auth_deps = auth_deps

        self.superuser_or_redirect = superuser_or_redirect

        self.router = APIRouter(prefix=self.settings_prefix, tags=["auth-settings"])
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.get("", response_class=HTMLResponse)
        async def settings_page(
            request: Request,
            current_user=Depends(self.superuser_or_redirect),
        ):
            if isinstance(current_user, RedirectResponse):
                return current_user

            return self.templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "title": "Auth Einstellungen",
                    "user": current_user,
                    "api_prefix": self.api_prefix,
                },
            )

        @self.router.get("/data")
        async def settings_data(
            current_user=Depends(self.superuser_or_redirect),
        ) -> dict[str, Any]:
            # Für JSON-Endpunkt reicht es, Superuser zu erzwingen.
            if isinstance(current_user, RedirectResponse):
                # HTML redirect ist für API call unpraktisch; wir liefern eine klare Fehlermeldung.
                return {
                    "error": "not_authenticated",
                    "detail": "Authentication required",
                }

            mode = "single-provider" if self.auth_service is not None else "multi-provider"

            providers = []
            if self.auth_manager is not None:
                providers = self.auth_manager.list_auth_providers()

            cfg_obj = None
            if self.auth_service is not None:
                cfg_obj = getattr(self.auth_service, "config", None)
            elif self.auth_manager is not None:
                cfg_obj = None

            def cfg_get(key: str, default: Any = None) -> Any:
                if cfg_obj is None:
                    return default
                return getattr(cfg_obj, key, default)

            access_exp = cfg_get("ACCESS_TOKEN_EXPIRE_MINUTES")
            refresh_exp = cfg_get("REFRESH_TOKEN_EXPIRE_DAYS")
            secret = cfg_get("SECRET_KEY")

            return {
                "mode": mode,
                "router": {
                    "auth_prefix": self.auth_prefix,
                    "settings_prefix": self.settings_prefix,
                },
                "config": {
                    "ACCESS_TOKEN_EXPIRE_MINUTES": access_exp,
                    "REFRESH_TOKEN_EXPIRE_DAYS": refresh_exp,
                    "SECRET_KEY_SET": _safe_bool(secret),
                },
                "providers": providers,
                "links": {
                    "providers_url": "{}/providers".format(self.auth_prefix),
                    "stats_url": "{}/stats".format(self.auth_prefix),
                },
            }


def create_auth_settings_router(
    *,
    templates_dir: str,
    api_prefix: str = "/api",
    auth_prefix: str = "/api/auth",
    settings_prefix: str = "/api/auth/settings",
    auth_service: AuthService | None = None,
    auth_manager: AuthServiceManager | None = None,
    auth_deps: MultiProviderAuthDependencies | None = None,
    superuser_or_redirect: Callable[..., Any] | None = None,
) -> APIRouter:
    """Factory für den Settings-Router.

    Contract:
    - templates_dir muss ein Verzeichnis sein, das `settings.html` enthält.
    - superuser_or_redirect muss eine Dependency sein, die für HTML entweder
      den User oder eine RedirectResponse zurückgibt.
    """
    if superuser_or_redirect is None:
        raise ValueError("superuser_or_redirect muss gesetzt sein (für HTML-Auth + Redirect)")

    router = AuthSettingsRouter(
        templates_dir=templates_dir,
        api_prefix=api_prefix,
        auth_prefix=auth_prefix,
        settings_prefix=settings_prefix,
        auth_service=auth_service,
        auth_manager=auth_manager,
        auth_deps=auth_deps,
        superuser_or_redirect=superuser_or_redirect,
    )
    return router.router
