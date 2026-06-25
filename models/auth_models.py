"""
Pydantic-Modelle für Authentifizierung und Token-Management.

Diese Modelle definieren die Datenstrukturen für:
- JWT-Token und deren Payload
- Passwort-Reset-Funktionalität
- API-Nachrichten und Antworten
"""
import enum

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class IdentityProvider(str, enum.Enum):
    Integrated = "Integrated"


class TwoFactorAuthentication(str, enum.Enum):
    Off = "Off"
    HOTP = "HOTP"
    TOTP = "TOTP"


class Token(BaseModel):
    """Pydantic-Modell für JWT-Access-Token."""

    access_token: str = Field(..., description="JWT-Access-Token")
    token_type: str = Field(default="bearer", description="Token-Typ")
    expires_in: Optional[int] = Field(None, description="Token-Gültigkeitsdauer in Sekunden")
    refresh_token: Optional[str] = Field(None, description="JWT-Refresh-Token (optional, z.B. bei Token-Rotation)")


class TokenData(BaseModel):
    """Pydantic-Modell für Token-Daten mit Benutzerinformationen."""

    access_token: str = Field(..., description="JWT-Access-Token")
    token_type: str = Field(default="bearer", description="Token-Typ")
    expires_in: Optional[int] = Field(None, description="Token-Gültigkeitsdauer in Sekunden")
    refresh_token: Optional[str] = Field(None, description="JWT-Refresh-Token (optional)")
    user_id: UUID = Field(..., description="Benutzer-ID")
    email: str = Field(..., description="E-Mail-Adresse des Benutzers")
    is_superuser: bool = Field(False, description="Superuser-Status")
    requires_2fa: bool = Field(False, description="Zwei-Faktor-Authentifizierung erforderlich")
    requires_2fa_registration: bool = Field(False,
                                            description="Registrierung mit Zwei-Faktor-Authentifizierung erforderlich")
    requires_password_update: bool = Field(False, description="Passwort-Update erforderlich")


class TokenPayload(BaseModel):
    """Pydantic-Modell für JWT-Token-Payload (Standard-Claims nach RFC 7519)."""

    sub: Optional[str] = Field(None, description="Subject (Benutzer-ID)")
    exp: Optional[datetime] = Field(None, description="Ablaufzeit")
    iat: Optional[datetime] = Field(None, description="Ausstellungszeit")
    iss: Optional[str] = Field(None, description="Aussteller")
    jti: Optional[str] = Field(None, description="JWT-ID (eindeutige Token-Kennung)")


class TokenPayloadData(BaseModel):
    """Erweiterte Token-Payload mit zusätzlichen Benutzerdaten."""

    sub: str = Field(..., description="Subject (Benutzer-ID)")
    exp: datetime = Field(..., description="Ablaufzeit")
    iat: datetime = Field(..., description="Ausstellungszeit")
    email: str = Field(..., description="E-Mail-Adresse")
    is_superuser: bool = Field(False, description="Superuser-Status")
    token_type: str = Field(default="access", description="Token-Typ")


class NewPassword(BaseModel):
    """Pydantic-Modell für neues Passwort mit Token."""

    token: str = Field(..., description="Passwort-Reset-Token")
    new_password: str = Field(..., min_length=8, description="Neues Passwort (mindestens 8 Zeichen)")


class NewPasswordRequest(BaseModel):
    """Pydantic-Modell für Passwort-Reset-Anfrage."""

    email: str = Field(..., description="E-Mail-Adresse für Passwort-Reset")


class Message(BaseModel):
    """Pydantic-Modell für API-Nachrichten."""

    message: str = Field(..., description="Nachrichtentext")
    success: bool = Field(default=True, description="Erfolgs-Status")
    data: Optional[Any] = Field(None, description="Zusätzliche Daten")


class UserAlert(BaseModel):
    password_expires_in: Optional[int] = None
    license_expires_in: Optional[int] = None


class PasswordResetToken(BaseModel):
    """Pydantic-Modell für Passwort-Reset-Token."""

    email: str = Field(..., description="E-Mail-Adresse")
    token: str = Field(..., description="Reset-Token")
    expires_at: datetime = Field(..., description="Ablaufzeit")


class LoginResponse(BaseModel):
    """Pydantic-Modell für erfolgreiche Login-Antwort."""

    access_token: str = Field(..., description="JWT-Access-Token")
    token_type: str = Field(default="bearer", description="Token-Typ")
    expires_in: int = Field(..., description="Token-Gültigkeitsdauer in Sekunden")
    user: dict = Field(..., description="Benutzerinformationen")
    message: str = Field(default="Login erfolgreich", description="Erfolgs-Nachricht")


class TwoFactorAuthSecret(BaseModel):
    secret: str
    uri: str
    type: TwoFactorAuthentication


class TwoFactorAuthVerificationCode(BaseModel):
    otp: str

