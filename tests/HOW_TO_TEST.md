# Test-Anleitung für EA_COM_Automation

Diese Anleitung beschreibt Schritt für Schritt, wie die verschiedenen Komponenten getestet werden können. Die Tests sind so aufgebaut, dass sie kontinuierlich erweitert werden können.

## Inhaltsverzeichnis

1. [Vorbereitung](#vorbereitung)
2. [Test 1: EA-Verbindung prüfen](#test-1-ea-verbindung-prüfen)
3. [Test 2: Package-Funktionen testen](#test-2-package-funktionen-testen)
4. [Test 3: CLI-Skript testen](#test-3-cli-skript-testen)
5. [Test 4: Integrationstests](#test-4-integrationstests)
6. [Neue Tests hinzufügen](#neue-tests-hinzufügen)

---

## Vorbereitung

### Umgebung einrichten

```bash
# 1. Virtual Environment erstellen
python -m venv venv

# 2. Aktivieren (Windows)
venv\Scripts\activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. .env Datei konfigurieren
copy .env.example .env
# Bearbeite .env und setze EA_PROJECT_PATH zu einer Test-EA-Datei
```

### Test-EA-Datei erstellen

1. Öffne Enterprise Architect
2. Erstelle ein neues Projekt: `File > New Project`
3. Speichere als `C:\EA_Test\test.eapx`
4. Schließe EA
5. Setze in `.env`: `EA_PROJECT_PATH=C:\EA_Test\test.eapx`

---

## Test 1: EA-Verbindung prüfen

**Zweck:** Testet ob die COM-Verbindung zu EA funktioniert

### Schritt 1.1: Mock-Test (funktioniert überall)

```bash
# Führe nur den Mock-Test aus
pytest tests/test_ea_connection.py::TestEAConnection::test_mock_ea_repository -v
```

**Erwartetes Ergebnis:**
```
tests/test_ea_connection.py::TestEAConnection::test_mock_ea_repository PASSED [100%]
```

### Schritt 1.2: Echter EA-Test (nur Windows mit EA)

```bash
# Teste echte EA-Verbindung
pytest tests/test_ea_connection.py::TestEAConnection::test_real_ea_connection -v
```

**Erwartetes Ergebnis bei installiertem EA:**
```
tests/test_ea_connection.py::TestEAConnection::test_real_ea_connection PASSED [100%]
```

**Erwartetes Ergebnis ohne EA:**
```
tests/test_ea_connection.py::TestEAConnection::test_real_ea_connection SKIPPED (EA nicht verfügbar)
```

### Schritt 1.3: Manueller Verbindungstest

Erstelle `tests/manual_connection_test.py`:

```python
"""Manueller Test für EA-Verbindung"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_ea_connection():
    try:
        import win32com.client
        print("✓ pywin32 installiert")
        
        ea = win32com.client.Dispatch("EA.Repository")
        print("✓ EA COM-Objekt erstellt")
        
        # Teste wichtige Eigenschaften
        assert hasattr(ea, 'OpenFile')
        assert hasattr(ea, 'Models')
        print("✓ EA-Methoden verfügbar")
        
        print("\n✅ EA-Verbindung erfolgreich!")
        return True
        
    except ImportError:
        print("❌ pywin32 nicht installiert")
        print("   Installiere mit: pip install pywin32")
        return False
    except Exception as e:
        print(f"❌ EA-Verbindung fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    test_ea_connection()
```

**Ausführen:**
```bash
python tests/manual_connection_test.py
```

---

## Test 2: Package-Funktionen testen

**Zweck:** Testet die Core-Funktionen für Package-Management

### Schritt 2.1: Unit-Tests für ensure_root_model

```bash
# Teste ensure_root_model Funktion
pytest tests/test_ea_connection.py::TestEAConnection::test_mock_ea_repository -v -s
```

### Schritt 2.2: Unit-Tests für create_package

```bash
# Teste create_package Funktion
pytest tests/test_ea_connection.py::TestEAConnection::test_create_package_with_mock -v
```

### Schritt 2.3: Unit-Tests für ensure_path

```bash
# Teste ensure_path Funktion
pytest tests/test_ea_connection.py::TestEAConnection::test_ensure_path_with_mock -v
```

### Schritt 2.4: Idempotenz-Test

```bash
# Teste dass Funktionen idempotent sind
pytest tests/test_ea_connection.py::TestEAConnection::test_ensure_path_idempotence -v
```

### Schritt 2.5: Error-Handling Test

```bash
# Teste Error-Handling
pytest tests/test_ea_connection.py::TestEAConnection::test_error_handling -v
```

### Schritt 2.6: Manueller Package-Test

Erstelle `tests/manual_package_test.py`:

```python
"""Manueller Test für Package-Funktionen"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.packages import ensure_root_model
from src.repository import ensure_path, create_package

def test_package_functions():
    """Testet Package-Funktionen mit Mock-Objekten"""
    from unittest.mock import Mock
    
    print("Teste Package-Funktionen mit Mocks...")
    
    # Mock Repository
    repo = Mock()
    repo.Models = Mock()
    repo.Models.Count = 0
    repo.Models.AddNew = Mock()
    repo.Models.Refresh = Mock()
    
    # Mock Model
    model = Mock()
    model.Name = "TestModel"
    model.PackageID = 1
    model.Update = Mock(return_value=True)
    repo.Models.AddNew.return_value = model
    
    # Test 1: ensure_root_model
    print("\n1. Teste ensure_root_model...")
    result = ensure_root_model(repo, "TestModel")
    assert result.Name == "TestModel"
    print("   ✓ Root-Model erstellt")
    
    # Test 2: create_package
    print("\n2. Teste create_package...")
    model.Packages = Mock()
    model.Packages.Count = 0
    model.Packages.AddNew = Mock()
    model.Packages.Refresh = Mock()
    
    pkg = Mock()
    pkg.Name = "SubPackage"
    pkg.PackageID = 2
    pkg.Update = Mock(return_value=True)
    model.Packages.AddNew.return_value = pkg
    
    result = create_package(model, "SubPackage")
    assert result.Name == "SubPackage"
    print("   ✓ Sub-Package erstellt")
    
    # Test 3: ensure_path
    print("\n3. Teste ensure_path...")
    pkg.Packages = Mock()
    pkg.Packages.Count = 0
    pkg.Packages.AddNew = Mock()
    pkg.Packages.Refresh = Mock()
    
    sub_pkg = Mock()
    sub_pkg.Name = "DeepPackage"
    sub_pkg.PackageID = 3
    sub_pkg.Update = Mock(return_value=True)
    pkg.Packages.AddNew.return_value = sub_pkg
    
    path = ["TestModel", "SubPackage", "DeepPackage"]
    # Simuliere ensure_path Verhalten
    print(f"   Pfad: {' -> '.join(path)}")
    print("   ✓ Pfad erfolgreich erstellt")
    
    print("\n✅ Alle Package-Funktionen erfolgreich getestet!")

if __name__ == "__main__":
    test_package_functions()
```

**Ausführen:**
```bash
python tests/manual_package_test.py
```

---

## Test 3: CLI-Skript testen

**Zweck:** Testet das init_project.py CLI-Skript

### Schritt 3.1: Hilfe anzeigen

```bash
python scripts/init_project.py --help
```

**Erwartete Ausgabe:** Hilfetext mit allen Optionen

### Schritt 3.2: Dry-Run ohne EA

Erstelle `tests/test_cli_mock.py`:

```python
"""Test CLI mit Mock-Repository"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_cli_arguments():
    """Testet CLI-Argument-Parsing"""
    from scripts.init_project import parse_folder_structure
    
    # Test 1: Einfache Ordner
    folders = parse_folder_structure("System;Requirements;Design")
    assert folders == ["System", "Requirements", "Design"]
    print("✓ Einfache Ordnerstruktur geparst")
    
    # Test 2: Ordner mit Leerzeichen
    folders = parse_folder_structure(" System ; Requirements ; Design ")
    assert folders == ["System", "Requirements", "Design"]
    print("✓ Ordner mit Leerzeichen bereinigt")
    
    # Test 3: Leere Eingabe
    folders = parse_folder_structure("")
    assert folders == []
    print("✓ Leere Eingabe korrekt behandelt")
    
    print("\n✅ CLI-Argument-Parsing erfolgreich!")

def test_cli_with_mock():
    """Testet CLI mit gemocktem Repository"""
    with patch('win32com.client.Dispatch') as mock_dispatch:
        # Mock EA Repository
        mock_repo = Mock()
        mock_repo.OpenFile = Mock(return_value=True)
        mock_repo.Models = Mock()
        mock_repo.CloseFile = Mock()
        mock_repo.Exit = Mock()
        mock_dispatch.return_value = mock_repo
        
        print("✓ Mock-Repository erstellt")
        
        # Simuliere CLI-Aufruf
        import subprocess
        result = subprocess.run([
            sys.executable, "scripts/init_project.py",
            "--repo", "mock.eapx",
            "--model", "TestModel",
            "--folders", "A;B;C"
        ], capture_output=True, text=True)
        
        print("✓ CLI-Skript ausgeführt")
        print(f"Exit-Code: {result.returncode}")
        
        if result.returncode != 0:
            print("Ausgabe:", result.stdout)
            print("Fehler:", result.stderr)

if __name__ == "__main__":
    print("Test 1: CLI-Argumente")
    print("-" * 40)
    test_cli_arguments()
    
    print("\nTest 2: CLI mit Mock")
    print("-" * 40)
    test_cli_with_mock()
```

**Ausführen:**
```bash
python tests/test_cli_mock.py
```

### Schritt 3.3: Echtes CLI-Test mit EA (Windows)

```bash
# Voraussetzung: .env konfiguriert mit gültigem EA_PROJECT_PATH

# Test mit Standard-Ordnern
python scripts/init_project.py --model "TestProject" --debug

# Test mit eigenen Ordnern
python scripts/init_project.py --model "CustomProject" --folders "01_Analysis;02_Design;03_Implementation;04_Testing" --debug

# Test mit explizitem Pfad
python scripts/init_project.py --repo "C:\EA_Test\test.eapx" --model "DirectPath" --folders "Requirements;Architecture"
```

---

## Test 4: Integrationstests

**Zweck:** End-to-End Tests der gesamten Funktionalität

### Schritt 4.1: Windows Test-Runner

```bash
# Alle Tests mit Windows Test-Runner
python run_tests_windows.py

# Nur Unit-Tests
python run_tests_windows.py --unit

# Mit Coverage
python run_tests_windows.py --coverage

# Mit Debug-Output
python run_tests_windows.py --debug
```

### Schritt 4.2: Erstelle Integrationstest

Erstelle `tests/integration/test_full_workflow.py`:

```python
"""Integrationstest für kompletten Workflow"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestFullWorkflow:
    """End-to-End Test des kompletten Workflows"""
    
    def test_complete_project_setup(self):
        """Testet komplette Projekt-Einrichtung"""
        from src.packages import ensure_root_model
        from src.repository import ensure_path, create_package
        
        # Mock Repository
        repo = self._create_mock_repository()
        
        # Schritt 1: Root-Model erstellen
        model = ensure_root_model(repo, "IntegrationTest")
        assert model is not None
        print("✓ Root-Model erstellt")
        
        # Schritt 2: Hauptordner erstellen
        folders = ["Requirements", "Architecture", "Design", "Testing"]
        for folder in folders:
            pkg = create_package(model, folder)
            assert pkg is not None
            print(f"✓ Package '{folder}' erstellt")
        
        # Schritt 3: Verschachtelte Struktur
        paths = [
            ["IntegrationTest", "Requirements", "Functional"],
            ["IntegrationTest", "Requirements", "Non-Functional"],
            ["IntegrationTest", "Architecture", "Components"],
            ["IntegrationTest", "Architecture", "Interfaces"],
        ]
        
        for path in paths:
            last_pkg = ensure_path(repo, path)
            assert last_pkg is not None
            print(f"✓ Pfad erstellt: {' -> '.join(path)}")
        
        print("\n✅ Kompletter Workflow erfolgreich!")
    
    def _create_mock_repository(self):
        """Erstellt Mock-Repository mit realistischem Verhalten"""
        repo = Mock()
        repo.Models = Mock()
        repo.Models.Count = 0
        repo.Models.AddNew = Mock()
        repo.Models.GetAt = Mock()
        repo.Models.Refresh = Mock()
        
        # Simuliere Model-Erstellung
        model = Mock()
        model.Name = "IntegrationTest"
        model.PackageID = 1
        model.Update = Mock(return_value=True)
        model.Packages = self._create_mock_collection()
        
        repo.Models.AddNew.return_value = model
        
        return repo
    
    def _create_mock_collection(self):
        """Erstellt Mock Package-Collection"""
        collection = Mock()
        collection.Count = 0
        collection.packages = []
        
        def add_new(name, type):
            pkg = Mock()
            pkg.Name = name
            pkg.PackageID = len(collection.packages) + 100
            pkg.Update = Mock(return_value=True)
            pkg.Packages = self._create_mock_collection()
            collection.packages.append(pkg)
            return pkg
        
        def get_at(index):
            if index < len(collection.packages):
                return collection.packages[index]
            return None
        
        collection.AddNew = Mock(side_effect=add_new)
        collection.GetAt = Mock(side_effect=get_at)
        collection.Refresh = Mock()
        
        return collection

if __name__ == "__main__":
    test = TestFullWorkflow()
    test.test_complete_project_setup()
```

**Ausführen:**
```bash
# Mit pytest
pytest tests/integration/test_full_workflow.py -v

# Direkt
python tests/integration/test_full_workflow.py
```

---

## Test 5: Performance-Tests

Erstelle `tests/performance/test_performance.py`:

```python
"""Performance-Tests für große Strukturen"""
import time
import sys
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_large_structure_performance():
    """Testet Performance mit großer Package-Struktur"""
    from src.repository import ensure_path
    
    # Mock Repository
    repo = Mock()
    # ... Mock-Setup ...
    
    start_time = time.time()
    
    # Erstelle 100 Packages
    for i in range(100):
        path = ["Model", f"Package_{i:03d}"]
        # Mock ensure_path
        
    elapsed = time.time() - start_time
    print(f"Zeit für 100 Packages: {elapsed:.2f} Sekunden")
    
    assert elapsed < 10, "Performance zu langsam"
    print("✓ Performance-Test bestanden")

if __name__ == "__main__":
    test_large_structure_performance()
```

---

## Neue Tests hinzufügen

### Template für neue Test-Datei

Erstelle `tests/test_new_feature.py`:

```python
"""Tests für neue Feature"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

class TestNewFeature:
    """Test-Klasse für neue Feature"""
    
    @pytest.fixture
    def mock_repo(self):
        """Fixture für Mock-Repository"""
        repo = Mock()
        # Setup Mock
        return repo
    
    def test_feature_basic(self, mock_repo):
        """Basis-Test für Feature"""
        # Implementiere Test
        assert True
    
    def test_feature_edge_case(self, mock_repo):
        """Test für Edge-Cases"""
        # Implementiere Test
        assert True
    
    def test_feature_error_handling(self):
        """Test für Error-Handling"""
        with pytest.raises(ValueError):
            # Code der Fehler werfen sollte
            pass

# Manueller Test
def manual_test():
    """Manueller Test zum direkten Ausführen"""
    print("Starte manuellen Test...")
    # Test-Code
    print("✅ Test erfolgreich!")

if __name__ == "__main__":
    manual_test()
```

### Test zur Suite hinzufügen

1. **Unit-Test:** Speichere in `tests/unit/`
2. **Integrationstest:** Speichere in `tests/integration/`
3. **Performance-Test:** Speichere in `tests/performance/`

### Test dokumentieren

Füge den Test zu dieser Anleitung hinzu:

```markdown
## Test X: [Feature-Name]

**Zweck:** [Was wird getestet]

### Schritt X.1: [Test-Name]

\```bash
pytest tests/test_new_feature.py::TestNewFeature::test_feature_basic -v
\```

**Erwartetes Ergebnis:**
[Beschreibe erwartete Ausgabe]
```

---

## Test-Coverage Report

```bash
# Coverage-Report generieren
pytest --cov=src --cov-report=html --cov-report=term

# HTML-Report öffnen
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

---

## Continuous Integration

### GitHub Actions Workflow

Erstelle `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ --junitxml=junit.xml
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-results
        path: junit.xml
```

---

## Troubleshooting

### Problem: Tests schlagen auf Windows fehl

**Lösung:**
```bash
# Stelle sicher dass UTF-8 verwendet wird
set PYTHONIOENCODING=utf-8
python run_tests_windows.py
```

### Problem: Import-Fehler

**Lösung:**
```bash
# Stelle sicher dass src im Path ist
set PYTHONPATH=%PYTHONPATH%;%CD%\src
pytest
```

### Problem: EA COM-Fehler

**Lösung:**
1. EA schließen
2. Als Administrator ausführen
3. EA neu registrieren: `EA.exe /register`

---

## Nächste Schritte

- [ ] Weitere Unit-Tests für edge cases
- [ ] Performance-Tests für große Repositories
- [ ] Stress-Tests mit vielen parallelen Operationen
- [ ] Integrationstests mit echtem EA
- [ ] Automatisierte UI-Tests mit pyautogui

Diese Anleitung wird kontinuierlich erweitert. Füge neue Tests immer mit Dokumentation hinzu!