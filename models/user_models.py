"""
Pydantic-Modelle für Benutzer-Entitäten.

Diese Modelle definieren die Datenstrukturen für Benutzer in verschiedenen Kontexten:
- Datenbank-Entitäten (SQLAlchemy)
- API-Request/Response-Modelle (Pydantic)
- Interne Datenübertragung
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from shared_orm import Base

from pydantic import BaseModel, EmailStr, Field, ConfigDict

# SQLAlchemy model for user accounts
class User(Base):
    __tablename__ = "users"

    # Falls das Modul in seltenen Fällen doppelt importiert wird (z.B. durch dynamische Imports),
    # verhindert dies einen Crash. Besser ist: Importpfade konsolidieren.
    # TODO: Required?
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)

    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    full_name = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)


# Pydantic Base Models
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
