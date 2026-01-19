"""
Authentication Router für das fastapi_users_auth Modul.

Dieser Router behandelt alle authentifizierungsbezogenen Endpunkte:
- Login/Logout
- Token-Refresh
- Passwort-Reset
- Benutzerregistrierung
"""

from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..models.auth_models import Token, TokenData, NewPassword, NewPasswordRequest, Message, LoginResponse
from ..models.user_models import UserRegister, UserPublic
from ..services.auth_service import AuthService
from ..dependencies.auth_deps import (
    AuthDependencies,
    get_current_user as get_current_user_provider,
    get_current_active_user as get_current_active_user_provider,
)


class AuthRouter:
    """
    Router-Klasse für Authentifizierungs-Endpunkte.

    Diese Klasse kapselt alle authentifizierungsbezogenen FastAPI-Routen
    und stellt eine saubere API für Client-Anwendungen bereit.
    """

    def __init__(self, auth_service: AuthService, auth_deps: AuthDependencies, prefix: str = "/auth"):
        """
        Initialisiert den AuthRouter.

        Args:
            auth_service: AuthService-Instanz
            auth_deps: AuthDependencies-Instanz
            prefix: URL-Prefix für alle Routen (Standard: "/auth")
        """
        self.auth_service = auth_service
        self.auth_deps = auth_deps
        self.router = APIRouter(prefix=prefix, tags=["authentication"])

        # Dependencies instanziieren
        self.get_current_user_dep = get_current_user_provider(auth_deps)
        self.get_current_active_user_dep = get_current_active_user_provider(auth_deps)

        self._setup_routes()

    def _setup_routes(self):
        """Konfiguriert alle Routen für den Router."""

        @self.router.post("/login", response_model=TokenData)
        def login(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
        ) -> TokenData:
            """
            OAuth2-kompatible Token-Anmeldung.

            Authentifiziert einen Benutzer mit E-Mail und Passwort
            und gibt einen JWT-Access-Token zurück.
            """
            credentials = {"email": form_data.username, "password": form_data.password}
            token_data = self.auth_service.login(credentials)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token_data

        @self.router.post("/login/test-token", response_model=UserPublic)
        def test_token(
            current_user: Annotated[Any, Depends(self.get_current_user_dep)]
        ) -> Any:
            """
            Testet die Gültigkeit eines Access-Tokens.

            Gibt die Benutzerinformationen für einen gültigen Token zurück.
            """
            return current_user

        @self.router.post("/register", response_model=UserPublic)
        def register(user_register: UserRegister) -> UserPublic:
            """
            Registriert einen neuen Benutzer.

            Erstellt ein neues Benutzerkonto mit den angegebenen Daten.
            """
            try:
                user = self.auth_service.register_user(user_register)
                return UserPublic.model_validate(user)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.post("/password-reset/request", response_model=Message)
        def request_password_reset(reset_request: NewPasswordRequest) -> Message:
            """
            Fordert einen Passwort-Reset an.

            Sendet eine E-Mail mit einem Reset-Link an die angegebene Adresse,
            falls ein Konto mit dieser E-Mail existiert.
            """
            reset_token = self.auth_service.create_password_reset_token(reset_request.email)

            if reset_token:
                # TODO: E-Mail mit Reset-Link senden
                # In einer vollständigen Implementierung würde hier eine E-Mail gesendet
                message = f"Passwort-Reset angefordert für {reset_request.email}. Reset-Token: {reset_token}"
            else:
                # Aus Sicherheitsgründen immer die gleiche Nachricht zurückgeben
                message = "Falls ein Konto mit dieser E-Mail existiert, wurde eine Reset-E-Mail gesendet."

            return Message(message=message)

        @self.router.post("/password-reset/confirm", response_model=Message)
        def confirm_password_reset(reset_data: NewPassword) -> Message:
            """
            Bestätigt einen Passwort-Reset mit Token.

            Setzt das Passwort für einen Benutzer anhand eines gültigen Reset-Tokens zurück.
            """
            success = self.auth_service.reset_password(reset_data.token, reset_data.new_password)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )

            return Message(message="Passwort erfolgreich zurückgesetzt")

        @self.router.post("/refresh", response_model=Token)
        def refresh_token(
            refresh_token: str,
        ) -> Token:
            """
            Erneuert einen Access-Token mit einem Refresh-Token.

            Args:
                refresh_token: Der Refresh-Token

            Returns:
                Neuer Access-Token (+ optional neues Refresh-Token)
            """
            token_data = self.auth_service.refresh_token(refresh_token)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            # TokenData -> Token mappen (Token ist die schlanke Response)
            return Token(
                access_token=token_data.access_token,
                token_type=token_data.token_type,
                expires_in=token_data.expires_in,
                refresh_token=getattr(token_data, "refresh_token", None)
            )

        @self.router.post("/logout", response_model=Message)
        def logout(
            current_user: Annotated[Any, Depends(self.get_current_active_user_dep)],
            token: Annotated[str, Depends(self.auth_deps.get_token)]
        ) -> Message:
            """
            Meldet einen Benutzer ab.

            Widerruft den aktuellen Access-Token (in einer vollständigen
            Implementierung würde der Token zur Blacklist hinzugefügt).
            """
            success = self.auth_service.revoke_token(token)
            if success:
                return Message(message="Successfully logged out")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not revoke token"
                )

        @self.router.get("/me", response_model=UserPublic)
        def get_current_user_info(
            current_user: Annotated[Any, Depends(self.get_current_active_user_dep)]
        ) -> Any:
            """
            Holt die Informationen des aktuell angemeldeten Benutzers.

            Returns:
                Öffentliche Benutzerinformationen
            """
            return current_user

        @self.router.get("/permissions")
        def get_current_user_permissions(
            current_user: Annotated[Any, Depends(self.get_current_active_user_dep)]
        ) -> dict[str, Any]:
            """
            Holt die Berechtigungen des aktuell angemeldeten Benutzers.

            Returns:
                Dictionary mit Benutzerinformationen und Berechtigungen
            """
            permissions = self.auth_service.get_user_permissions(current_user)
            return {
                "user_id": str(current_user.id),
                "email": current_user.email,
                "is_active": current_user.is_active,
                "is_superuser": current_user.is_superuser,
                "permissions": permissions
            }


def create_auth_router(
    auth_service: AuthService,
    auth_deps: AuthDependencies,
    prefix: str = "/auth"
) -> APIRouter:
    """
    Factory-Funktion zur Erstellung eines Authentifizierungs-Routers.

    Args:
        auth_service: AuthService-Instanz
        auth_deps: AuthDependencies-Instanz
        prefix: URL-Prefix für Routen

    Returns:
        Konfigurierter APIRouter
    """
    auth_router = AuthRouter(auth_service, auth_deps, prefix)
    return auth_router.router
