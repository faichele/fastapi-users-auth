# Users Auth Module

Ein wiederverwendbares Python-Modul für Benutzerverwaltung und Authentifizierung in FastAPI-Anwendungen.

## Überblick

Das `users_auth` Modul bietet eine vollständige, produktionsreife Lösung für:

- **Benutzerverwaltung**: Registrierung, CRUD-Operationen, Profilverwaltung
- **Authentifizierung**: JWT-basierte Anmeldung, Token-Management
- **Autorisierung**: Rollen- und berechtigungsbasierte Zugriffskontrolle
- **Sicherheit**: Sichere Passwort-Hashing, Token-Verifikation
- **Passwort-Reset**: Token-basierte Passwort-Zurücksetzung

## Architektur

Das Modul folgt einer sauberen, schichtweisen Architektur:

```
users_auth/
├── models/              # Pydantic-Modelle und SQLAlchemy-Entitäten
│   ├── user_models.py   # Benutzer-Datenmodelle
│   └── auth_models.py   # Authentifizierungs-Modelle
├── services/            # Business Logic Layer
│   ├── user_service.py  # Benutzer-Geschäftslogik
│   └── auth_service.py  # Authentifizierungs-Logik
├── utils/               # Utility-Funktionen
│   ├── security.py      # Passwort-Hashing und Sicherheit
│   └── token_utils.py   # JWT-Token-Management
├── dependencies/        # FastAPI Dependencies
│   └── auth_deps.py     # Authentifizierungs-Dependencies
├── routers/             # FastAPI Router
│   ├── auth_router.py   # Authentifizierungs-Endpunkte
│   └── user_router.py   # Benutzer-Endpunkte
└── examples/            # Integrations-Beispiele
    └── integration_example.py
```

## Features

### Benutzermodell
- UUID-basierte Benutzer-IDs
- E-Mail als Benutzername
- Sichere Passwort-Speicherung (bcrypt)
- Benutzer-Status (aktiv/inaktiv)
- Rollen-System (normale Benutzer/Superuser)
- Zeitstempel für Erstellung, Updates und letzten Login

### Authentifizierung
- JWT-basierte Access-Token
- OAuth2-kompatible Login-Endpunkte
- Token-Refresh-Mechanismus
- Passwort-Reset mit zeitlich begrenzten Token
- Sichere Token-Verifikation

### API-Endpunkte

#### Authentifizierung (`/auth`)
- `POST /auth/login` - Benutzeranmeldung
- `POST /auth/register` - Benutzerregistrierung
- `POST /auth/logout` - Benutzerabmeldung
- `POST /auth/password-reset/request` - Passwort-Reset anfordern
- `POST /auth/password-reset/confirm` - Passwort-Reset bestätigen
- `POST /auth/refresh` - Token erneuern
- `GET /auth/me` - Aktuelle Benutzerinfo
- `GET /auth/permissions` - Benutzerberechtigungen

#### Benutzerverwaltung (`/users`)
- `GET /users/` - Benutzer auflisten (Admin)
- `POST /users/` - Benutzer erstellen (Admin)
- `GET /users/me` - Eigene Informationen
- `PATCH /users/me` - Eigene Daten aktualisieren
- `PATCH /users/me/password` - Eigenes Passwort ändern
- `GET /users/{id}` - Benutzer nach ID
- `PATCH /users/{id}` - Benutzer aktualisieren (Admin)
- `DELETE /users/{id}` - Benutzer löschen (Admin)
- `PATCH /users/{id}/activate` - Benutzer aktivieren (Admin)
- `PATCH /users/{id}/deactivate` - Benutzer deaktivieren (Admin)

## Installation & Integration

### 1. Einfache Integration (empfohlen)

```python
from fastapi import FastAPI
from users_auth import UserAuthModule

app = FastAPI()

# Authentifizierungsmodul integrieren
auth_module = UserAuthModule(app, database_session, config)
```

### 2. Manuelle Integration

