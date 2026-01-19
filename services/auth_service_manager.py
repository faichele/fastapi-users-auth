"""
Multi-Provider Auth Service Manager.

Dieser Service Manager verwaltet mehrere Authentifizierungsanbieter und
stellt Fallback-Mechanismen sowie kombinierte Funktionalität bereit.
"""

from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from ..models.user_models import User, UserRegister
from ..models.auth_models import TokenData
from .base_auth_service import BaseAuthService
from .base_user_service import BaseUserService


class AuthServiceManager:
    """
    Manager für mehrere Authentifizierungsanbieter.

    Ermöglicht die Verwendung verschiedener Auth-Provider mit Fallback-Mechanismen
    und kombinierter Funktionalität.
    """

    def __init__(self, primary_user_service: BaseUserService):
        """
        Initialisiert den AuthServiceManager.

        Args:
            primary_user_service: Primärer UserService für Benutzerverwaltung
        """
        self.auth_providers: List[BaseAuthService] = []
        self.user_service = primary_user_service
        self.provider_priority: Dict[str, int] = {}

    def add_auth_provider(self, auth_service: BaseAuthService, priority: int = 0) -> None:
        """
        Fügt einen Authentifizierungsanbieter hinzu.

        Args:
            auth_service: Der hinzuzufügende AuthService
            priority: Priorität (höher = wird zuerst versucht)
        """
        self.auth_providers.append(auth_service)
        self.provider_priority[auth_service.get_provider_name()] = priority

        # Nach Priorität sortieren (höchste zuerst)
        self.auth_providers.sort(
            key=lambda x: self.provider_priority.get(x.get_provider_name(), 0),
            reverse=True
        )

    def remove_auth_provider(self, provider_name: str) -> bool:
        """
        Entfernt einen Authentifizierungsanbieter.

        Args:
            provider_name: Name des zu entfernenden Providers

        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        for i, provider in enumerate(self.auth_providers):
            if provider.get_provider_name() == provider_name:
                del self.auth_providers[i]
                del self.provider_priority[provider_name]
                return True
        return False

    def get_auth_provider(self, provider_name: str) -> Optional[BaseAuthService]:
        """
        Holt einen spezifischen Authentifizierungsanbieter.

        Args:
            provider_name: Name des Providers

        Returns:
            AuthService wenn gefunden, None andernfalls
        """
        for provider in self.auth_providers:
            if provider.get_provider_name() == provider_name:
                return provider
        return None

    def list_auth_providers(self) -> List[Dict[str, Any]]:
        """
        Listet alle verfügbaren Authentifizierungsanbieter auf.

        Returns:
            Liste mit Provider-Informationen
        """
        providers = []
        for provider in self.auth_providers:
            info = {
                "name": provider.get_provider_name(),
                "priority": self.provider_priority.get(provider.get_provider_name(), 0),
                "supports_registration": provider.supports_registration(),
                "supported_credentials": provider.get_supported_credentials_types(),
                "login_url": provider.get_login_url()
            }
            providers.append(info)
        return providers

    def authenticate_user(self, credentials: Dict[str, Any], provider_name: Optional[str] = None) -> Optional[tuple[User, str]]:
        """
        Authentifiziert einen Benutzer mit optionalem Provider.

        Args:
            credentials: Anmeldedaten
            provider_name: Optionaler spezifischer Provider

        Returns:
            Tuple aus (User, Provider-Name) wenn erfolgreich, None andernfalls
        """
        providers_to_try = []

        if provider_name:
            # Spezifischen Provider versuchen
            provider = self.get_auth_provider(provider_name)
            if provider:
                providers_to_try = [provider]
        else:
            # Alle passenden Provider nach Priorität versuchen
            credential_type = self._detect_credential_type(credentials)
            providers_to_try = [
                p for p in self.auth_providers
                if credential_type in p.get_supported_credentials_types()
            ]

        for provider in providers_to_try:
            try:
                user = provider.authenticate_user(credentials)
                if user:
                    return user, provider.get_provider_name()
            except Exception as e:
                # Logging würde hier implementiert werden
                continue

        return None

    def login(self, credentials: Dict[str, Any], provider_name: Optional[str] = None) -> Optional[TokenData]:
        """
        Führt Login mit optionalem Provider durch.

        Args:
            credentials: Anmeldedaten
            provider_name: Optionaler spezifischer Provider

        Returns:
            TokenData wenn erfolgreich, None bei Fehlschlag
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.login(credentials)
        else:
            # Fallback: alle passenden Provider versuchen
            credential_type = self._detect_credential_type(credentials)
            providers_to_try = [
                p for p in self.auth_providers
                if credential_type in p.get_supported_credentials_types()
            ]

            for provider in providers_to_try:
                try:
                    result = provider.login(credentials)
                    if result:
                        return result
                except Exception as e:
                    continue

        return None

    def register_user(self, user_register: UserRegister, provider_name: Optional[str] = None) -> Optional[User]:
        """
        Registriert einen Benutzer mit optionalem Provider.

        Args:
            user_register: Registrierungsdaten
            provider_name: Optionaler spezifischer Provider

        Returns:
            Der erstellte Benutzer oder None
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider and provider.supports_registration():
                return provider.register_user(user_register)
        else:
            # Ersten Provider verwenden, der Registrierung unterstützt
            for provider in self.auth_providers:
                if provider.supports_registration():
                    try:
                        return provider.register_user(user_register)
                    except Exception as e:
                        continue

        return None

    def get_current_user(self, token: str, provider_name: Optional[str] = None) -> Optional[User]:
        """
        Holt den aktuellen Benutzer anhand des Tokens.

        Args:
            token: JWT-Access-Token
            provider_name: Optionaler spezifischer Provider

        Returns:
            User-Objekt wenn Token gültig, None andernfalls
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.get_current_user(token)
        else:
            # Alle Provider versuchen
            for provider in self.auth_providers:
                try:
                    user = provider.get_current_user(token)
                    if user:
                        return user
                except Exception as e:
                    continue

        return None

    def create_password_reset_token(self, identifier: str, provider_name: Optional[str] = None) -> Optional[str]:
        """
        Erstellt einen Passwort-Reset-Token.

        Args:
            identifier: Benutzer-Identifikator
            provider_name: Optionaler spezifischer Provider

        Returns:
            Reset-Token wenn möglich, None andernfalls
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.create_password_reset_token(identifier)
        else:
            # Ersten Provider verwenden, der Password-Reset unterstützt
            for provider in self.auth_providers:
                try:
                    token = provider.create_password_reset_token(identifier)
                    if token:
                        return token
                except Exception as e:
                    continue

        return None

    def reset_password(self, token: str, new_password: str, provider_name: Optional[str] = None) -> bool:
        """
        Setzt das Passwort zurück.

        Args:
            token: Reset-Token
            new_password: Neues Passwort
            provider_name: Optionaler spezifischer Provider

        Returns:
            True wenn erfolgreich
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.reset_password(token, new_password)
        else:
            # Alle Provider versuchen
            for provider in self.auth_providers:
                try:
                    if provider.reset_password(token, new_password):
                        return True
                except Exception as e:
                    continue

        return False

    def refresh_token(self, refresh_token: str, provider_name: Optional[str] = None) -> Optional[TokenData]:
        """
        Erneuert einen Access-Token.

        Args:
            refresh_token: Der Refresh-Token
            provider_name: Optionaler spezifischer Provider

        Returns:
            Neue Token-Daten wenn gültig
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.refresh_token(refresh_token)
        else:
            # Alle Provider versuchen
            for provider in self.auth_providers:
                try:
                    result = provider.refresh_token(refresh_token)
                    if result:
                        return result
                except Exception as e:
                    continue

        return None

    def revoke_token(self, token: str, provider_name: Optional[str] = None) -> bool:
        """
        Widerruft einen Token.

        Args:
            token: Der zu widerrufende Token
            provider_name: Optionaler spezifischer Provider

        Returns:
            True wenn erfolgreich
        """
        success = False

        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.revoke_token(token)
        else:
            # Bei allen Providern versuchen
            for provider in self.auth_providers:
                try:
                    if provider.revoke_token(token):
                        success = True
                except Exception as e:
                    continue

        return success

    def is_token_valid(self, token: str, provider_name: Optional[str] = None) -> bool:
        """
        Prüft Token-Gültigkeit.

        Args:
            token: Der zu prüfende Token
            provider_name: Optionaler spezifischer Provider

        Returns:
            True wenn gültig
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.is_token_valid(token)
        else:
            # Bei allen Providern versuchen
            for provider in self.auth_providers:
                try:
                    if provider.is_token_valid(token):
                        return True
                except Exception as e:
                    continue

        return False

    def get_user_permissions(self, user: User, provider_name: Optional[str] = None) -> list[str]:
        """
        Holt die Berechtigungen eines Benutzers.

        Args:
            user: Der Benutzer
            provider_name: Optionaler spezifischer Provider

        Returns:
            Liste der Berechtigungen
        """
        if provider_name:
            provider = self.get_auth_provider(provider_name)
            if provider:
                return provider.get_user_permissions(user)

        # Alle Provider abfragen und Berechtigungen zusammenführen
        all_permissions = set()
        for provider in self.auth_providers:
            try:
                permissions = provider.get_user_permissions(user)
                all_permissions.update(permissions)
            except Exception as e:
                continue

        return list(all_permissions)

    def _detect_credential_type(self, credentials: Dict[str, Any]) -> str:
        """
        Erkennt den Typ der Anmeldedaten.

        Args:
            credentials: Anmeldedaten

        Returns:
            Credential-Typ
        """
        if "email" in credentials and "password" in credentials:
            return "email_password"
        elif "code" in credentials or "access_token" in credentials:
            return "oauth_code" if "code" in credentials else "oauth_token"
        elif "token" in credentials:
            return "token"
        else:
            return "unknown"

    def get_primary_user_service(self) -> BaseUserService:
        """
        Gibt den primären UserService zurück.

        Returns:
            Der primäre UserService
        """
        return self.user_service

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Provider zurück.

        Returns:
            Dictionary mit Statistiken
        """
        return {
            "total_providers": len(self.auth_providers),
            "providers": [
                {
                    "name": p.get_provider_name(),
                    "priority": self.provider_priority.get(p.get_provider_name(), 0),
                    "supports_registration": p.supports_registration(),
                    "credential_types": p.get_supported_credentials_types()
                }
                for p in self.auth_providers
            ]
        }
