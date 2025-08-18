# Installation und Setup

## Wichtiger Hinweis
pywin32 ist nur auf Windows-Systemen verfügbar, da es die Windows COM-Schnittstelle nutzt.

## Installation auf Windows

1. Virtual Environment erstellen:
```bash
python -m venv venv
```

2. Virtual Environment aktivieren:
```bash
# Windows CMD:
venv\Scripts\activate

# Windows PowerShell:
venv\Scripts\Activate.ps1
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

## Projektstruktur
```
EA_COM_Automation/
├── ea_automation/           # Hauptmodul
│   ├── __init__.py
│   ├── repository.py        # Repository-Funktionen
│   ├── packages.py          # Package-Verwaltung
│   ├── elements.py          # Element-Verwaltung
│   ├── diagrams.py          # Diagramm-Verwaltung
│   ├── connectors.py        # Connector-Verwaltung
│   ├── json_io.py           # JSON Import/Export
│   ├── logging_conf.py      # Logging-Konfiguration
│   ├── exceptions.py        # Exception-Klassen
│   └── utils.py             # Hilfsfunktionen
├── examples/                # Beispiele
│   └── example.json
├── api_documentation/       # Platz für EA API-Dokumentation
├── logs/                    # Log-Dateien (wird automatisch erstellt)
├── venv/                    # Virtual Environment
├── pyproject.toml           # Projekt-Konfiguration
├── requirements.txt         # Python-Abhängigkeiten
└── .gitignore

## Verwendung

```python
from ea_automation import open_repository, create_repository, close_repository
from ea_automation.packages import get_model_root

# Repository öffnen
repo = open_repository("path/to/model.eap")

# Mit dem Model arbeiten
root = get_model_root(repo)
new_package = root.add_package("MyPackage")

# Repository speichern und schließen
save(repo)
close_repository(repo)
```