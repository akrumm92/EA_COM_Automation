# EA_COM_Automation

Enterprise Architect COM Automation Framework für die automatisierte Verwaltung von EA-Projekten.

## Installation

### Voraussetzungen

- Windows OS (für EA COM-Automation)
- Python 3.8+
- Enterprise Architect installiert
- Git (optional)

### Setup

1. **Repository klonen:**
```bash
git clone https://github.com/yourusername/EA_COM_Automation.git
cd EA_COM_Automation
```

2. **Virtuelle Umgebung erstellen:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen konfigurieren:**
```bash
copy .env.example .env
# Bearbeite .env und setze EA_PROJECT_PATH
```

## Verwendung

### CLI-Skript: Projekt initialisieren

```bash
# Mit Umgebungsvariable
python scripts/init_project.py --model "MyProject" --folders "System;Requirements;Architecture"

# Mit explizitem Pfad
python scripts/init_project.py --repo "C:\Projects\test.eapx" --model "MyProject" --folders "01_Req;02_Arch;03_Design"

# Mit Debug-Ausgabe
python scripts/init_project.py --model "Test" --debug
```

**Argumente:**
- `--repo PATH`: Pfad zur EA-Datei (optional, nutzt EA_PROJECT_PATH aus .env)
- `--model NAME`: Name des Root-Model-Package (erforderlich)
- `--folders "A;B;C"`: Semikolon-getrennte Liste von Ordnern (optional)
- `--debug`: Aktiviert Debug-Logging

### Python API

```python
from src.packages import ensure_root_model
from src.repository import ensure_path, create_package
import win32com.client

# Mit Repository verbinden
repo = win32com.client.Dispatch("EA.Repository")
repo.OpenFile(r"C:\Projects\test.eapx")

# Root-Model sicherstellen
model = ensure_root_model(repo, "MyProject")

# Verschachtelten Pfad erstellen
path = ["MyProject", "System", "Components", "Database"]
last_package = ensure_path(repo, path)

# Einzelnes Package erstellen
new_pkg = create_package(model, "Documentation")

# Repository schließen
repo.CloseFile()
repo.Exit()
```

## Testing

### Tests ausführen

**Auf Windows (empfohlen):**
```bash
python run_tests_windows.py
```

**Optionen:**
```bash
# Nur Unit-Tests
python run_tests_windows.py --unit

# Mit Coverage
python run_tests_windows.py --coverage

# Debug-Modus
python run_tests_windows.py --debug
```

**Direkt mit pytest:**
```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=src --cov-report=html

# Nur EA-Connection Test
pytest tests/test_ea_connection.py -v
```

### Test-Struktur

```
tests/
├── unit/              # Unit-Tests mit Mocks
├── integration/       # Integrationstests mit EA
├── fixtures/          # Test-Daten
└── test_ea_connection.py  # EA-Verbindungstest
```

## Projekt-Struktur

```
EA_COM_Automation/
├── src/
│   ├── packages.py     # Package-Management Funktionen
│   └── repository.py   # Repository-Funktionen
├── scripts/
│   └── init_project.py # CLI für Projekt-Init
├── tests/
│   └── test_ea_connection.py
├── logs/               # Log-Dateien (automatisch erstellt)
├── test_reports/       # Test-Reports (automatisch erstellt)
├── .env.example        # Beispiel-Konfiguration
├── CLAUDE.md          # Entwicklungsrichtlinien
├── requirements.txt    # Python-Abhängigkeiten
└── run_tests_windows.py # Windows Test-Runner
```

## Features

- ✅ **Idempotente Package-Erstellung**: Existierende Packages werden wiederverwendet
- ✅ **Robustes Error-Handling**: Aussagekräftige Fehlermeldungen und Exit-Codes
- ✅ **Cross-Platform kompatibel**: Code läuft auf Windows und macOS (Tests mit Mocks)
- ✅ **Umfassende Tests**: Unit-Tests mit Mock-Objekten für CI/CD
- ✅ **Logging**: Detailliertes Logging für Debugging
- ✅ **CLI-Interface**: Einfache Verwendung über Kommandozeile

## Error-Codes

- `0`: Erfolg
- `1`: Allgemeiner Fehler
- `2`: Datei nicht gefunden
- `3`: Fehlende Abhängigkeit
- `4`: Unerwarteter Fehler

## Troubleshooting

**"pywin32 nicht installiert":**
```bash
pip install pywin32
```

**"EA.Repository kann nicht erstellt werden":**
- Stelle sicher, dass Enterprise Architect installiert ist
- Prüfe ob EA als COM-Server registriert ist
- Führe das Skript als Administrator aus (falls nötig)

**"Repository kann nicht geöffnet werden":**
- Prüfe den Dateipfad in .env oder --repo Argument
- Stelle sicher, dass die Datei nicht bereits geöffnet ist
- Prüfe Dateiberechtigungen

## Lizenz

MIT
