"""
Beispiel-Konfiguration für Multi-Provider-Authentifizierung.

Diese Datei zeigt, wie verschiedene Authentifizierungsanbieter
konfiguriert und priorisiert werden können.
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Basis-Konfiguration
BASE_CONFIG = {
    "SECRET_KEY": os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production"),
    "ACCESS_TOKEN_EXPIRE_MINUTES": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    "REFRESH_TOKEN_EXPIRE_DAYS": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
    "user_provider": "database"
}

# OAuth-Provider-Konfigurationen
OAUTH_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/oauth/callback/google"),
        "auth_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile"
    },
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/oauth/callback/github"),
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_info_url": "https://api.github.com/user",
        "scope": "user:email"
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/oauth/callback/microsoft"),
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "user_info_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile"
    }
}


# Pydantic-Modelle für strukturierte Konfiguration

class OAuthProviderConfig(BaseModel):
    """Konfiguration für einen OAuth-Provider."""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    auth_url: str = ""
    token_url: str = ""
    user_info_url: str = ""
    scope: str = ""


class AuthProviderConfig(BaseModel):
    """Konfiguration für einen Authentifizierungsanbieter."""
    type: str
    priority: int
    enabled: bool = True


class AuthConfig(BaseModel):
    """
    Pydantic-Konfigurationsmodell für das fastapi_users_auth-Modul.

    Dieses Modell ermöglicht typsichere Konfiguration und kann aus
    den bestehenden Dictionary-Funktionen instanziiert werden.
    """
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    )
    user_provider: str = "database"
    auth_providers: List[AuthProviderConfig] = Field(default_factory=list)
    oauth_providers: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "AuthConfig":
        """
        Erstellt eine AuthConfig-Instanz aus einem Dictionary.

        Args:
            config_dict: Konfigurationsdictionary (z.B. von get_auth_config())

        Returns:
            AuthConfig-Instanz
        """
        # Konvertiere auth_providers zu AuthProviderConfig-Objekten falls nötig
        if "auth_providers" in config_dict:
            auth_providers = []
            for provider in config_dict["auth_providers"]:
                if isinstance(provider, dict):
                    auth_providers.append(AuthProviderConfig(**provider))
                else:
                    auth_providers.append(provider)
            config_dict["auth_providers"] = auth_providers

        return cls(**config_dict)

    @classmethod
    def for_environment(cls, env: Optional[str] = None) -> "AuthConfig":
        """
        Erstellt eine AuthConfig für eine bestimmte Umgebung.

        Args:
            env: Umgebung ("development", "production", "testing")

        Returns:
            AuthConfig-Instanz für die Umgebung
        """
        config_dict = get_config_for_environment(env)
        return cls.from_dict(config_dict)

    @classmethod
    def for_development(cls) -> "AuthConfig":
        """Erstellt eine Entwicklungskonfiguration."""
        return cls.from_dict(get_development_config())

    @classmethod
    def for_production(cls) -> "AuthConfig":
        """Erstellt eine Produktionskonfiguration."""
        return cls.from_dict(get_production_config())

    @classmethod
    def for_testing(cls) -> "AuthConfig":
        """Erstellt eine Test-Konfiguration."""
        return cls.from_dict(get_testing_config())


# Authentifizierungsanbieter-Konfiguration
def get_auth_config(enable_oauth: bool = True) -> Dict[str, Any]:
    """
    Erstellt die Authentifizierungskonfiguration.

    Args:
        enable_oauth: Ob OAuth-Provider aktiviert werden sollen

    Returns:
        Vollständige Auth-Konfiguration
    """
    config = BASE_CONFIG.copy()
    config["oauth_providers"] = OAUTH_PROVIDERS

    # Auth-Provider definieren
    auth_providers = [
        {
            "type": "database",
            "priority": 10,
            "enabled": True
        }
    ]

    if enable_oauth:
        # Google OAuth (höchste Priorität bei OAuth)
        if OAUTH_PROVIDERS["google"]["client_id"]:
            auth_providers.append({
                "type": "oauth_google",
                "priority": 8,
                "enabled": True
            })

        # GitHub OAuth
        if OAUTH_PROVIDERS["github"]["client_id"]:
            auth_providers.append({
                "type": "oauth_github",
                "priority": 7,
                "enabled": True
            })

        # Microsoft OAuth
        if OAUTH_PROVIDERS["microsoft"]["client_id"]:
            auth_providers.append({
                "type": "oauth_microsoft",
                "priority": 6,
                "enabled": True
            })

    config["auth_providers"] = auth_providers
    return config


def get_development_config() -> Dict[str, Any]:
    """
    Entwicklungskonfiguration mit reduzierten OAuth-Anforderungen.

    Returns:
        Entwicklungskonfiguration
    """
    config = get_auth_config(enable_oauth=False)
    config.update({
        "ACCESS_TOKEN_EXPIRE_MINUTES": 60,  # Längere Token-Gültigkeit für Entwicklung
        "REFRESH_TOKEN_EXPIRE_DAYS": 30,
    })
    return config


def get_production_config() -> Dict[str, Any]:
    """
    Produktionskonfiguration mit allen Sicherheitsfeatures.

    Returns:
        Produktionskonfiguration
    """
    config = get_auth_config(enable_oauth=True)

    # Produktions-spezifische Sicherheitseinstellungen
    config.update({
        "ACCESS_TOKEN_EXPIRE_MINUTES": 15,  # Kürzere Token-Gültigkeit
        "REFRESH_TOKEN_EXPIRE_DAYS": 7,
    })

    return config


def get_testing_config() -> Dict[str, Any]:
    """
    Test-Konfiguration mit Mock-Providern.

    Returns:
        Test-Konfiguration
    """
    config = BASE_CONFIG.copy()
    config.update({
        "SECRET_KEY": "test-secret-key",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 5,
        "auth_providers": [
            {
                "type": "database",
                "priority": 10,
                "enabled": True
            }
        ],
        "oauth_providers": {}
    })
    return config


# Umgebungsbasierte Konfiguration
def get_config_for_environment(env: str = None) -> Dict[str, Any]:
    """
    Gibt die Konfiguration für eine bestimmte Umgebung zurück.

    Args:
        env: Umgebung ("development", "production", "testing")

    Returns:
        Umgebungs-spezifische Konfiguration
    """
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return get_production_config()
    elif env == "testing":
        return get_testing_config()
    else:
        return get_development_config()


# Beispiel für manuelle Provider-Konfiguration
def get_custom_config() -> Dict[str, Any]:
    """
    Beispiel für eine benutzerdefinierte Konfiguration.

    Returns:
        Benutzerdefinierte Konfiguration
    """
    return {
        "SECRET_KEY": "custom-secret-key",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 45,
        "REFRESH_TOKEN_EXPIRE_DAYS": 14,
        "user_provider": "database",

        # Nur Google und Database Auth
        "auth_providers": [
            {
                "type": "database",
                "priority": 10,
                "enabled": True
            },
            {
                "type": "oauth_google",
                "priority": 9,
                "enabled": True
            }
        ],

        # Nur Google OAuth konfiguriert
        "oauth_providers": {
            "google": {
                "client_id": "your-google-client-id",
                "client_secret": "your-google-client-secret",
                "redirect_uri": "https://yourdomain.com/auth/oauth/callback/google",
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile"
            }
        }
    }
