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

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

# SQLAlchemy-ORM-Modelle werden per configure_auth_models in dieses Modul
# gepacht – Platzhalter damit Import-Prüftools (mypy, IDE) nicht warnen.
User: type = None  # type: ignore[assignment]
UserSession: type = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Pydantic Base Models
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    """Basis-Pydantic-Modell für Benutzer."""

    email: EmailStr = Field(..., description="E-Mail-Adresse des Benutzers")
    full_name: Optional[str] = Field(None, description="Vollständiger Name des Benutzers")
    is_active: bool = Field(True, description="Ob der Benutzer aktiv ist")


class UserCreate(UserBase):
    """Pydantic-Modell für die Benutzererstellung."""

    password: str = Field(..., min_length=8, description="Passwort (mindestens 8 Zeichen)")
    is_superuser: bool = Field(False, description="Ob der Benutzer Superuser-Rechte hat")


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
    created_at: datetime = Field(..., description="Erstellungsdatum")
    updated_at: datetime = Field(..., description="Letztes Update")
    last_login: Optional[datetime] = Field(None, description="Letzter Login")

    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    """Pydantic-Modell für öffentliche Benutzerinformationen."""

    id: UUID = Field(..., description="Eindeutige Benutzer-ID")
    created_at: datetime = Field(..., description="Erstellungsdatum")

    model_config = ConfigDict(from_attributes=True)


class UsersPublic(BaseModel):
    """Pydantic-Modell für eine Liste von öffentlichen Benutzern."""

    data: list[UserPublic] = Field(..., description="Liste der Benutzer")
    count: int = Field(..., description="Anzahl der Benutzer")


