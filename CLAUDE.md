# EA_COM_Automation Projekt - Entwicklungsrichtlinien

## Entwicklungsumgebung

**Entwicklung:** Windows  
**Testing:** Windows  
**Wichtig:** Entwicklung erfolgt direkt auf Windows, da EA COM nur auf Windows funktioniert!

## ⚠️ WICHTIG: EA COM "Internal Application Error" Fix

### Problem
EA COM API wirft "Internal application error" bei direktem Zugriff auf Repository-Methoden.

### ✅ LÖSUNG
```python
import win32com.client

# FALSCH - führt zu Internal Error:
ea_app = win32com.client.GetActiveObject("EA.App")
repo = ea_app.Repository

# RICHTIG - Repository initialisieren:
repo = win32com.client.Dispatch("EA.Repository")
success = repo.OpenFile(r"C:\path\to\project.qea")
# Jetzt funktionieren alle Repository-Methoden!
```

### Funktionierende Methode für Package-Erstellung:
1. Neues Repository-Objekt mit `Dispatch("EA.Repository")` erstellen
2. Projekt-Datei mit `OpenFile()` öffnen - das initialisiert das Repository
3. Dann funktionieren Models, Packages, Elements etc. normal

### Was funktioniert:
- ✅ Package-Erstellung über Models.AddNew()
- ✅ Element-Erstellung (Klassen, Interfaces)
- ✅ Diagramm-Erstellung
- ✅ SQL-Queries
- ✅ GetPackageByGuid nach OpenFile()

## 📚 EA Dokumentation

**WICHTIG:** Alle EA-spezifischen Erkenntnisse und Lessons Learned werden in [`docs/EA_HOW_TO_USE.md`](docs/EA_HOW_TO_USE.md) dokumentiert!

Diese Datei enthält:
- Vollständige Code-Beispiele
- Troubleshooting-Guide
- Best Practices für EA COM
- Workarounds für bekannte Probleme

## Windows-Entwicklung

### Systemanforderungen
- Windows 10/11
- Enterprise Architect installiert
- Python 3.8+ 
- pywin32 (`pip install pywin32`)

### Pfad-Handling
- **IMMER** `os.path.join()` oder `pathlib.Path` für Dateipfade verwenden
- **NIEMALS** hardcodierte Pfad-Trennzeichen (`/` oder `\`)
- **IMMER** `encoding='utf-8'` bei Dateioperationen angeben

```python
# Richtig
from pathlib import Path
file_path = Path("tests") / "logs" / "test.log"

# Falsch
file_path = "tests/logs/test.log"
```

## Ordnerstruktur

```
EA_COM_Automation/
├── src/                    # Hauptquellcode
│   └── ...
├── tests/                  # Test-Dateien
│   ├── unit/              # Unit-Tests
│   ├── integration/       # Integrationstests
│   ├── fixtures/          # Test-Daten und Fixtures
│   └── conftest.py        # Pytest-Konfiguration
├── logs/                  # Log-Dateien (wird automatisch erstellt)
│   ├── test_runs/         # Test-Ausführungs-Logs
│   │   └── YYYY-MM-DD/    # Tagesordner
│   ├── debug/             # Debug-Logs
│   └── reports/           # Test-Reports
├── test_reports/          # HTML/XML Test-Reports
│   ├── html/              # HTML-Reports für Browser-Ansicht
│   └── junit/             # JUnit XML für CI/CD
└── run_tests_windows.py   # Windows-Test-Skript

```

## Logging-Konzept

### Log-Level
- **DEBUG:** Detaillierte Informationen für Debugging
- **INFO:** Allgemeine Informationen über Programmablauf
- **WARNING:** Warnungen, die Aufmerksamkeit erfordern
- **ERROR:** Fehler, die behoben werden müssen
- **CRITICAL:** Kritische Fehler, die zum Programmabbruch führen

### Log-Format
```python
import logging
from pathlib import Path
from datetime import datetime

# Log-Konfiguration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging(log_level=logging.INFO):
    log_dir = Path("logs") / "test_runs" / datetime.now().strftime("%Y-%m-%d")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_{datetime.now().strftime('%H%M%S')}.log"
    
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
```

### Logger-Verwendung
```python
import logging

logger = logging.getLogger(__name__)

# Beispiele
logger.debug("Detaillierte Debug-Information")
logger.info("Test wurde gestartet")
logger.warning("Unerwarteter Wert gefunden")
logger.error("Fehler beim Verbindungsaufbau", exc_info=True)
```

## Test-Report-Struktur

### Report-Komponenten

1. **Zusammenfassung**
   - Gesamtanzahl Tests
   - Erfolgreiche Tests
   - Fehlgeschlagene Tests
   - Übersprungene Tests
   - Ausführungszeit

2. **Detaillierte Ergebnisse**
   - Test-Name und Pfad
   - Status (PASS/FAIL/SKIP)
   - Ausführungszeit
   - Fehlermeldungen mit Stack-Trace
   - Logs für fehlgeschlagene Tests

3. **System-Informationen**
   - OS-Version
   - Python-Version
   - Installierte Pakete
   - Umgebungsvariablen

### Report-Formate

#### HTML-Report (für Menschen)
```python
# Mit pytest-html
# pytest --html=test_reports/html/report.html --self-contained-html
```

#### JUnit XML (für CI/CD)
```python
# Mit pytest
# pytest --junitxml=test_reports/junit/results.xml
```

#### JSON-Report (für weitere Verarbeitung)
```python
import json
from pathlib import Path
from datetime import datetime

def create_test_report(test_results):
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(test_results),
            "passed": sum(1 for r in test_results if r["status"] == "passed"),
            "failed": sum(1 for r in test_results if r["status"] == "failed"),
            "skipped": sum(1 for r in test_results if r["status"] == "skipped"),
        },
        "tests": test_results,
        "environment": {
            "platform": platform.system(),
            "python_version": sys.version,
            "cwd": str(Path.cwd())
        }
    }
    
    report_path = Path("test_reports") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_path
```

## Windows-Test-Workflow

### Vor jedem Commit:
1. Code auf macOS entwickeln
2. Änderungen auf Windows-System synchronisieren
3. `python run_tests_windows.py` ausführen
4. Test-Report prüfen
5. Bei Erfolg: Commit durchführen

### Test-Kommandos

```bash
# Alle Tests ausführen
python run_tests_windows.py

# Nur Unit-Tests
python run_tests_windows.py --unit

# Nur Integration-Tests  
python run_tests_windows.py --integration

# Mit Debug-Logging
python run_tests_windows.py --debug

# Mit Coverage-Report
python run_tests_windows.py --coverage
```

## Wichtige Regeln

1. **NIEMALS** Methoden mit `@validated_test` Decorator ohne Rückfrage ändern
2. **IMMER** Cross-Platform-Kompatibilität sicherstellen
3. **IMMER** auf Windows testen vor Commit
4. **IMMER** UTF-8 Encoding verwenden
5. **NIEMALS** absolute Pfade hardcoden
6. **IMMER** Logging für wichtige Operationen

## Dependencies

Nur Open-Source-Bibliotheken mit permissiven Lizenzen verwenden:
- ✅ MIT License
- ✅ Apache 2.0
- ✅ BSD
- ❌ GPL/LGPL/AGPL

## Kontakt bei Problemen

Bei Platform-spezifischen Problemen:
1. Logs prüfen in `logs/test_runs/`
2. Debug-Mode aktivieren für mehr Details
3. System-Informationen in Report prüfen