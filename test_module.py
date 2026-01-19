"""
Test-Script zur Überprüfung der fastapi_users_auth Modul-Integration.

Dieses Script testet die grundlegende Funktionalität des Moduls
und zeigt, wie es verwendet werden kann.
"""

import sys
import os
from pathlib import Path

# Pfad zum Backend-Verzeichnis hinzufügen
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def test_imports():
    """Testet, ob alle Module korrekt importiert werden können."""
    print("🔍 Teste Imports...")

    try:
        # Hauptmodul-Import
        from users_auth import UserAuthModule
        print("✅ UserAuthModule erfolgreich importiert")

        # Model-Imports
        from users_auth.models import User, UserCreate, Token, Message
        print("✅ Modelle erfolgreich importiert")

        # Service-Imports
        from users_auth.services import AuthService, UserService
        print("✅ Services erfolgreich importiert")

        # Utils-Imports
        from users_auth.utils import SecurityUtils, TokenUtils
        print("✅ Utils erfolgreich importiert")

        # Dependencies-Imports
        from users_auth.dependencies import AuthDependencies
        print("✅ Dependencies erfolgreich importiert")

        # Router-Imports
        from users_auth.routers import create_auth_router, create_user_router
        print("✅ Router erfolgreich importiert")

        return True

    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False

def test_security_utils():
    """Testet die SecurityUtils-Funktionalität."""
    print("\n🔐 Teste SecurityUtils...")

    try:
        from users_auth.utils import SecurityUtils

        security = SecurityUtils()

        # Passwort hashen
        password = "TestPassword123!"
        hashed = security.get_password_hash(password)
        print(f"✅ Passwort gehasht: {hashed[:20]}...")

        # Passwort verifizieren
        is_valid = security.verify_password(password, hashed)
        print(f"✅ Passwort-Verifikation: {is_valid}")

        # Passwort-Stärke prüfen
        is_strong, issues = security.is_password_strong(password)
        print(f"✅ Passwort-Stärke: {is_strong}, Probleme: {len(issues)}")

        # Sicheres Passwort generieren
        generated = security.generate_password(16)
        print(f"✅ Generiertes Passwort: {generated}")

        return True

    except Exception as e:
        print(f"❌ SecurityUtils-Fehler: {e}")
        return False

def test_token_utils():
    """Testet die TokenUtils-Funktionalität."""
    print("\n🎫 Teste TokenUtils...")

    try:
        from users_auth.utils import TokenUtils
        from datetime import timedelta

        secret_key = "test-secret-key-for-testing-only"
        token_utils = TokenUtils(secret_key)

        # Token erstellen
        user_id = "12345"
        token = token_utils.create_access_token(
            subject=user_id,
            expires_delta=timedelta(minutes=30)
        )
        print(f"✅ Token erstellt: {token[:20]}...")

        # Token verifizieren
        payload = token_utils.verify_token(token)
        print(f"✅ Token verifiziert: {payload.sub if payload else 'Ungültig'}")

        # Passwort-Reset-Token
        reset_token = token_utils.create_password_reset_token("test@example.com")
        print(f"✅ Reset-Token erstellt: {reset_token[:20]}...")

        # Reset-Token verifizieren
        email = token_utils.verify_password_reset_token(reset_token)
        print(f"✅ Reset-Token verifiziert für: {email}")

        return True

    except Exception as e:
        print(f"❌ TokenUtils-Fehler: {e}")
        return False

def test_models():
    """Testet die Pydantic-Modelle."""
    print("\n📋 Teste Modelle...")

    try:
        from users_auth.models import UserCreate, UserPublic, Token, Message

        # UserCreate-Modell testen
        user_data = UserCreate(
            email="test@example.com",
            password="TestPassword123!",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        print(f"✅ UserCreate-Modell: {user_data.email}")

        # Token-Modell testen
        token_data = Token(
            access_token="test-token",
            token_type="bearer",
            expires_in=1800
        )
        print(f"✅ Token-Modell: {token_data.token_type}")

        # Message-Modell testen
        message = Message(
            message="Test erfolgreich",
            success=True
        )
        print(f"✅ Message-Modell: {message.message}")

        return True

    except Exception as e:
        print(f"❌ Modell-Fehler: {e}")
        return False

def show_module_structure():
    """Zeigt die Struktur des erstellten Moduls."""
    print("\n📁 Modul-Struktur:")

    users_auth_path = Path(__file__).parent

    for root, dirs, files in os.walk(users_auth_path):
        level = root.replace(str(users_auth_path), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")

        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                print(f"{sub_indent}{file}")

def main():
    """Hauptfunktion zum Ausführen aller Tests."""
    print("🚀 Teste fastapi_users_auth Modul\n")

    # Struktur anzeigen
    show_module_structure()

    # Tests ausführen
    tests = [
        test_imports,
        test_models,
        test_security_utils,
        test_token_utils
    ]

    results = []
    for test in tests:
        results.append(test())

    # Ergebnisse zusammenfassen
    print(f"\n📊 Test-Ergebnisse: {sum(results)}/{len(results)} erfolgreich")

    if all(results):
        print("✅ Alle Tests erfolgreich! Das fastapi_users_auth Modul ist einsatzbereit.")
        print("\n📖 Nächste Schritte:")
        print("1. Schauen Sie sich die README_authentication_multi.md für Integrations-Beispiele an")
        print("2. Prüfen Sie examples/integration_example.py")
        print("3. Integrieren Sie das Modul in Ihre FastAPI-App")
    else:
        print("❌ Einige Tests fehlgeschlagen. Bitte prüfen Sie die Fehlermeldungen.")

if __name__ == "__main__":
    main()
