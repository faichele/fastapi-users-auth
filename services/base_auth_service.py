"""
Abstrakte Basis-Klasse für Authentifizierungs-Services.

Diese Klasse definiert die Schnittstelle für alle Authentifizierungsanbieter
und ermöglicht die Implementierung verschiedener Auth-Strategien.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..models.user_models import User, UserRegister
from ..models.auth_models import TokenData


class BaseAuthService(ABC):
    """
    Abstrakte Basis-Klasse für Authentifizierungs-Services.

    Definiert die gemeinsame Schnittstelle für alle Authentifizierungsanbieter
    wie Database Auth, OAuth, LDAP, etc.
    """

    def __init__(self, config: Any, provider_name: str):
        """
        Initialisiert den BaseAuthService.

        Args:
            config: Konfigurationsobjekt
            provider_name: Name des Auth-Providers (z.B. "database", "google", "ldap")
        """
        self.config = config
        self.provider_name = provider_name

    @abstractmethod
    def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[User]:
        """
        Authentifiziert einen Benutzer basierend auf den Anmeldedaten.

        Args:
            credentials: Dictionary mit Anmeldedaten (variiert je nach Provider)
                        - Für Database: {"email": str, "password": str}
                        - Für OAuth: {"code": str, "state": str}
                        - Für Token: {"token": str}

        Returns:
            User-Objekt wenn authentifiziert, None andernfalls
        """
        pass

    @abstractmethod
    def login(self, credentials: Dict[str, Any]) -> Optional[TokenData]:
        """
        Führt Login durch und gibt Token-Daten zurück.

        Args:
            credentials: Anmeldedaten

        Returns:
            TokenData wenn erfolgreich, None bei Fehlschlag
        """
        pass

    @abstractmethod
    def supports_registration(self) -> bool:
        """
        Gibt an, ob dieser Provider Benutzerregistrierung unterstützt.

        Returns:
            True wenn Registrierung unterstützt wird
        """
        pass

    @abstractmethod
    def register_user(self, user_register: UserRegister) -> Optional[User]:
        """
        Registriert einen neuen Benutzer (wenn unterstützt).

        Args:
            user_register: Registrierungsdaten

        Returns:
            Der erstellte Benutzer oder None wenn nicht unterstützt

        Raises:
            NotImplementedError: Wenn Registrierung nicht unterstützt wird
        """
        pass

    @abstractmethod
    def get_current_user(self, token: str) -> Optional[User]:
        """
        Holt den aktuellen Benutzer anhand des Tokens.

        Args:
            token: JWT-Access-Token

        Returns:
            User-Objekt wenn Token gültig, None andernfalls
        """
        pass

    @abstractmethod
    def create_password_reset_token(self, identifier: str) -> Optional[str]:
        """
        Erstellt einen Passwort-Reset-Token.

        Args:
            identifier: Benutzer-Identifikator (E-Mail, Username, etc.)

        Returns:
            Reset-Token wenn möglich, None andernfalls
        """
        pass

    @abstractmethod
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Setzt das Passwort zurück.

        Args:
            token: Reset-Token
            new_password: Neues Passwort

        Returns:
            True wenn erfolgreich
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Erneuert einen Access-Token.

        Args:
            refresh_token: Der Refresh-Token

        Returns:
            Neue Token-Daten wenn gültig
        """
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        Widerruft einen Token.

        Args:
            token: Der zu widerrufende Token

        Returns:
            True wenn erfolgreich
        """
        pass

    @abstractmethod
    def is_token_valid(self, token: str) -> bool:
        """
        Prüft Token-Gültigkeit.

        Args:
            token: Der zu prüfende Token

        Returns:
            True wenn gültig
        """
        pass

    def get_provider_name(self) -> str:
        """
        Gibt den Namen des Auth-Providers zurück.

        Returns:
            Provider-Name
        """
        return self.provider_name

    def get_supported_credentials_types(self) -> list[str]:
        """
        Gibt unterstützte Anmeldedaten-Typen zurück.

        Returns:
            Liste der unterstützten Credential-Typen
        """
        return ["email_password"]  # Standard-Implementierung

    def get_user_permissions(self, user: User) -> list[str]:
        """
        Holt die Berechtigungen eines Benutzers.

        Args:
            user: Der Benutzer

        Returns:
            Liste der Berechtigungen
        """
        permissions = ["read"]  # Basis-Berechtigung

        if user.is_active:
            permissions.append("write")

        if user.is_superuser:
            permissions.extend(["admin", "delete", "manage_users"])

        return permissions

    def get_login_url(self, redirect_uri: Optional[str] = None) -> Optional[str]:
        """
        Gibt die Login-URL für externe Provider zurück.

        Args:
            redirect_uri: Optionale Redirect-URI

        Returns:
            Login-URL für externe Provider oder None für lokale Auth
        """
        return None  # Standard: keine externe Login-URL
