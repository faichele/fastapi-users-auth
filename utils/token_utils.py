"""
Token-Utilities für JWT-Token-Management.

Diese Klasse behandelt:
- JWT-Token-Erstellung und -Verifikation
- Token-Payload-Handling
- Passwort-Reset-Token
- Token-Ablaufzeit-Management
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from uuid import UUID

import jwt
from pydantic import ValidationError

from fastapi_users_auth.models.auth_models import TokenPayload, TokenPayloadData


class TokenUtils:
    """
    Utility-Klasse für JWT-Token-Management.

    Kapselt alle token-bezogenen Operationen wie Erstellung,
    Verifikation und Dekodierung von JWT-Tokens.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialisiert die TokenUtils.

        Args:
            secret_key: Der Geheimschlüssel für JWT-Signierung
            algorithm: Der zu verwendende Algorithmus (Standard: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict] = None
    ) -> str:
        """
        Erstellt einen JWT-Access-Token.

        Args:
            subject: Das Subject (normalerweise die Benutzer-ID)
            expires_delta: Ablaufzeit als timedelta
            additional_claims: Zusätzliche Claims für den Token

        Returns:
            Der erstellte JWT-Token als String
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }

        # Zusätzliche Claims hinzufügen
        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Erstellt einen JWT-Refresh-Token.

        Args:
            subject: Das Subject (normalerweise die Benutzer-ID)
            expires_delta: Ablaufzeit als timedelta

        Returns:
            Der erstellte Refresh-Token als String
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verifiziert und dekodiert einen JWT-Token.

        Args:
            token: Der zu verifizierende Token

        Returns:
            TokenPayload wenn gültig, None wenn ungültig
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            token_data = TokenPayload(**payload)
            return token_data
        except (jwt.PyJWTError, ValidationError):
            return None

    def decode_token(self, token: str) -> Optional[dict]:
        """
        Dekodiert einen Token ohne Verifikation (für Debug-Zwecke).

        Args:
            token: Der zu dekodierende Token

        Returns:
            Dekodierte Payload als dict oder None
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except jwt.PyJWTError:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        Überprüft, ob ein Token abgelaufen ist.

        Args:
            token: Der zu überprüfende Token

        Returns:
            True wenn abgelaufen, False wenn noch gültig
        """
        payload = self.decode_token(token)
        if not payload or "exp" not in payload:
            return True

        exp_timestamp = payload["exp"]
        expiry_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        return datetime.now(timezone.utc) > expiry_time

    def get_token_subject(self, token: str) -> Optional[str]:
        """
        Extrahiert das Subject aus einem Token.

        Args:
            token: Der Token

        Returns:
            Das Subject als String oder None
        """
        token_data = self.verify_token(token)
        return token_data.sub if token_data else None

    def create_password_reset_token(self, email: str) -> str:
        """
        Erstellt einen Token für Passwort-Reset.

        Args:
            email: E-Mail-Adresse des Benutzers

        Returns:
            Der Passwort-Reset-Token
        """
        delta = timedelta(hours=48)  # 48 Stunden gültig
        expire = datetime.now(timezone.utc) + delta

        to_encode = {
            "exp": expire,
            "sub": email,
            "iat": datetime.now(timezone.utc),
            "type": "password_reset"
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """
        Verifiziert einen Passwort-Reset-Token.

        Args:
            token: Der zu verifizierende Token

        Returns:
            E-Mail-Adresse wenn gültig, None wenn ungültig
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )

            # Überprüfen, ob es ein Passwort-Reset-Token ist
            if payload.get("type") != "password_reset":
                return None

            return payload.get("sub")
        except jwt.PyJWTError:
            return None

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generiert einen sicheren zufälligen Token.

        Args:
            length: Länge des Tokens in Bytes (Standard: 32)

        Returns:
            Ein URL-sicherer Token-String
        """
        return secrets.token_urlsafe(length)

    def extract_token_claims(self, token: str) -> Optional[dict]:
        """
        Extrahiert alle Claims aus einem Token.

        Args:
            token: Der Token

        Returns:
            Dictionary mit allen Claims oder None
        """
        token_data = self.verify_token(token)
        if not token_data:
            return None

        return token_data.model_dump()


# Convenience-Funktionen für einfache Verwendung
def create_access_token(
    subject: Union[str, Any],
    secret_key: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """Convenience-Funktion für Token-Erstellung."""
    token_utils = TokenUtils(secret_key)
    return token_utils.create_access_token(subject, expires_delta, additional_claims)


def verify_token(token: str, secret_key: str) -> Optional[TokenPayload]:
    """Convenience-Funktion für Token-Verifikation."""
    token_utils = TokenUtils(secret_key)
    return token_utils.verify_token(token)