```python
from users_auth.services import AuthService, UserService
from users_auth.dependencies import AuthDependencies
from users_auth.routers import create_auth_router, create_user_router

# Services erstellen
auth_service = AuthService(db_session, config)
user_service = UserService(db_session)

# Dependencies erstellen
auth_deps = AuthDependencies(auth_service, user_service)

# Router erstellen und einbinden
auth_router = create_auth_router(auth_service, auth_deps)
user_router = create_user_router(user_service, auth_deps)

app.include_router(auth_router)
app.include_router(user_router)
```

### 3. Konfiguration

Das Modul benötigt ein Konfigurationsobjekt mit folgenden Attributen:

```python
class Config:
    SECRET_KEY: str                    # JWT-Signierung
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # Token-Gültigkeitsdauer
```

### 4. Datenbank-Setup

```python
from users_auth.models.user_models import User

# Tabellen erstellen (oder mit Alembic migrieren)
User.metadata.create_all(bind=engine)
```

## Verwendung in Routern

### Dependencies verwenden

```python
from fastapi import APIRouter, Depends
from users_auth.dependencies import CurrentUser, CurrentSuperuser

router = APIRouter()

@router.get("/protected")
def protected_route(current_user: CurrentUser):
    return {"user": current_user.email}

@router.get("/admin-only")
def admin_route(current_user: CurrentSuperuser):
    return {"message": "Admin access"}
```

### Services verwenden

```python
from users_auth.services import UserService, AuthService

def some_business_logic(db_session, config):
    user_service = UserService(db_session)
    auth_service = AuthService(db_session, config)
    
    # Benutzer erstellen
    user = user_service.create_user(user_data)
    
    # Authentifizierung
    token_data = auth_service.login(email, password)
```

## Sicherheitsfeatures

- **Passwort-Hashing**: argon2id für neue Hashes, bcrypt für Legacy-Hashes
- **JWT-Token**: HS256-Signierung mit konfigurierbarem Secret
- **Token-Verifikation**: Automatische Signatur- und Ablaufprüfung
- **Berechtigungssystem**: Rollen-basierte Zugriffskontrolle
- **Input-Validierung**: Pydantic-basierte Request-Validierung
- **SQL-Injection-Schutz**: SQLAlchemy ORM
- **Rate-Limiting-Ready**: Strukturiert für Rate-Limiting-Integration

## Best Practices

### 1. Umgebungsvariablen
```bash
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Produktions-Setup
- Verwenden Sie starke SECRET_KEY (mindestens 32 Zeichen)
- Implementieren Sie HTTPS in der Produktion
- Konfigurieren Sie angemessene Token-Ablaufzeiten
- Überwachen Sie fehlgeschlagene Login-Versuche

### 3. E-Mail-Integration
Für Passwort-Reset-E-Mails erweitern Sie die `AuthService`:

```python
def send_password_reset_email(self, email: str, token: str):
    # Ihre E-Mail-Implementierung
    pass
```

## Erweiterbarkeit

Das Modul ist für Erweiterungen konzipiert:

- **Zusätzliche Benutzerfelder**: Erweitern Sie das User-Modell
- **Komplexere Rollen**: Implementieren Sie ein Permission-System
- **OAuth-Provider**: Integrieren Sie externe Authentifizierung
- **Token-Blacklisting**: Fügen Sie Redis-basiertes Token-Management hinzu
- **Audit-Logging**: Protokollieren Sie Benutzeraktivitäten

## Abhängigkeiten

- FastAPI
- SQLAlchemy
- Pydantic
- python-jose[cryptography] (für JWT)
- passlib[bcrypt,argon2] (für Passwort-Hashing)
- python-multipart (für OAuth2-Forms)

## Beispiel-Integration in Rideto

```python
# In der bestehenden Rideto-App
from backend.app.config import settings
from backend.database.base import get_db
from users_auth import UserAuthModule

def setup_auth(app: FastAPI):
    class AuthConfig:
        SECRET_KEY = settings.SECRET_KEY
        ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    auth_module = UserAuthModule()
    auth_module.init_app(app, next(get_db()), AuthConfig())
```

Dieses Modul bietet eine solide Grundlage für Authentifizierung und Benutzerverwaltung, die in verschiedenen FastAPI-Projekten wiederverwendet werden kann.
