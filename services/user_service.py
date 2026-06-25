"""
Database User Service - Datenbankbasierte Benutzerverwaltung.

Diese Klasse implementiert die Benutzerverwaltung über SQLAlchemy und Datenbank.
Sie erbt von BaseUserService und stellt eine konkrete Implementierung für
datenbankbasierte Benutzerspeicherung bereit.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models.user_models import User, UserCreate, UserUpdate, UserUpdateMe, UpdatePassword
from ..utils.security import SecurityUtils
from .base_user_service import BaseUserService


class DatabaseUserService(BaseUserService):
    """
    Datenbankbasierte Implementierung des UserService.

    Diese Klasse stellt alle benutzerbezogenen Operationen über SQLAlchemy
    und eine relationale Datenbank bereit.
    """

    def __init__(self, db_session: Session, config: Any = None):
        """
        Initialisiert den DatabaseUserService.

        Args:
            db_session: SQLAlchemy Session für Datenbankoperationen
            config: Konfigurationsobjekt
        """
        super().__init__(config, "database")
        self.db = db_session
        self.security = SecurityUtils()

    def _normalize_user_id(self, user_id: UUID | str) -> UUID | str:
        """Normalize user IDs to the SQL type of User.id (UUID or String)."""
        try:
            id_python_type = User.id.type.python_type
        except Exception:
            id_python_type = str

        if id_python_type is str:
            return str(user_id)

        if id_python_type is UUID and isinstance(user_id, str):
            return UUID(user_id)

        return user_id

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Holt einen Benutzer anhand seiner ID.

        Args:
            user_id: Die eindeutige Benutzer-ID

        Returns:
            User-Objekt wenn gefunden, None andernfalls
        """
        normalized_user_id = self._normalize_user_id(user_id)
        return self.db.query(User).filter(User.id == normalized_user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Holt einen Benutzer anhand seiner E-Mail-Adresse.

        Args:
            email: Die E-Mail-Adresse

        Returns:
            User-Objekt wenn gefunden, None andernfalls
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_external_id(self, external_id: str, provider: str) -> Optional[User]:
        """
        Holt einen Benutzer anhand einer externen ID.

        Für DatabaseUserService wird dies über ein externes Mapping implementiert
        oder als Not-Implemented behandelt, je nach Datenbankschema.

        Args:
            external_id: Externe Benutzer-ID
            provider: Name des externen Providers

        Returns:
            User-Objekt wenn gefunden, None andernfalls
        """
        # TODO: Implementierung abhängig vom Datenbankschema
        # Könnte über eine separate Tabelle für externe Verknüpfungen erfolgen
        return None

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[User], int]:
        """
        Holt eine Liste von Benutzern mit optionaler Filterung.

        Args:
            skip: Anzahl zu überspringender Datensätze
            limit: Maximale Anzahl zurückzugebender Datensätze
            search: Suchbegriff für E-Mail oder Name
            is_active: Filter für aktive Benutzer
            is_superuser: Filter für Superuser

        Returns:
            Tuple aus (Liste der Benutzer, Gesamtanzahl)
        """
        query = self.db.query(User)

        # Filter anwenden
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if is_superuser is not None:
            query = query.filter(User.is_superuser == is_superuser)

        # Gesamtanzahl für Paginierung
        total_count = query.count()

        # Paginierung anwenden
        users = query.offset(skip).limit(limit).all()

        return users, total_count

    def create_user(self, user_create: UserCreate) -> User:
        """
        Erstellt einen neuen Benutzer.

        Args:
            user_create: Benutzerdaten für die Erstellung

        Returns:
            Der erstellte Benutzer

        Raises:
            ValueError: Wenn E-Mail bereits existiert
        """
        # Prüfen, ob E-Mail bereits existiert
        existing_user = self.get_user_by_email(user_create.email)
        if existing_user:
            raise ValueError("E-Mail-Adresse bereits registriert")

        # Passwort hashen
        hashed_password = self.security.get_password_hash(user_create.password)

        # Benutzer erstellen
        db_user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            is_active=user_create.is_active,
            is_superuser=user_create.is_superuser
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """
        Aktualisiert einen Benutzer (Admin-Funktion).

        Args:
            user_id: ID des zu aktualisierenden Benutzers
            user_update: Aktualisierungsdaten

        Returns:
            Der aktualisierte Benutzer oder None wenn nicht gefunden

        Raises:
            ValueError: Wenn E-Mail bereits von anderem Benutzer verwendet wird
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        # Prüfen, ob neue E-Mail bereits existiert
        if user_update.email and user_update.email != db_user.email:
            existing_user = self.get_user_by_email(user_update.email)
            if existing_user:
                raise ValueError("E-Mail-Adresse bereits von anderem Benutzer verwendet")

        # Felder aktualisieren
        update_data = user_update.model_dump(exclude_unset=True)

        # Passwort hashen, falls vorhanden
        if "password" in update_data:
            hashed_password = self.security.get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]

        for field, value in update_data.items():
            setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def update_user_me(self, user_id: UUID, user_update: UserUpdateMe) -> Optional[User]:
        """
        Aktualisiert eigene Benutzerdaten.

        Args:
            user_id: ID des aktuellen Benutzers
            user_update: Aktualisierungsdaten

        Returns:
            Der aktualisierte Benutzer oder None wenn nicht gefunden

        Raises:
            ValueError: Wenn E-Mail bereits von anderem Benutzer verwendet wird
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        # Prüfen, ob neue E-Mail bereits existiert
        if user_update.email and user_update.email != db_user.email:
            existing_user = self.get_user_by_email(user_update.email)
            if existing_user:
                raise ValueError("E-Mail-Adresse bereits von anderem Benutzer verwendet")

        # Felder aktualisieren
        update_data = user_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def update_password(self, user_id: UUID, password_update: UpdatePassword) -> bool:
        """
        Aktualisiert das Passwort eines Benutzers.

        Args:
            user_id: ID des Benutzers
            password_update: Passwort-Aktualisierungsdaten

        Returns:
            True wenn erfolgreich, False andernfalls

        Raises:
            ValueError: Wenn aktuelles Passwort falsch ist
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return False

        # Aktuelles Passwort prüfen
        if not self.security.verify_password(
            password_update.current_password,
            db_user.hashed_password
        ):
            raise ValueError("Aktuelles Passwort ist falsch")

        # Neues Passwort hashen und speichern
        hashed_password = self.security.get_password_hash(password_update.new_password)
        db_user.hashed_password = hashed_password

        self.db.commit()
        return True

    def delete_user(self, user_id: UUID) -> bool:
        """
        Löscht einen Benutzer.

        Args:
            user_id: ID des zu löschenden Benutzers

        Returns:
            True wenn erfolgreich gelöscht, False wenn nicht gefunden
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deaktiviert einen Benutzer.

        Args:
            user_id: ID des zu deaktivierenden Benutzers

        Returns:
            Der deaktivierte Benutzer oder None wenn nicht gefunden
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        db_user.is_active = False
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Aktiviert einen Benutzer.

        Args:
            user_id: ID des zu aktivierenden Benutzers

        Returns:
            Der aktivierte Benutzer oder None wenn nicht gefunden
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        db_user.is_active = True
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def is_email_available(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Prüft, ob eine E-Mail-Adresse verfügbar ist.

        Args:
            email: Die zu prüfende E-Mail-Adresse
            exclude_user_id: Benutzer-ID, die ausgeschlossen werden soll

        Returns:
            True wenn verfügbar, False wenn bereits verwendet
        """
        query = self.db.query(User).filter(User.email == email)

        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)

        return query.first() is None

    def supports_operation(self, operation: str) -> bool:
        """
        Prüft, ob eine bestimmte Operation unterstützt wird.

        DatabaseUserService unterstützt alle Standard-Operationen.

        Args:
            operation: Name der Operation

        Returns:
            True für alle Standard-Operationen
        """
        supported_ops = ["create", "update", "delete", "password_update", "activate", "deactivate"]
        return operation in supported_ops

    def link_external_account(self, user_id: UUID, external_id: str, provider: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verknüpft ein externes Konto mit einem Benutzer.

        Für eine vollständige Implementierung würde hier eine separate Tabelle
        für externe Account-Verknüpfungen verwendet werden.

        Args:
            user_id: Interne Benutzer-ID
            external_id: Externe ID
            provider: Name des externen Providers
            metadata: Zusätzliche Metadaten

        Returns:
            True wenn erfolgreich verknüpft
        """
        # TODO: Implementierung einer external_accounts Tabelle
        # Beispiel-Schema:
        # CREATE TABLE user_external_accounts (
        #     user_id UUID REFERENCES users(id),
        #     external_id VARCHAR NOT NULL,
        #     provider VARCHAR NOT NULL,
        #     metadata JSONB,
        #     created_at TIMESTAMP DEFAULT NOW(),
        #     PRIMARY KEY (user_id, provider)
        # );
        return False

    def unlink_external_account(self, user_id: UUID, provider: str) -> bool:
        """
        Entfernt die Verknüpfung zu einem externen Konto.

        Args:
            user_id: Interne Benutzer-ID
            provider: Name des externen Providers

        Returns:
            True wenn erfolgreich entfernt
        """
        # TODO: Implementierung basierend auf external_accounts Tabelle
        return False


# Alias für Rückwärtskompatibilität
UserService = DatabaseUserService
