"""
Abstrakte Basis-Klasse für Benutzer-Services.

Diese Klasse definiert die Schnittstelle für alle Benutzerverwaltungsanbieter
und ermöglicht die Implementierung verschiedener User-Storage-Strategien.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..models.user_models import User, UserCreate, UserUpdate, UserUpdateMe, UpdatePassword


class BaseUserService(ABC):
    """
    Abstrakte Basis-Klasse für Benutzer-Services.

    Definiert die gemeinsame Schnittstelle für alle Benutzerverwaltungsanbieter
    wie Database, LDAP, External APIs, etc.
    """

    def __init__(self, config: Any, provider_name: str):
        """
        Initialisiert den BaseUserService.

        Args:
            config: Konfigurationsobjekt
            provider_name: Name des User-Providers (z.B. "database", "ldap", "api")
        """
        self.config = config
        self.provider_name = provider_name

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Holt einen Benutzer anhand seiner ID.

        Args:
            user_id: Die eindeutige Benutzer-ID

        Returns:
            User-Objekt wenn gefunden, None andernfalls
        """
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Holt einen Benutzer anhand seiner E-Mail-Adresse.

        Args:
            email: Die E-Mail-Adresse

        Returns:
            User-Objekt wenn gefunden, None andernfalls
        """
        pass

    @abstractmethod
    def get_user_by_external_id(self, external_id: str, provider: str) -> Optional[User]:
        """
        Holt einen Benutzer anhand einer externen ID.

        Args:
            external_id: Externe Benutzer-ID (z.B. OAuth Provider ID)
            provider: Name des externen Providers

        Returns:
            User-Objekt wenn gefunden, None andernfalls
        """
        pass

    @abstractmethod
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
            filters: Zusätzliche Provider-spezifische Filter

        Returns:
            Tuple aus (Liste der Benutzer, Gesamtanzahl)
        """
        pass

    @abstractmethod
    def create_user(self, user_create: UserCreate) -> User:
        """
        Erstellt einen neuen Benutzer.

        Args:
            user_create: Benutzerdaten für die Erstellung

        Returns:
            Der erstellte Benutzer

        Raises:
            ValueError: Wenn E-Mail bereits existiert oder andere Validierungsfehler
            NotImplementedError: Wenn Provider keine Benutzererstellung unterstützt
        """
        pass

    @abstractmethod
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
            NotImplementedError: Wenn Provider keine Updates unterstützt
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
            NotImplementedError: Wenn Provider keine Passwort-Updates unterstützt
        """
        pass

    @abstractmethod
    def delete_user(self, user_id: UUID) -> bool:
        """
        Löscht einen Benutzer.

        Args:
            user_id: ID des zu löschenden Benutzers

        Returns:
            True wenn erfolgreich gelöscht, False wenn nicht gefunden

        Raises:
            NotImplementedError: Wenn Provider keine Löschung unterstützt
        """
        pass

    @abstractmethod
    def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Aktiviert einen Benutzer.

        Args:
            user_id: ID des zu aktivierenden Benutzers

        Returns:
            Der aktivierte Benutzer oder None wenn nicht gefunden
        """
        pass

    @abstractmethod
    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deaktiviert einen Benutzer.

        Args:
            user_id: ID des zu deaktivierenden Benutzers

        Returns:
            Der deaktivierte Benutzer oder None wenn nicht gefunden
        """
        pass

    @abstractmethod
    def is_email_available(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Prüft, ob eine E-Mail-Adresse verfügbar ist.

        Args:
            email: Die zu prüfende E-Mail-Adresse
            exclude_user_id: Benutzer-ID, die ausgeschlossen werden soll

        Returns:
            True wenn verfügbar, False wenn bereits verwendet
        """
        pass

    def get_provider_name(self) -> str:
        """
        Gibt den Namen des User-Providers zurück.

        Returns:
            Provider-Name
        """
        return self.provider_name

    def supports_operation(self, operation: str) -> bool:
        """
        Prüft, ob eine bestimmte Operation unterstützt wird.

        Args:
            operation: Name der Operation ("create", "update", "delete", "password_update")

        Returns:
            True wenn unterstützt
        """
        # Standard-Implementierung: alle Operationen unterstützt
        return True

    def get_user_metadata(self, user_id: UUID) -> Dict[str, Any]:
        """
        Holt zusätzliche Metadaten für einen Benutzer.

        Args:
            user_id: Benutzer-ID

        Returns:
            Dictionary mit Metadaten
        """
        return {}  # Standard: keine zusätzlichen Metadaten

    def link_external_account(self, user_id: UUID, external_id: str, provider: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verknüpft ein externes Konto mit einem Benutzer.

        Args:
            user_id: Interne Benutzer-ID
            external_id: Externe ID
            provider: Name des externen Providers
            metadata: Zusätzliche Metadaten

        Returns:
            True wenn erfolgreich verknüpft
        """
        # Standard-Implementierung: nicht unterstützt
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
        # Standard-Implementierung: nicht unterstützt
        return False
