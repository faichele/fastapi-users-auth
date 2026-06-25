"""
Pydantic-Modelle für Benutzer-Entitäten.

Diese Modelle definieren die Datenstrukturen für Benutzer in verschiedenen Kontexten:
- Datenbank-Entitäten (SQLAlchemy)
- API-Request/Response-Modelle (Pydantic)
- Interne Datenübertragung

Hinweis zu SQLAlchemy-Modellen (User, UserSession, …):
  Die SQLAlchemy-ORM-Klassen werden NICHT statisch hier definiert. Sie werden
  dynamisch durch :func:`~fastapi_users_auth.model_factory.configure_auth_models`
  in dieses Modul eingebunden. Nach dem Aufruf von ``configure_auth_models`` sind
  folgende Attribute verfügbar:
    - ``fastapi_users_auth.User``
    - ``fastapi_users_auth.UserSession``
    - ``fastapi_users_auth.Group``
    - ``fastapi_users_auth.UserGroupMembership``
  In Anwendungen wird empfohlen, diese Klassen über das ``database``-Package zu
  importieren (z. B. ``from database import UserSession``), da dort der Aufruf
  von ``configure_auth_models`` mit dem korrekten Präfix und den Anwendungs-Mixins
  garantiert ist.
"""
import enum

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator

# SQLAlchemy-ORM-Modelle werden per configure_auth_models in dieses Modul
# gepacht – Platzhalter damit Import-Prüftools (mypy, IDE) nicht warnen.
User: type = None  # type: ignore[assignment]
UserSession: type = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Pydantic Base Models
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class Language(str, enum.Enum):
    en = "en"
    de = "de"


class UserBase(BaseModel):
    """Basis-Pydantic-Modell für Benutzer."""

    email: EmailStr = Field(..., description="E-Mail-Adresse des Benutzers")
    full_name: Optional[str] = Field(None, description="Vollständiger Name des Benutzers")
    is_active: bool = Field(True, description="Ob der Benutzer aktiv ist")


class UserRegister(BaseModel):
    """Pydantic-Modell für die Benutzerregistrierung (öffentlich)."""

    email: EmailStr = Field(..., description="E-Mail-Adresse")
    password: str = Field(..., min_length=8, description="Passwort (mindestens 8 Zeichen)")
    full_name: Optional[str] = Field(None, description="Vollständiger Name")


class UserLogin(BaseModel):
    """Pydantic-Modell für die Benutzeranmeldung."""

    email: EmailStr = Field(..., description="E-Mail-Adresse")
    password: str = Field(..., description="Passwort")


class UserUpdate(BaseModel):
    """Pydantic-Modell für Benutzer-Updates (Admin)."""

    email: Optional[EmailStr] = Field(None, description="Neue E-Mail-Adresse")
    full_name: Optional[str] = Field(None, description="Neuer vollständiger Name")
    is_active: Optional[bool] = Field(None, description="Aktiv-Status")
    is_superuser: Optional[bool] = Field(None, description="Superuser-Status")
    password: Optional[str] = Field(None, min_length=8, description="Neues Passwort")


class UserUpdateMe(BaseModel):
    """Pydantic-Modell für Benutzer-Updates (selbst)."""

    full_name: Optional[str] = Field(None, description="Neuer vollständiger Name")
    email: Optional[EmailStr] = Field(None, description="Neue E-Mail-Adresse")


class UpdatePassword(BaseModel):
    """Pydantic-Modell für Passwort-Updates."""

    current_password: str = Field(..., description="Aktuelles Passwort")
    new_password: str = Field(..., min_length=8, description="Neues Passwort (mindestens 8 Zeichen)")


class UserInDB(UserBase):
    """Pydantic-Modell für Benutzer mit Datenbank-spezifischen Feldern."""

    id: UUID = Field(..., description="Eindeutige Benutzer-ID")
    password: str = Field(..., description="Gehashtes Passwort")
    is_superuser: bool = Field(False, description="Superuser-Status")
    role: UserRole = Field(UserRole.user, description="Rolle des Benutzers")
    created_at: datetime = Field(..., description="Erstellungsdatum")
    updated_at: datetime = Field(..., description="Letztes Update")
    last_login: Optional[datetime] = Field(None, description="Letzter Login")

    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    """Pydantic-Modell für öffentliche Benutzerinformationen."""

    id: UUID = Field(..., serialization_alias="uuid", alias="uuid", description="Eindeutige Benutzer-ID")
    created_at: datetime = Field(..., description="Erstellungsdatum")
    is_superuser: bool = Field(False, description="Superuser-Status")
    role: UserRole = Field(User, description="Rolle des Benutzers")
    department: Optional[str] = Field(None, description="Abteilung")
    login: str = Field(None, description="Login (E-Mail-Adresse) des Benutzers")
    email: Optional[EmailStr] = Field(None, description="E-Mail-Adresse des Benutzers", exclude=False)
    first_name: Optional[str] = Field(None, description="Vorname des Benutzers")
    last_name: Optional[str] = Field(None, description="Nachname des Benutzers")
    full_name: Optional[str] = Field(None, description="Voller Name des Benutzers", exclude=False)
    language: Language = Field(Language.de, description="Bevorzugte Sprache des Benutzers")
    two_fa_enabled: bool = Field(False, description="2FA-Status")
    machines: list[str] = Field([], description="Liste der zugeordneten Maschinen")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode='after')
    def populate_derived_fields(self) -> 'UserPublic':
        if self.email and not self.login:
            self.login = self.email
        if self.full_name and not (self.first_name or self.last_name):
            parts = self.full_name.strip().split(' ', 1)
            self.first_name = parts[0] if parts else None
            self.last_name = parts[1] if len(parts) > 1 else None
        return self


class UserCreate(UserPublic):
    """Pydantic-Modell für die Benutzererstellung."""
    password: str = Field(..., min_length=8, description="Passwort (mindestens 8 Zeichen)")


class UsersPublic(BaseModel):
    """Pydantic-Modell für eine Liste von öffentlichen Benutzern."""

    data: list[UserPublic] = Field(..., description="Liste der Benutzer")
    count: int = Field(..., description="Anzahl der Benutzer")


