"""Factory und Konfiguration für ORM-Modelle des Auth-Moduls.

Die ORM-Klassen dieses Pakets können gegen eine anwendungsspezifische
SQLAlchemy-Base mit optionalem Tabellenpräfix erzeugt werden. Das ist vor allem
für Anwendungen nützlich, die externe Paketmodelle in eine gemeinsame
`Base.metadata` registrieren und dabei Namenskollisionen vermeiden möchten.

Über die Parameter ``user_mixins``, ``user_attrs_override`` und
``user_class_name`` in :func:`create_auth_models` lässt sich das generierte
User-Modell nahtlos mit anwendungsspezifischen Feldern und Relationships
zusammenführen (Mixin-Mechanismus).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship


@dataclass(frozen=True)
class AuthORMModels:
    """Bundle der erzeugten ORM-Klassen und ihrer Tabellennamen."""

    User: type[Any]
    Group: type[Any]
    UserGroupMembership: type[Any]
    UserSession: type[Any]
    table_prefix: str
    user_table_name: str
    group_table_name: str
    membership_table_name: str
    session_table_name: str


def _normalize_prefix(table_prefix: str | None) -> str:
    return table_prefix or ""


def _class_name_suffix(table_prefix: str) -> str:
    suffix = re.sub(r"\W+", "_", table_prefix).strip("_")
    return suffix or "default"


def _cache_for_base(base: type[Any]) -> dict[Any, AuthORMModels]:
    metadata = getattr(base, "metadata")
    return metadata.info.setdefault("_fastapi_users_auth_model_cache", {})


def _mixin_cache_key(user_mixins: list[type] | None) -> tuple[int, ...]:
    """Erzeuge einen Hash-stabilen Cache-Schlüssel aus den Mixin-Identitäten."""
    if not user_mixins:
        return ()
    return tuple(id(m) for m in user_mixins)


def _patch_module(module_name: str, **updates: Any) -> None:
    module = sys.modules.get(module_name)
    if module is None:
        return
    for attribute_name, value in updates.items():
        setattr(module, attribute_name, value)


def create_auth_models(
    base: type[Any],
    table_prefix: str = "",
    user_mixins: list[type] | None = None,
    user_attrs_override: dict[str, Any] | None = None,
    user_class_name: str | None = None,
) -> AuthORMModels:
    """Erzeugt User-/Group-/Membership-ORM-Modelle für eine gegebene Base.

    Args:
        base: Declarative Base bzw. abgeleitete Basisklasse der Anwendung.
        table_prefix: Optionales Präfix für alle Auth-Tabellen, z. B. ``"auth_"``.
        user_mixins: Optionale Liste von SQLAlchemy-Mixin-Klassen (plain Python,
            KEIN ``Base``-Erbe), die in die Basisklassen-Tuple des generierten
            User-Modells aufgenommen werden. Damit lassen sich anwendungs-
            spezifische Spalten und ``declared_attr``-Relationships einmischen,
            ohne die generische Auth-Logik zu verändern. Beispiel::

                from myapp.database.user_mixin import AppUserMixin
                auth = create_auth_models(Base, table_prefix="myapp_",
                                          user_mixins=[AppUserMixin])

        user_attrs_override: Optionales Dict, dessen Einträge die Standard-
            Spalten/-Attribute des generierten User-Modells **überschreiben**.
            Damit lässt sich z. B. der Typ der ``id``-Spalte oder der Name
            des Login-Felds anpassen::

                user_attrs_override = {
                    "id": Column(Integer, primary_key=True, autoincrement=True),
                }

        user_class_name: Optionaler Python-Klassenname für das generierte
            User-Modell (Standard: ``"AuthUser_{suffix}"``). Wichtig, wenn
            andere SQLAlchemy-Modelle via String-Referenz auf ``"User"``
            verweisen, z. B. ``relationship("User", ...)``.

    Returns:
        Ein Bundle mit den erzeugten ORM-Klassen.
    """

    normalized_prefix = _normalize_prefix(table_prefix)
    cache_key: Any = (normalized_prefix, _mixin_cache_key(user_mixins))
    base_cache = _cache_for_base(base)
    cached_models = base_cache.get(cache_key)
    if cached_models is not None:
        return cached_models

    class_suffix = _class_name_suffix(normalized_prefix)
    user_table_name = f"{normalized_prefix}users"
    group_table_name = f"{normalized_prefix}groups"
    membership_table_name = f"{normalized_prefix}user_group_memberships"
    membership_constraint_name = f"uq_{membership_table_name}_user_group"
    session_table_name = f"{normalized_prefix}user_sessions"

    user_attrs: dict[str, Any] = {
        "__module__": __name__,
        "__tablename__": user_table_name,
        "id": Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())),
        # "uuid": Column(String(36), primary_key=False, index=False, default=lambda: str(uuid.uuid4())),
        "email": Column(String(255), unique=True, nullable=False, index=True),
        "hashed_password": Column(String(255), nullable=False),
        "is_active": Column(Boolean, default=True, nullable=False),
        "is_superuser": Column(Boolean, default=False, nullable=False),
        "full_name": Column(String(255), nullable=True),
        "department": Column(String(255), nullable=True),
        "language": Column(String(10), nullable=False, default="de"),
        "two_fa_enabled": Column(Boolean, default=False, nullable=False),
        "created_at": Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
        "updated_at": Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        ),
        "last_login": Column(DateTime(timezone=True), nullable=True),
    }

    # Anwendungsspezifische Überschreibungen einmischen (höchste Priorität)
    if user_attrs_override:
        user_attrs.update(user_attrs_override)

    # Basisklassen-Tuple aufbauen: Base + optionale Mixins
    user_base_classes: tuple[type, ...] = (base, *user_mixins) if user_mixins else (base,)

    # Klassenname: explizit übergeben oder aus Präfix-Suffix ableiten
    effective_class_name = user_class_name or f"AuthUser_{class_suffix}"

    User = type(effective_class_name, user_base_classes, user_attrs)

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

    # -----------------------------------------------------------------------
    # UserSession – anwendungsunabhängiges Session-Modell
    #
    # FK: user_id → users.id
    # login_source: Plain String(16); der Wert wird von der Anwendung gesetzt
    #               (z. B. "backend", "frontend", "unknown").
    # -----------------------------------------------------------------------
    session_attrs = {
        "__module__": __name__,
        "__tablename__": session_table_name,
        "id": Column(Integer, primary_key=True, index=True, autoincrement=True),
        "user_id": Column(
            String(36),
            ForeignKey(f"{user_table_name}.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        "session_id": Column(
            String,
            unique=True,
            nullable=False,
            index=True,
            default=lambda: str(uuid.uuid4()),
        ),
        "login_source": Column(String(16), nullable=False, default="unknown", index=True),
        "valid_until": Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    }
    UserSession = type(f"AuthUserSession_{class_suffix}", (base,), session_attrs)

    # Bidirektionale Relationship User ↔ UserSession
    User.sessions = relationship(
        UserSession,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    UserSession.user = relationship(
        User,
        back_populates="sessions",
    )

    bundle = AuthORMModels(
        User=User,
        Group=Group,
        UserGroupMembership=UserGroupMembership,
        UserSession=UserSession,
        table_prefix=normalized_prefix,
        user_table_name=user_table_name,
        group_table_name=group_table_name,
        membership_table_name=membership_table_name,
        session_table_name=session_table_name,
    )
    base_cache[cache_key] = bundle
    return bundle


def configure_auth_models(
    base: type[Any],
    table_prefix: str = "",
    user_mixins: list[type] | None = None,
    user_attrs_override: dict[str, Any] | None = None,
    user_class_name: str | None = None,
) -> AuthORMModels:
    """Konfiguriert die öffentlichen ORM-Aliasse des Pakets für Base + Präfix.

    Diese Funktion sollte früh in der Anwendung aufgerufen werden, bevor Services,
    Dependencies oder Router aus dem Paket importiert werden. So verwenden sowohl
    die App als auch das Paket dieselben ORM-Klassen.

    Die Parameter ``user_mixins``, ``user_attrs_override`` und ``user_class_name``
    werden direkt an :func:`create_auth_models` weitergegeben. Siehe dort für
    die vollständige Dokumentation.
    """

    bundle = create_auth_models(
        base,
        table_prefix=table_prefix,
        user_mixins=user_mixins,
        user_attrs_override=user_attrs_override,
        user_class_name=user_class_name,
    )

    module_updates = {
        "User": bundle.User,
        "Group": bundle.Group,
        "UserGroupMembership": bundle.UserGroupMembership,
        "UserSession": bundle.UserSession,
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

