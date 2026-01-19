"""
Erweiterter Authentication Router mit Multi-Provider-Unterstützung.

Dieser Router behandelt alle authentifizierungsbezogenen Endpunkte mit
Unterstützung für verschiedene Authentifizierungsanbieter.
"""

from datetime import timedelta
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from ..models.auth_models import (
    Token, TokenData, NewPassword, NewPasswordRequest, Message, LoginResponse
)
from ..models.user_models import UserRegister, UserPublic
from ..services.auth_service_manager import AuthServiceManager
from ..services.base_user_service import BaseUserService
from ..dependencies.multi_provider_auth_deps import MultiProviderAuthDependencies


class MultiProviderAuthRouter:
    """
    Erweiterter Router für Multi-Provider-Authentifizierung.

    Dieser Router behandelt Authentifizierung über verschiedene Provider
    und stellt entsprechende Endpunkte bereit.
    """

    def __init__(
        self,
        auth_manager: AuthServiceManager,
        user_service: BaseUserService,
        auth_deps: MultiProviderAuthDependencies,
        prefix: str = "/auth"
    ):
        """
        Initialisiert den MultiProviderAuthRouter.

        Args:
            auth_manager: AuthServiceManager-Instanz
            user_service: UserService-Instanz
            auth_deps: AuthDependencies-Instanz
            prefix: URL-Prefix für alle Routen (Standard: "/auth")
        """
        self.auth_manager = auth_manager
        self.user_service = user_service
        self.auth_deps = auth_deps
        self.router = APIRouter(prefix=prefix, tags=["multi-provider-authentication"])
        self._setup_routes()

    def _setup_routes(self):
        """Konfiguriert alle Routen für den Router."""

        @self.router.get("/providers", response_model=list[dict])
        def list_auth_providers() -> list[dict]:
            """
            Listet alle verfügbaren Authentifizierungsanbieter auf.

            Returns:
                Liste der verfügbaren Auth-Provider mit Details
            """
            return self.auth_manager.list_auth_providers()

        @self.router.get("/providers/{provider_name}/login-url")
        def get_provider_login_url(
            provider_name: str,
            redirect_uri: Optional[str] = Query(None, description="Optional redirect URI")
        ) -> dict[str, Optional[str]]:
            """
            Holt die Login-URL für einen externen Provider.

            Args:
                provider_name: Name des Auth-Providers
                redirect_uri: Optionale Redirect-URI

            Returns:
                Dictionary mit Login-URL
            """
            provider = self.auth_manager.get_auth_provider(provider_name)
            if not provider:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Auth provider not found"
                )

            login_url = provider.get_login_url(redirect_uri)
            return {"login_url": login_url}

        @self.router.post("/login", response_model=TokenData)
        def login(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
            provider_name: Optional[str] = Query(None, description="Specific auth provider to use")
        ) -> TokenData:
            """
            Meldet einen Benutzer an (Standard E-Mail/Passwort).

            Args:
                form_data: Login-Formulardaten
                provider_name: Optionaler spezifischer Auth-Provider

            Returns:
                Token-Daten bei erfolgreichem Login
            """
            credentials = {
                "email": form_data.username,  # OAuth2PasswordRequestForm verwendet 'username'
                "password": form_data.password
            }

            token_data = self.auth_manager.login(credentials, provider_name)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return token_data

        @self.router.post("/login/{provider_name}", response_model=TokenData)
        def login_with_provider(
            provider_name: str,
            credentials: dict[str, Any]
        ) -> TokenData:
            """
            Meldet einen Benutzer mit einem spezifischen Provider an.

            Args:
                provider_name: Name des Auth-Providers
                credentials: Provider-spezifische Anmeldedaten

            Returns:
                Token-Daten bei erfolgreichem Login
            """
            token_data = self.auth_manager.login(credentials, provider_name)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return token_data

        @self.router.post("/oauth/callback/{provider_name}", response_model=TokenData)
        def oauth_callback(
            provider_name: str,
            code: str = Query(..., description="OAuth authorization code"),
            state: Optional[str] = Query(None, description="OAuth state parameter")
        ) -> TokenData:
            """
            OAuth-Callback-Endpunkt für externe Provider.

            Args:
                provider_name: Name des OAuth-Providers
                code: Authorization Code vom Provider
                state: State-Parameter für CSRF-Schutz

            Returns:
                Token-Daten bei erfolgreichem Login
            """
            credentials = {"code": code}
            if state:
                credentials["state"] = state

            token_data = self.auth_manager.login(credentials, f"oauth_{provider_name}")
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="OAuth authentication failed"
                )

            return token_data

        @self.router.post("/register", response_model=UserPublic)
        def register(
            user_register: UserRegister,
            provider_name: Optional[str] = Query(None, description="Specific auth provider for registration")
        ) -> UserPublic:
            """
            Registriert einen neuen Benutzer.

            Args:
                user_register: Registrierungsdaten
                provider_name: Optionaler spezifischer Provider

            Returns:
                Der erstellte Benutzer
            """
            try:
                user = self.auth_manager.register_user(user_register, provider_name)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Registration not supported by any available provider"
                    )
                return UserPublic.model_validate(user)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.post("/logout", response_model=Message)
        def logout(
            token: Annotated[str, Depends(self.auth_deps.get_token)],
            provider_name: Optional[str] = Query(None, description="Specific auth provider")
        ) -> Message:
            """
            Meldet einen Benutzer ab.

            Args:
                token: Access-Token
                provider_name: Optionaler spezifischer Provider

            Returns:
                Bestätigungsnachricht
            """
            success = self.auth_manager.revoke_token(token, provider_name)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Logout failed"
                )

            return Message(message="Successfully logged out")

        @self.router.post("/refresh", response_model=TokenData)
        def refresh_token(
            refresh_token: str,
            provider_name: Optional[str] = Query(None, description="Specific auth provider")
        ) -> TokenData:
            """
            Erneuert einen Access-Token.

            Args:
                refresh_token: Refresh-Token
                provider_name: Optionaler spezifischer Provider

            Returns:
                Neue Token-Daten
            """
            token_data = self.auth_manager.refresh_token(refresh_token, provider_name)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            return token_data

        @self.router.post("/password-reset/request", response_model=Message)
        def request_password_reset(
            email: str,
            provider_name: Optional[str] = Query(None, description="Specific auth provider")
        ) -> Message:
            """
            Fordert einen Passwort-Reset-Token an.

            Args:
                email: E-Mail-Adresse des Benutzers
                provider_name: Optionaler spezifischer Provider

            Returns:
                Bestätigungsnachricht
            """
            reset_token = self.auth_manager.create_password_reset_token(email, provider_name)
            if not reset_token:
                # Aus Sicherheitsgründen immer Erfolg melden
                pass

            return Message(
                message="If the email exists, a password reset link has been sent"
            )

        @self.router.post("/password-reset/confirm", response_model=Message)
        def confirm_password_reset(
            password_reset: NewPasswordRequest,
            provider_name: Optional[str] = Query(None, description="Specific auth provider")
        ) -> Message:
            """
            Bestätigt Passwort-Reset mit Token.

            Args:
                password_reset: Reset-Token und neues Passwort
                provider_name: Optionaler spezifischer Provider

            Returns:
                Bestätigungsnachricht
            """
            success = self.auth_manager.reset_password(
                password_reset.token,
                password_reset.new_password,
                provider_name
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )

            return Message(message="Password has been reset successfully")

        @self.router.get("/validate-token", response_model=dict[str, bool])
        def validate_token(
            token: Annotated[str, Depends(self.auth_deps.get_token)],
            provider_name: Optional[str] = Query(None, description="Specific auth provider")
        ) -> dict[str, bool]:
            """
            Validiert einen Token.

            Args:
                token: Der zu validierende Token
                provider_name: Optionaler spezifischer Provider

            Returns:
                Validierungsergebnis
            """
            is_valid = self.auth_manager.is_token_valid(token, provider_name)
            return {"valid": is_valid}

        @self.router.get("/me", response_model=UserPublic)
        def get_current_user_info(
            current_user: Annotated[User, Depends(self.auth_deps.get_current_active_user)]
        ) -> UserPublic:
            """
            Holt Informationen über den aktuellen Benutzer.

            Args:
                current_user: Aktueller Benutzer

            Returns:
                Benutzerinformationen
            """
            return UserPublic.model_validate(current_user)

        @self.router.get("/me/permissions", response_model=dict[str, list[str]])
        def get_current_user_permissions(
            current_user: Annotated[User, Depends(self.auth_deps.get_current_active_user)],
            provider_name: Optional[str] = Query(None, description="Specific auth provider")
        ) -> dict[str, list[str]]:
            """
            Holt die Berechtigungen des aktuellen Benutzers.

            Args:
                current_user: Aktueller Benutzer
                provider_name: Optionaler spezifischer Provider

            Returns:
                Berechtigungen des Benutzers
            """
            permissions = self.auth_manager.get_user_permissions(current_user, provider_name)
            return {"permissions": permissions}

        @self.router.get("/stats", response_model=dict[str, Any])
        def get_auth_stats(
            current_user: Annotated[User, Depends(self.auth_deps.get_current_active_superuser)]
        ) -> dict[str, Any]:
            """
            Holt Statistiken über die Auth-Provider (nur Superuser).

            Args:
                current_user: Aktueller Superuser

            Returns:
                Auth-Provider-Statistiken
            """
            return self.auth_manager.get_stats()


def create_multi_provider_auth_router(
    auth_manager: AuthServiceManager,
    user_service: BaseUserService,
    auth_deps: MultiProviderAuthDependencies,
    prefix: str = "/auth"
) -> APIRouter:
    """
    Factory-Funktion zur Erstellung eines Multi-Provider-Auth-Routers.

    Args:
        auth_manager: AuthServiceManager-Instanz
        user_service: UserService-Instanz
        auth_deps: AuthDependencies-Instanz
        prefix: URL-Prefix für Routen

    Returns:
        Konfigurierter APIRouter
    """
    auth_router = MultiProviderAuthRouter(auth_manager, user_service, auth_deps, prefix)
    return auth_router.router
