"""Factory und Konfiguration für ORM-Modelle des Auth-Moduls.

Die ORM-Klassen dieses Pakets können gegen eine anwendungsspezifische
SQLAlchemy-Base mit optionalem Tabellenpräfix erzeugt werden. Das ist vor allem
für Anwendungen nützlich, die externe Paketmodelle in eine gemeinsame
`Base.metadata` registrieren und dabei Namenskollisionen vermeiden möchten.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship


@dataclass(frozen=True)
class AuthORMModels:
    """Bundle der erzeugten ORM-Klassen und ihrer Tabellennamen."""

    User: type[Any]
    Group: type[Any]
    UserGroupMembership: type[Any]
    table_prefix: str
    user_table_name: str
    group_table_name: str
    membership_table_name: str


def _normalize_prefix(table_prefix: str | None) -> str:
    return table_prefix or ""


def _class_name_suffix(table_prefix: str) -> str:
    suffix = re.sub(r"\W+", "_", table_prefix).strip("_")
    return suffix or "default"


def _cache_for_base(base: type[Any]) -> dict[str, AuthORMModels]:
    metadata = getattr(base, "metadata")
    return metadata.info.setdefault("_fastapi_users_auth_model_cache", {})


def _patch_module(module_name: str, **updates: Any) -> None:
    module = sys.modules.get(module_name)
    if module is None:
        return
    for attribute_name, value in updates.items():
        setattr(module, attribute_name, value)


def create_auth_models(base: type[Any], table_prefix: str = "") -> AuthORMModels:
    """Erzeugt User-/Group-/Membership-ORM-Modelle für eine gegebene Base.

    Args:
        base: Declarative Base bzw. abgeleitete Basisklasse der Anwendung.
        table_prefix: Optionales Präfix für alle Auth-Tabellen, z. B. ``"auth_"``.

    Returns:
        Ein Bundle mit den erzeugten ORM-Klassen.
    """

    normalized_prefix = _normalize_prefix(table_prefix)
    base_cache = _cache_for_base(base)
    cached_models = base_cache.get(normalized_prefix)
    if cached_models is not None:
        return cached_models

    class_suffix = _class_name_suffix(normalized_prefix)
    user_table_name = f"{normalized_prefix}users"
    group_table_name = f"{normalized_prefix}groups"
    membership_table_name = f"{normalized_prefix}user_group_memberships"
    membership_constraint_name = f"uq_{membership_table_name}_user_group"

    user_attrs = {
        "__module__": __name__,
        "__tablename__": user_table_name,
        "id": Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())),
        "email": Column(String(255), unique=True, nullable=False, index=True),
        "hashed_password": Column(String(255), nullable=False),
        "is_active": Column(Boolean, default=True, nullable=False),
        "is_superuser": Column(Boolean, default=False, nullable=False),
        "full_name": Column(String(255), nullable=True),
        "created_at": Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
        "updated_at": Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
        "last_login": Column(DateTime(timezone=True), nullable=True),
    }
    User = type(f"AuthUser_{class_suffix}", (base,), user_attrs)

    group_attrs = {
        "__module__": __name__,
        "__tablename__": group_table_name,
        "name": Column(String(255), unique=True, nullable=False, index=True),
        "id": Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())),
        "description": Column(String(1024), nullable=True),
        "is_active": Column(Boolean, default=True, nullable=False),
        "created_at": Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
        "updated_at": Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    }
    Group = type(f"AuthGroup_{class_suffix}", (base,), group_attrs)

    membership_attrs = {
        "__module__": __name__,
        "__tablename__": membership_table_name,
        "__table_args__": (
            UniqueConstraint("user_id", "group_id", name=membership_constraint_name),
        ),
        "id": Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())),
        "user_id": Column(String(36), ForeignKey(f"{user_table_name}.id", ondelete="CASCADE"), nullable=False, index=True),
        "group_id": Column(String(36), ForeignKey(f"{group_table_name}.id", ondelete="CASCADE"), nullable=False, index=True),
        "role": Column(String(50), default="member", nullable=False),
        "created_at": Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
        "updated_at": Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
    }
    UserGroupMembership = type(f"AuthUserGroupMembership_{class_suffix}", (base,), membership_attrs)

    User.group_memberships = relationship(
        UserGroupMembership,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    User.groups = relationship(
        Group,
        secondary=UserGroupMembership.__table__,
        back_populates="users",
        viewonly=True,
        overlaps="group_memberships,memberships,user,group",
    )
    Group.memberships = relationship(
        UserGroupMembership,
        back_populates="group",
        cascade="all, delete-orphan",
        overlaps="groups,group_memberships,user,users",
    )
    Group.users = relationship(
        User,
        secondary=UserGroupMembership.__table__,
        back_populates="groups",
        viewonly=True,
        overlaps="memberships,group_memberships,user,group",
    )
    UserGroupMembership.user = relationship(
        User,
        back_populates="group_memberships",
        overlaps="groups,memberships,group",
    )
    UserGroupMembership.group = relationship(
        Group,
        back_populates="memberships",
        overlaps="groups,group_memberships,user",
    )

    bundle = AuthORMModels(
        User=User,
        Group=Group,
        UserGroupMembership=UserGroupMembership,
        table_prefix=normalized_prefix,
        user_table_name=user_table_name,
        group_table_name=group_table_name,
        membership_table_name=membership_table_name,
    )
    base_cache[normalized_prefix] = bundle
    return bundle


def configure_auth_models(base: type[Any], table_prefix: str = "") -> AuthORMModels:
    """Konfiguriert die öffentlichen ORM-Aliasse des Pakets für Base + Präfix.

    Diese Funktion sollte früh in der Anwendung aufgerufen werden, bevor Services,
    Dependencies oder Router aus dem Paket importiert werden. So verwenden sowohl
    die App als auch das Paket dieselben ORM-Klassen.
    """

    bundle = create_auth_models(base, table_prefix=table_prefix)

    module_updates = {
        "User": bundle.User,
        "Group": bundle.Group,
        "UserGroupMembership": bundle.UserGroupMembership,
    }

    for module_name in (
        "fastapi_users_auth.models.user_models",
        "fastapi_users_auth.models.group_models",
        "fastapi_users_auth.models",
        "fastapi_users_auth.models.users",
        "fastapi_users_auth",
        "packages.fastapi_users_auth.models.user_models",
        "packages.fastapi_users_auth.models.group_models",
        "packages.fastapi_users_auth.models",
        "packages.fastapi_users_auth.models.users",
        "packages.fastapi_users_auth",
    ):
        _patch_module(module_name, **module_updates)

    return bundle


__all__ = ["AuthORMModels", "create_auth_models", "configure_auth_models"]

