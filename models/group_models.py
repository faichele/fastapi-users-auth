"""
Modelle für Benutzer-Gruppen und Gruppenmitgliedschaften.

Dieses Modul ergänzt das Auth-Paket um:
- SQLAlchemy-Modelle für Gruppen und Mitgliedschaften
- Pydantic-Modelle für API-Request/Response-Schemas
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shared_orm import Base
from ..model_factory import create_auth_models

_DEFAULT_AUTH_MODELS = create_auth_models(Base)
Group = _DEFAULT_AUTH_MODELS.Group
UserGroupMembership = _DEFAULT_AUTH_MODELS.UserGroupMembership


class GroupBase(BaseModel):
    """Basis-Pydantic-Modell für Gruppen."""

    name: str = Field(..., min_length=1, max_length=255, description="Name der Gruppe")
    description: Optional[str] = Field(None, description="Optionale Beschreibung der Gruppe")
    is_active: bool = Field(True, description="Ob die Gruppe aktiv ist")


class GroupCreate(GroupBase):
    """Pydantic-Modell zum Erstellen einer Gruppe."""


class GroupUpdate(BaseModel):
    """Pydantic-Modell zum Aktualisieren einer Gruppe."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Neuer Name der Gruppe")
    description: Optional[str] = Field(None, description="Neue Beschreibung der Gruppe")
    is_active: Optional[bool] = Field(None, description="Aktiv-Status der Gruppe")


class GroupInDB(GroupBase):
    """Pydantic-Modell für Gruppen mit Datenbankfeldern."""

    id: UUID = Field(..., description="Eindeutige Gruppen-ID")
    created_at: datetime = Field(..., description="Erstellungsdatum")
    updated_at: datetime = Field(..., description="Letztes Update")

    model_config = ConfigDict(from_attributes=True)


class GroupPublic(GroupBase):
    """Pydantic-Modell für öffentliche Gruppeninformationen."""

    id: UUID = Field(..., description="Eindeutige Gruppen-ID")
    created_at: datetime = Field(..., description="Erstellungsdatum")

    model_config = ConfigDict(from_attributes=True)


class GroupsPublic(BaseModel):
    """Pydantic-Modell für eine Liste von Gruppen."""

    data: list[GroupPublic] = Field(..., description="Liste der Gruppen")
    count: int = Field(..., description="Anzahl der Gruppen")


class UserGroupMembershipBase(BaseModel):
    """Basis-Pydantic-Modell für Gruppenmitgliedschaften."""

    role: str = Field("member", min_length=1, max_length=50, description="Rolle des Benutzers in der Gruppe")


class UserGroupMembershipCreate(UserGroupMembershipBase):
    """Pydantic-Modell zum Erstellen einer Gruppenmitgliedschaft."""

    user_id: UUID = Field(..., description="Benutzer-ID")
    group_id: UUID = Field(..., description="Gruppen-ID")


class UserGroupMembershipUpdate(BaseModel):
    """Pydantic-Modell zum Aktualisieren einer Gruppenmitgliedschaft."""

    role: Optional[str] = Field(None, min_length=1, max_length=50, description="Neue Rolle des Benutzers in der Gruppe")


class UserGroupMembershipInDB(UserGroupMembershipBase):
    """Pydantic-Modell für Gruppenmitgliedschaften mit Datenbankfeldern."""

    id: UUID = Field(..., description="Eindeutige Mitgliedschafts-ID")
    user_id: UUID = Field(..., description="Benutzer-ID")
    group_id: UUID = Field(..., description="Gruppen-ID")
    created_at: datetime = Field(..., description="Erstellungsdatum")
    updated_at: datetime = Field(..., description="Letztes Update")

    model_config = ConfigDict(from_attributes=True)


class UserGroupMembershipPublic(UserGroupMembershipBase):
    """Pydantic-Modell für öffentliche Gruppenmitgliedschaften."""

    id: UUID = Field(..., description="Eindeutige Mitgliedschafts-ID")
    user_id: UUID = Field(..., description="Benutzer-ID")
    group_id: UUID = Field(..., description="Gruppen-ID")
    created_at: datetime = Field(..., description="Erstellungsdatum")

    model_config = ConfigDict(from_attributes=True)


class UserGroupMembershipsPublic(BaseModel):
    """Pydantic-Modell für eine Liste von Gruppenmitgliedschaften."""

    data: list[UserGroupMembershipPublic] = Field(..., description="Liste der Gruppenmitgliedschaften")
    count: int = Field(..., description="Anzahl der Gruppenmitgliedschaften")


__all__ = [
    "Group",
    "UserGroupMembership",
    "GroupBase",
    "GroupCreate",
    "GroupUpdate",
    "GroupInDB",
    "GroupPublic",
    "GroupsPublic",
    "UserGroupMembershipBase",
    "UserGroupMembershipCreate",
    "UserGroupMembershipUpdate",
    "UserGroupMembershipInDB",
    "UserGroupMembershipPublic",
    "UserGroupMembershipsPublic",
]

