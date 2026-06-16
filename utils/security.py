"""
Sicherheits-Utilities für Passwort-Hashing und -Verifikation.

Diese Klasse kapselt alle sicherheitsrelevanten Funktionen:
- Passwort-Hashing mit argon2id
- Passwort-Verifikation für argon2id und bcrypt
- Sichere Passwort-Generierung
"""

import secrets
import string
from typing import Optional

from passlib.context import CryptContext


class SecurityUtils:
    """
    Utility-Klasse für alle sicherheitsrelevanten Operationen.

    Verwendet argon2id für neue Hashes und akzeptiert bcrypt als Legacy-Format.
    Methoden für Passwort-Verifikation und -Generierung bereit.
    """

    def __init__(self, schemes: list[str] = None, deprecated: str = "auto"):
        """
        Initialisiert die SecurityUtils mit konfigurierbaren Hashing-Schemes.

        Args:
            schemes: Liste der zu verwendenden Hashing-Schemes (Standard: ["argon2", "bcrypt"])
            deprecated: Behandlung veralteter Schemes (Standard: "auto")
        """
        if schemes is None:
            schemes = ["argon2", "bcrypt"]

        self.pwd_context = CryptContext(schemes=schemes, deprecated=deprecated)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifiziert ein Klartext-Passwort gegen einen Hash.

        Args:
            plain_password: Das Klartext-Passwort
            hashed_password: Der gehashte Passwort-Hash

        Returns:
            True wenn das Passwort korrekt ist, False andernfalls
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Erstellt einen sicheren Hash für ein Passwort.

        Args:
            password: Das zu hashende Passwort

        Returns:
            Der gehashte Passwort-String
        """
        return self.pwd_context.hash(password)

    def generate_password(self, length: int = 12, include_symbols: bool = True) -> str:
        """
        Generiert ein sicheres zufälliges Passwort.

        Args:
            length: Länge des zu generierenden Passworts (Standard: 12)
            include_symbols: Ob Symbole einbezogen werden sollen (Standard: True)

        Returns:
            Ein sicher generiertes Passwort
        """
        # Basis-Zeichensatz: Buchstaben und Zahlen
        characters = string.ascii_letters + string.digits

        # Symbole hinzufügen, falls gewünscht
        if include_symbols:
            characters += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Sicheres zufälliges Passwort generieren
        password = ''.join(secrets.choice(characters) for _ in range(length))

        return password

    def is_password_strong(self, password: str, min_length: int = 8) -> tuple[bool, list[str]]:
        """
        Überprüft die Stärke eines Passworts.

        Args:
            password: Das zu überprüfende Passwort
            min_length: Mindestlänge (Standard: 8)

        Returns:
            Tuple mit (is_strong, list_of_issues)
        """
        issues = []

        # Länge prüfen
        if len(password) < min_length:
            issues.append(f"Passwort muss mindestens {min_length} Zeichen lang sein")

        # Großbuchstaben prüfen
        if not any(c.isupper() for c in password):
            issues.append("Passwort muss mindestens einen Großbuchstaben enthalten")

        # Kleinbuchstaben prüfen
        if not any(c.islower() for c in password):
            issues.append("Passwort muss mindestens einen Kleinbuchstaben enthalten")

        # Zahlen prüfen
        if not any(c.isdigit() for c in password):
            issues.append("Passwort muss mindestens eine Zahl enthalten")

        # Sonderzeichen prüfen
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("Passwort muss mindestens ein Sonderzeichen enthalten")

        return len(issues) == 0, issues

    def hash_needs_update(self, hashed_password: str) -> bool:
        """
        Überprüft, ob ein Hash aktualisiert werden muss.

        Args:
            hashed_password: Der zu überprüfende Hash

        Returns:
            True wenn der Hash aktualisiert werden sollte, False andernfalls
        """
        return self.pwd_context.needs_update(hashed_password)


# Globale Instanz für einfache Verwendung
security_utils = SecurityUtils()

# Convenience-Funktionen für Rückwärtskompatibilität
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Convenience-Funktion für Passwort-Verifikation."""
    return security_utils.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Convenience-Funktion für Passwort-Hashing."""
    return security_utils.get_password_hash(password)
