"""
Database Auth Service - Datenbankbasierte Authentifizierung.

Diese Klasse implementiert die Authentifizierung über SQLAlchemy und Datenbank.
Sie erbt von BaseAuthService und stellt eine konkrete Implementierung für
datenbankbasierte Authentifizierung bereit.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.user_models import User, UserRegister
from ..models.auth_models import Token, TokenData, LoginResponse
from ..utils.security import SecurityUtils
from ..utils.token_utils import TokenUtils
from .base_auth_service import BaseAuthService
from .user_service import DatabaseUserService


class DatabaseAuthService(BaseAuthService):
    """
    Datenbankbasierte Implementierung des AuthService.

    Diese Klasse behandelt Login, Token-Management und Session-Handling
    über eine SQLAlchemy-Datenbank.
    """

    def __init__(self, db_session: Session, config):
        """
        Initialisiert den DatabaseAuthService.

        Args:
            db_session: SQLAlchemy Session für Datenbankoperationen
            config: Konfigurationsobjekt mit SECRET_KEY und TOKEN_EXPIRE_MINUTES
        """
        super().__init__(config, "database")
        self.db = db_session
        self.security = SecurityUtils()
        self.token_utils = TokenUtils(config.SECRET_KEY)
        self.user_service = DatabaseUserService(db_session, config)

    def get_supported_credentials_types(self) -> list[str]:
        """
        Gibt unterstützte Anmeldedaten-Typen zurück.

        Returns:
            Liste der unterstützten Credential-Typen
        """
        return ["email_password"]

    def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[User]:
        """
        Authentifiziert einen Benutzer anhand von E-Mail und Passwort.

        Args:
            credentials: Dictionary mit {"email": str, "password": str}

        Returns:
            User-Objekt wenn authentifiziert, None andernfalls
        """
        email = credentials.get("email")
        password = credentials.get("password")

        if not email or not password:
            return None

        user = self.user_service.get_user_by_email(email)
        if not user:
            return None

        if not self.security.verify_password(password, user.hashed_password):
            return None

        return user

    def login(self, credentials: Dict[str, Any]) -> Optional[TokenData]:
        """
        Meldet einen Benutzer an und gibt Token-Daten zurück.

        Args:
            credentials: Dictionary mit Anmeldedaten

        Returns:
            TokenData wenn erfolgreich, None bei Fehlschlag
        """
        user = self.authenticate_user(credentials)
        if not user:
            return None

        if not user.is_active:
            return None

        # Access Token erstellen
        access_token_expires = timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.token_utils.create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            additional_claims={
                "email": user.email,
                "is_superuser": user.is_superuser
            }
        )

        # Initiales Refresh-Token erstellen
        refresh_token_expires = timedelta(days=getattr(self.config, "REFRESH_TOKEN_EXPIRE_DAYS", 7))
        refresh_token = self.token_utils.create_refresh_token(
            subject=str(user.id),
            expires_delta=refresh_token_expires
        )

        # Login-Zeit aktualisieren
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()

        return TokenData(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            is_superuser=user.is_superuser
        )

    def supports_registration(self) -> bool:
        """
        Gibt an, ob dieser Provider Benutzerregistrierung unterstützt.

        Returns:
            True für Database-Provider
        """
        return True

    def register_user(self, user_register: UserRegister) -> Optional[User]:
        """
        Registriert einen neuen Benutzer.

        Args:
            user_register: Registrierungsdaten

        Returns:
            Der erstellte Benutzer

        Raises:
            ValueError: Wenn E-Mail bereits existiert
        """
        from ..models.user_models import UserCreate

        # UserCreate-Objekt erstellen
        user_create = UserCreate(
            email=user_register.email,
            password=user_register.password,
            full_name=user_register.full_name,
            is_active=True,
            is_superuser=False
        )

        return self.user_service.create_user(user_create)

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
            user = self.user_service.get_user_by_id(user_id)
            return user
        except ValueError:
            return None

    def get_current_active_user(self, token: str) -> Optional[User]:
        """
        Holt den aktuellen aktiven Benutzer anhand des Tokens.

        Args:
            token: JWT-Access-Token

        Returns:
            User-Objekt wenn Token gültig und Benutzer aktiv, None andernfalls
        """
        user = self.get_current_user(token)
        if not user or not user.is_active:
            return None
        return user

    def get_current_superuser(self, token: str) -> Optional[User]:
        """
        Holt den aktuellen Superuser anhand des Tokens.

        Args:
            token: JWT-Access-Token

        Returns:
            User-Objekt wenn Token gültig und Benutzer Superuser, None andernfalls
        """
        user = self.get_current_active_user(token)
        if not user or not user.is_superuser:
            return None
        return user

    def create_password_reset_token(self, email: str) -> Optional[str]:
        """
        Erstellt einen Passwort-Reset-Token für eine E-Mail-Adresse.

        Args:
            email: E-Mail-Adresse des Benutzers

        Returns:
            Reset-Token wenn Benutzer existiert, None andernfalls
        """
        user = self.user_service.get_user_by_email(email)
        if not user or not user.is_active:
            return None

        return self.token_utils.create_password_reset_token(email)

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Setzt das Passwort eines Benutzers anhand eines Reset-Tokens zurück.

        Args:
            token: Passwort-Reset-Token
            new_password: Neues Passwort

        Returns:
            True wenn erfolgreich, False andernfalls
        """
        email = self.token_utils.verify_password_reset_token(token)
        if not email:
            return False

        user = self.user_service.get_user_by_email(email)
        if not user or not user.is_active:
            return False

        # Passwort aktualisieren
        hashed_password = self.security.get_password_hash(new_password)
        user.hashed_password = hashed_password
        self.db.commit()

        return True

    def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Erneuert einen Access-Token anhand eines Refresh-Tokens.

        Args:
            refresh_token: Der Refresh-Token

        Returns:
            Neue TokenData wenn gültig, None andernfalls
        """
        token_data = self.token_utils.verify_token(refresh_token)
        if not token_data or not token_data.sub:
            return None

        # Prüfen, ob es ein Refresh-Token ist
        payload = self.token_utils.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
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
                    "is_superuser": user.is_superuser
                }
            )

            # Optional: Refresh-Token rotieren (empfohlen)
            refresh_token_expires = timedelta(days=getattr(self.config, "REFRESH_TOKEN_EXPIRE_DAYS", 7))
            new_refresh_token = self.token_utils.create_refresh_token(
                subject=str(user.id),
                expires_delta=refresh_token_expires
            )

            return TokenData(
                access_token=access_token,
                token_type="bearer",
                expires_in=int(access_token_expires.total_seconds()),
                user_id=user.id,
                email=user.email,
                is_superuser=user.is_superuser,
                # Wird vom Router in das Token-Response-Model gemappt
                refresh_token=new_refresh_token
            )

        except ValueError:
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Widerruft einen Token (für Logout).

        In einer vollständigen Implementierung würde hier eine Token-Blacklist
        verwaltet werden. Für diese Basisimplementierung wird True zurückgegeben.

        Args:
            token: Der zu widerrufende Token

        Returns:
            True wenn erfolgreich
        """
        # TODO: Implementierung einer Token-Blacklist
        # Für jetzt einfach True zurückgeben
        return True

    def is_token_valid(self, token: str) -> bool:
        """
        Prüft, ob ein Token gültig ist.

        Args:
            token: Der zu prüfende Token

        Returns:
            True wenn gültig, False andernfalls
        """
        token_data = self.token_utils.verify_token(token)
        return token_data is not None

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


# Alias für Rückwärtskompatibilität
AuthService = DatabaseAuthService
