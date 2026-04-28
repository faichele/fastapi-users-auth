# fastapi_users_auth/dependencies/web_auth_deps.py
from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth_provider import AuthProvider


_security = HTTPBearer(auto_error=False)


def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
):
    """
    Optionaler User:
    - akzeptiert `Authorization: Bearer <token>` ODER Cookie `access_token`
    - kein/ungültiger Token => `None`
    - nutzt zentral `AuthProvider` (muss via `AuthProvider.initialize(...)` initialisiert sein)
    """
    token: Optional[str] = None

    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    else:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            token = cookie_token.replace("Bearer ", "", 1) if cookie_token.startswith("Bearer ") else cookie_token

    if not token:
        return None

    if not AuthProvider.is_initialized():
        return None

    try:
        auth_deps = AuthProvider.get_instance()
        user = auth_deps.auth_service.get_current_user(token)
        if not user or not getattr(user, "is_active", True):
            return None
        return user
    except Exception:
        return None


async def get_mandatory_current_user(
    request: Request,
    current_user: object | None = Depends(get_optional_current_user),
) -> object:
    """
    Mandatory User:
    - HTML\-Navigation => Redirect auf `/login?next=<url>`
    - API/JSON/AJAX => `403 Forbidden`
    """
    if current_user is not None:
        return current_user

    accept = (request.headers.get("accept") or "").lower()
    xrw = (request.headers.get("x-requested-with") or "").lower()
    wants_html = "text/html" in accept
    is_ajax = xrw == "xmlhttprequest"

    if wants_html and not is_ajax:
        next_url = str(request.url)
        qs = urlencode({"next": next_url})
        return RedirectResponse(url=f"/login?{qs}", status_code=status.HTTP_303_SEE_OTHER)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def auth_or_redirect(
    request: Request,
    login_path: str = "/login",
) -> RedirectResponse:
    """
    Kleine Helper\-Funktion für HTML\-Handler (wenn man explizit redirecten will).
    """
    next_url = str(request.url)
    qs = urlencode({"next": next_url})
    return RedirectResponse(
        url=f"{login_path}?{qs}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
