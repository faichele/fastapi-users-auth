"""
Service Factory für die Erstellung von Auth- und User-Services.

Diese Factory erstellt Services basierend auf der Konfiguration und
ermöglicht die einfache Integration verschiedener Provider.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .base_auth_service import BaseAuthService
from .base_user_service import BaseUserService
from .user_service import DatabaseUserService
from .auth_service import DatabaseAuthService
from .oauth_auth_service import OAuthAuthService
from .auth_service_manager import AuthServiceManager


class ServiceFactory:
    """
    Factory-Klasse für die Erstellung von Authentication- und User-Services.

    Erstellt Services basierend auf Konfiguration und verwaltet Dependencies.
    """

    @staticmethod
    def create_user_service(config: Dict[str, Any], db_session: Optional[Session] = None) -> BaseUserService:
        """
        Erstellt einen UserService basierend auf der Konfiguration.

        Args:
            config: Konfiguration mit Provider-Details
            db_session: Optional SQLAlchemy Session

        Returns:
            BaseUserService-Implementierung

        Raises:
            ValueError: Wenn Provider nicht unterstützt wird
        """
        provider_type = config.get("user_provider", "database")

        if provider_type == "database":
            if not db_session:
                raise ValueError("Database session required for database user provider")
            return DatabaseUserService(db_session, config)
        else:
            raise ValueError(f"Unsupported user provider: {provider_type}")

    @staticmethod
    def create_auth_service(
        config: Dict[str, Any],
        user_service: BaseUserService,
        db_session: Optional[Session] = None
    ) -> BaseAuthService:
        """
        Erstellt einen einzelnen AuthService basierend auf der Konfiguration.

        Args:
            config: Konfiguration mit Provider-Details
            user_service: UserService für Benutzerverwaltung
            db_session: Optional SQLAlchemy Session

        Returns:
            BaseAuthService-Implementierung

        Raises:
            ValueError: Wenn Provider nicht unterstützt wird
        """
        provider_type = config.get("auth_provider", "database")

        if provider_type == "database":
            if not db_session:
                raise ValueError("Database session required for database auth provider")
            return DatabaseAuthService(db_session, config)

        elif provider_type.startswith("oauth_"):
            oauth_provider = provider_type.replace("oauth_", "")
            oauth_config = config.get("oauth_providers", {}).get(oauth_provider)

            if not oauth_config:
                raise ValueError(f"OAuth configuration missing for provider: {oauth_provider}")

            oauth_config["provider"] = oauth_provider
            return OAuthAuthService(user_service, config, oauth_config)

        else:
            raise ValueError(f"Unsupported auth provider: {provider_type}")

    @staticmethod
    def create_auth_service_manager(
        config: Dict[str, Any],
        db_session: Optional[Session] = None
    ) -> AuthServiceManager:
        """
        Erstellt einen AuthServiceManager mit konfigurierten Providern.

        Args:
            config: Vollständige Konfiguration
            db_session: Optional SQLAlchemy Session

        Returns:
            Konfigurierter AuthServiceManager

        Example config:
        {
            "user_provider": "database",
            "auth_providers": [
                {
                    "type": "database",
                    "priority": 10,
                    "enabled": True
                },
                {
                    "type": "oauth_google",
                    "priority": 5,
                    "enabled": True
                }
            ],
            "oauth_providers": {
                "google": {
                    "client_id": "...",
                    "client_secret": "...",
                    "redirect_uri": "...",
                    "auth_url": "https://accounts.google.com/o/oauth2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                    "scope": "openid email profile"
                }
            }
        }
        """
        # Primären UserService erstellen
        user_service = ServiceFactory.create_user_service(config, db_session)

        # AuthServiceManager erstellen
        manager = AuthServiceManager(user_service)

        # Auth-Provider basierend auf Konfiguration hinzufügen
        auth_providers_config = config.get("auth_providers", [])

        for provider_config in auth_providers_config:
            if not provider_config.get("enabled", True):
                continue

            try:
                # Provider-spezifische Konfiguration erstellen
                provider_config_copy = dict(config)
                provider_config_copy.update(provider_config)
                provider_config_copy["auth_provider"] = provider_config["type"]

                # AuthService erstellen
                auth_service = ServiceFactory.create_auth_service(
                    provider_config_copy,
                    user_service,
                    db_session
                )

                # Zum Manager hinzufügen
                priority = provider_config.get("priority", 0)
                manager.add_auth_provider(auth_service, priority)

            except Exception as e:
                # Logging würde hier implementiert werden
                print(f"Failed to create auth provider {provider_config.get('type')}: {e}")
                continue

        return manager

    @staticmethod
    def create_oauth_provider_configs() -> Dict[str, Dict[str, Any]]:
        """
        Gibt Standard-OAuth-Provider-Konfigurationen zurück.

        Returns:
            Dictionary mit OAuth-Provider-Konfigurationen
        """
        return {
            "google": {
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile"
            },
            "github": {
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user",
                "scope": "user:email"
            },
            "microsoft": {
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "user_info_url": "https://graph.microsoft.com/v1.0/me",
                "scope": "openid email profile"
            },
            "discord": {
                "auth_url": "https://discord.com/api/oauth2/authorize",
                "token_url": "https://discord.com/api/oauth2/token",
                "user_info_url": "https://discord.com/api/users/@me",
                "scope": "identify email"
            }
        }

    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """
        Erstellt eine Standard-Konfiguration.

        Returns:
            Standard-Konfiguration
        """
        oauth_configs = ServiceFactory.create_oauth_provider_configs()

        return {
            "user_provider": "database",
            "auth_providers": [
                {
                    "type": "database",
                    "priority": 10,
                    "enabled": True
                }
            ],
            "oauth_providers": oauth_configs,
            "SECRET_KEY": "your-secret-key-here",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
            "REFRESH_TOKEN_EXPIRE_DAYS": 7
        }

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """
        Validiert eine Konfiguration und gibt Fehler zurück.

        Args:
            config: Zu validierende Konfiguration

        Returns:
            Liste der Validierungsfehler
        """
        errors = []

        # Basis-Konfiguration prüfen
        if "SECRET_KEY" not in config:
            errors.append("SECRET_KEY is required")

        if "ACCESS_TOKEN_EXPIRE_MINUTES" not in config:
            errors.append("ACCESS_TOKEN_EXPIRE_MINUTES is required")

        # User-Provider prüfen
        user_provider = config.get("user_provider", "database")
        if user_provider not in ["database"]:
            errors.append(f"Unsupported user_provider: {user_provider}")

        # Auth-Provider prüfen
        auth_providers = config.get("auth_providers", [])
        oauth_providers = config.get("oauth_providers", {})

        for provider_config in auth_providers:
            provider_type = provider_config.get("type")

            if not provider_type:
                errors.append("Auth provider type is required")
                continue

            if provider_type == "database":
                continue  # Keine zusätzliche Validierung nötig

            elif provider_type.startswith("oauth_"):
                oauth_name = provider_type.replace("oauth_", "")
                oauth_config = oauth_providers.get(oauth_name)

                if not oauth_config:
                    errors.append(f"OAuth configuration missing for {oauth_name}")
                    continue

                # OAuth-spezifische Felder prüfen
                required_oauth_fields = ["client_id", "client_secret", "redirect_uri", "auth_url", "token_url", "user_info_url"]
                for field in required_oauth_fields:
                    if field not in oauth_config:
                        errors.append(f"OAuth {oauth_name}: {field} is required")

            else:
                errors.append(f"Unsupported auth provider type: {provider_type}")

        return errors


def create_services_from_config(
    config: Dict[str, Any],
    db_session: Optional[Session] = None
) -> tuple[BaseUserService, AuthServiceManager]:
    """
    Convenience-Funktion zur Erstellung aller Services aus Konfiguration.

    Args:
        config: Vollständige Konfiguration
        db_session: Optional SQLAlchemy Session

    Returns:
        Tuple aus (UserService, AuthServiceManager)

    Raises:
        ValueError: Bei Konfigurationsfehlern
    """
    # Konfiguration validieren
    errors = ServiceFactory.validate_config(config)
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    # Services erstellen
    user_service = ServiceFactory.create_user_service(config, db_session)
    auth_manager = ServiceFactory.create_auth_service_manager(config, db_session)

    return user_service, auth_manager
