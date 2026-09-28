# AGENTS.md - fastapi-users-auth

## Zweck

Dieses Paket stellt wiederverwendbare Benutzerverwaltung und Authentifizierung fuer
FastAPI-Anwendungen bereit. Es umfasst Pydantic-Schemas, dynamisch erzeugte SQLAlchemy-Modelle,
JWT-/Passwortlogik, FastAPI-Dependencies, Router und optionale OAuth-Provider.

## Sicherheitsregeln

- Secrets, Passwoerter, JWTs, Refresh-Tokens und Password-Reset-Tokens niemals loggen oder in
  Fehlermeldungen/API-Antworten offenlegen.
- `SECRET_KEY` muss in Produktion aus einer sicheren externen Konfiguration kommen; keine
  Entwicklungs-Defaults produktiv verwenden.
- Passwort-Hashes nur ueber `SecurityUtils` erzeugen und verifizieren. Argon2 ist der Standard;
  bcrypt bleibt nur fuer Legacy-Hashes kompatibel.
- Token-Signatur, Ablaufzeit und Claims ueber `TokenUtils` bzw. die vorhandenen Services behandeln.
- Geschuetzte Endpunkte ausschliesslich mit den vorhandenen Auth-Dependencies absichern und
  `is_active`/Superuser-Pruefungen nicht umgehen.
- OAuth-Client-Secrets und Redirect-URIs nicht in Quelltext, Tests oder Beispieldateien fest
  einbauen.

## Projektstruktur

- `models/`: Pydantic-Modelle sowie User-, Gruppen- und Membership-Modelle
- `model_factory.py`: ORM-Modell-Erzeugung fuer eine injizierte Base, Praefixe und Mixins
- `services/`: Benutzer-, Authentifizierungs-, OAuth- und Provider-Services
- `dependencies/`: Auth-Dependencies und zentraler `AuthProvider`
- `routers/`: Login, Registrierung, Benutzerverwaltung, Settings und Multi-Provider-Routen
- `utils/`: Passwort-/Token-Sicherheitsfunktionen
- `config/`: Auth- und OAuth-Konfiguration
- `templates/`: mitgelieferte HTML-Templates
- `tests/`: Model-Fabrik, Router, Gruppen, Security und Passwort-Kompatibilitaet

## ORM-Integration

- ORM-Klassen nicht mit einer fremden globalen Base voraussetzen. Anwendungen sollen
  `create_auth_models()` bzw. `configure_auth_models()` mit ihrer Declarative Base aufrufen.
- `table_prefix` fuer alle Auth-Tabellen bewusst setzen, wenn Namenskollisionen moeglich sind.
- `user_mixins`, `user_attrs_override` und `user_class_name` nur gezielt verwenden und fuer jede
  Kombination Tests vorsehen.
- Das Cache-Verhalten pro Base, Praefix und Mixin-Kombination erhalten.
- Bei Aenderungen an Tabellen, Foreign Keys, Constraints oder Beziehungen eine Migration im
  Consumer-Projekt einplanen.
- Module, die die oeffentlichen `User`, `Group` oder Membership-Aliasse verwenden, muessen nach
  `configure_auth_models()` weiterhin auf das konfigurierte Modell zeigen.

## Router und Services

- Services erhalten Datenbank-Session und Konfiguration als Abhaengigkeiten; keine globale
  Datenbankverbindung einfuehren.
- Neue FastAPI-Routen ueber die bestehenden Router-Klassen und Dependency-Factories integrieren.
- Provider-Reihenfolge und Prioritaeten im `AuthServiceManager` nicht still veraendern.
- Fehler bei Authentifizierung als sichere generische Antworten behandeln; keine User-Enumeration
  durch unterschiedliche Antworten bei Login oder Password-Reset einfuehren.
- Lazy-Imports in `__init__.py` beibehalten, damit das Basismodul ohne unnoetige Router- oder
  Service-Seiteneffekte importierbar bleibt.
- Neue oeffentliche Symbole ueber `fastapi_users_auth.__init__` exportieren.

## Vorgehen bei Aenderungen

1. Betroffene Schichten identifizieren: Models/Factory, Services, Dependencies, Router und Utils.
2. Bei API- oder Authentifizierungsveraenderungen positive und negative Tests ergaenzen.
3. Bei Schema- oder Tabellenveraenderungen die Model-Factory- und Migrationsfolgen pruefen.
4. Dokumentation und Integrationsbeispiele aktualisieren, wenn Konfigurations- oder
   Initialisierungsschritte geaendert werden.

## Qualitaetssicherung

Aus dem Paketverzeichnis:

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
mypy .
```

Besonders pruefen: lange Passwoerter, Argon2- und Legacy-bcrypt-Verifikation, ungueltige/abgelaufene
Tokens, geschuetzte Endpunkte, Provider-Fallbacks, ORM-Praefixe und Modell-Alias-Rebinding.

## Nicht tun

- Keine Secrets oder Test-Credentials committen.
- Keine Tokens oder Passwoerter in Logs ausgeben, auch nicht teilweise oder zu Debug-Zwecken.
- Keine breite Ausnahmebehandlung einfuehren, die Authentifizierungsfehler verschluckt.
- Keine manuellen Aenderungen an `.idea`-, Cache- oder Build-Artefakten.

## Agent skills

### Issue tracker

Issues are tracked in this repository's GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

The default five-label triage vocabulary is used. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain-doc layout. See `docs/agents/domain.md`.
