"""
OAuth Auth Service - OAuth-basierte Authentifizierung.

Diese Klasse implementiert die Authentifizierung über OAuth-Provider wie Google, GitHub, etc.
Sie erbt von BaseAuthService und stellt eine konkrete Implementierung für
OAuth-basierte Authentifizierung bereit.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
import httpx
import json

from ..models.user_models import User, UserRegister
from ..models.auth_models import TokenData
from ..utils.security import SecurityUtils
from ..utils.token_utils import TokenUtils
from .base_auth_service import BaseAuthService
from .user_service import DatabaseUserService


class OAuthAuthService(BaseAuthService):
    """
    OAuth-basierte Implementierung des AuthService.

    Diese Klasse behandelt Authentifizierung über externe OAuth-Provider
    wie Google, GitHub, Microsoft, etc.
    """

    def __init__(self, user_service: DatabaseUserService, config, oauth_config: Dict[str, Any]):
        """
        Initialisiert den OAuthAuthService.

        Args:
            user_service: UserService für Benutzerverwaltung
            config: Allgemeine Konfiguration
            oauth_config: OAuth-spezifische Konfiguration mit Provider-Details
        """
        provider_name = oauth_config.get("provider", "oauth")
        super().__init__(config, f"oauth_{provider_name}")

        self.user_service = user_service
        self.oauth_config = oauth_config
        self.security = SecurityUtils()
        self.token_utils = TokenUtils(config.SECRET_KEY)

        # OAuth Provider Konfiguration
        self.client_id = oauth_config["client_id"]
        self.client_secret = oauth_config["client_secret"]
        self.redirect_uri = oauth_config["redirect_uri"]
        self.auth_url = oauth_config["auth_url"]
        self.token_url = oauth_config["token_url"]
        self.user_info_url = oauth_config["user_info_url"]
        self.scope = oauth_config.get("scope", "openid email profile")

    def get_supported_credentials_types(self) -> list[str]:
        """
        Gibt unterstützte Anmeldedaten-Typen zurück.

        Returns:
            Liste der unterstützten Credential-Typen
        """
        return ["oauth_code", "oauth_token"]

    def get_login_url(self, redirect_uri: Optional[str] = None) -> Optional[str]:
        """
        Gibt die Login-URL für den OAuth-Provider zurück.

        Args:
            redirect_uri: Optionale Redirect-URI

        Returns:
            Login-URL für OAuth-Provider
        """
        redirect = redirect_uri or self.redirect_uri

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect,
            "scope": self.scope,
            "response_type": "code",
            "state": self.security.generate_random_string(32)  # CSRF-Schutz
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"

    def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[User]:
        """
        Authentifiziert einen Benutzer über OAuth.

        Args:
            credentials: Dictionary mit {"code": str, "state": str} oder {"access_token": str}

        Returns:
            User-Objekt wenn authentifiziert, None andernfalls
        """
        if "code" in credentials:
            return self._authenticate_with_code(credentials["code"])
        elif "access_token" in credentials:
            return self._authenticate_with_token(credentials["access_token"])
        else:
            return None

    def _authenticate_with_code(self, auth_code: str) -> Optional[User]:
        """
        Authentifiziert mit OAuth Authorization Code.

        Args:
            auth_code: Authorization Code vom OAuth-Provider

        Returns:
            User-Objekt wenn authentifiziert, None andernfalls
        """
        try:
            # Access Token vom Provider holen
            token_data = self._exchange_code_for_token(auth_code)
            if not token_data:
                return None

            # Benutzerinformationen vom Provider holen
            user_info = self._get_user_info(token_data["access_token"])
            if not user_info:
                return None

            # Benutzer in lokaler Datenbank finden oder erstellen
            return self._get_or_create_user(user_info, token_data)

        except Exception as e:
            # Logging würde hier implementiert werden
            return None

    def _authenticate_with_token(self, access_token: str) -> Optional[User]:
        """
        Authentifiziert mit OAuth Access Token.

        Args:
            access_token: Access Token vom OAuth-Provider

        Returns:
            User-Objekt wenn authentifiziert, None andernfalls
        """
        try:
            # Benutzerinformationen vom Provider holen
            user_info = self._get_user_info(access_token)
            if not user_info:
                return None

            # Benutzer in lokaler Datenbank finden oder erstellen
            return self._get_or_create_user(user_info, {"access_token": access_token})

        except Exception as e:
            return None

    def _exchange_code_for_token(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """
        Tauscht Authorization Code gegen Access Token.

        Args:
            auth_code: Authorization Code

        Returns:
            Token-Daten vom Provider
        """
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }

            with httpx.Client() as client:
                response = client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            return None

    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Holt Benutzerinformationen vom OAuth-Provider.

        Args:
            access_token: Access Token

        Returns:
            Benutzerinformationen vom Provider
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            with httpx.Client() as client:
                response = client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            return None

    def _get_or_create_user(self, user_info: Dict[str, Any], token_data: Dict[str, Any]) -> Optional[User]:
        """
        Findet oder erstellt einen Benutzer basierend auf OAuth-Informationen.

        Args:
            user_info: Benutzerinformationen vom Provider
            token_data: Token-Daten vom Provider

        Returns:
            User-Objekt
        """
        provider_id = str(user_info.get("id") or user_info.get("sub"))
        email = user_info.get("email")

        if not provider_id or not email:
            return None

        # Erst nach externer ID suchen
        user = self.user_service.get_user_by_external_id(provider_id, self.provider_name)

        if not user:
            # Nach E-Mail suchen
            user = self.user_service.get_user_by_email(email)

            if user:
                # Bestehenden Benutzer mit OAuth-Account verknüpfen
                self.user_service.link_external_account(
                    user.id,
                    provider_id,
                    self.provider_name,
                    {
                        "user_info": user_info,
                        "access_token": token_data.get("access_token"),
                        "refresh_token": token_data.get("refresh_token")
                    }
                )
            else:
                # Neuen Benutzer erstellen
                user = self._create_user_from_oauth(user_info, provider_id, token_data)

        return user

    def _create_user_from_oauth(self, user_info: Dict[str, Any], provider_id: str, token_data: Dict[str, Any]) -> Optional[User]:
        """
        Erstellt einen neuen Benutzer aus OAuth-Informationen.

        Args:
            user_info: Benutzerinformationen vom Provider
            provider_id: Provider-spezifische Benutzer-ID
            token_data: Token-Daten

        Returns:
            Erstellter Benutzer
        """
        try:
            from ..models.user_models import UserCreate

            # Zufälliges Passwort generieren (wird nicht verwendet)
            random_password = self.security.generate_random_string(32)

            user_create = UserCreate(
                email=user_info["email"],
                password=random_password,
                full_name=user_info.get("name", user_info.get("email", "")),
                is_active=True,
                is_superuser=False
            )

            user = self.user_service.create_user(user_create)

            # OAuth-Account verknüpfen
            self.user_service.link_external_account(
                user.id,
                provider_id,
                self.provider_name,
                {
                    "user_info": user_info,
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token")
                }
            )

            return user

        except Exception as e:
            return None

    def login(self, credentials: Dict[str, Any]) -> Optional[TokenData]:
        """
        Führt OAuth-Login durch und gibt Token-Daten zurück.

        Args:
            credentials: OAuth-Anmeldedaten

        Returns:
            TokenData wenn erfolgreich, None bei Fehlschlag
        """
        user = self.authenticate_user(credentials)
        if not user or not user.is_active:
            return None

        # Access Token erstellen
        access_token_expires = timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.token_utils.create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            additional_claims={
                "email": user.email,
                "is_superuser": user.is_superuser,
                "provider": self.provider_name
            }
        )

        return TokenData(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user_id=user.id,
            email=user.email,
            is_superuser=user.is_superuser
        )

    def supports_registration(self) -> bool:
        """
        OAuth-Provider unterstützen automatische Registrierung.

        Returns:
            True
        """
        return True

    def register_user(self, user_register: UserRegister) -> Optional[User]:
        """
        OAuth-Provider verwenden normalerweise automatische Registrierung.

        Args:
            user_register: Registrierungsdaten (nicht verwendet)

        Returns:
            None (nicht unterstützt)
        """
        return None  # OAuth macht automatische Registrierung

    def get_current_user(self, token: str) -> Optional[User]:
        """
        Holt den aktuellen Benutzer anhand des Tokens.

        Args:
            token: JWT-Access-Token

        Returns:
            User-Objekt wenn Token gültig, None andernfalls
        """
        token_data = self.token_utils.verify_token(token)
        if not token_data or not token_data.sub:
            return None

        try:
            user_id = UUID(token_data.sub)
            return self.user_service.get_user_by_id(user_id)
        except ValueError:
            return None

    def create_password_reset_token(self, identifier: str) -> Optional[str]:
        """
        OAuth-Provider unterstützen normalerweise kein Passwort-Reset.

        Args:
            identifier: Benutzer-Identifikator

        Returns:
            None (nicht unterstützt)
        """
        return None

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        OAuth-Provider unterstützen normalerweise kein Passwort-Reset.

        Args:
            token: Reset-Token
            new_password: Neues Passwort

        Returns:
            False (nicht unterstützt)
        """
        return False

    def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Erneuert einen Access-Token.

        Args:
            refresh_token: Der Refresh-Token

        Returns:
            Neue TokenData wenn gültig
        """
        token_data = self.token_utils.verify_token(refresh_token)
        if not token_data or not token_data.sub:
            return None

        try:
            user_id = UUID(token_data.sub)
            user = self.user_service.get_user_by_id(user_id)

            if not user or not user.is_active:
                return None

            # Neuen Access-Token erstellen
            access_token_expires = timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.token_utils.create_access_token(
                subject=str(user.id),
                expires_delta=access_token_expires,
                additional_claims={
                    "email": user.email,
                    "is_superuser": user.is_superuser,
                    "provider": self.provider_name
                }
            )

            return TokenData(
                access_token=access_token,
                token_type="bearer",
                expires_in=int(access_token_expires.total_seconds()),
                user_id=user.id,
                email=user.email,
                is_superuser=user.is_superuser
            )

        except ValueError:
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Widerruft einen Token.

        Args:
            token: Der zu widerrufende Token

        Returns:
            True wenn erfolgreich
        """
        # TODO: Implementierung einer Token-Blacklist
        return True

    def is_token_valid(self, token: str) -> bool:
        """
        Prüft Token-Gültigkeit.

        Args:
            token: Der zu prüfende Token

        Returns:
            True wenn gültig
        """
        token_data = self.token_utils.verify_token(token)
        return token_data is not None
