# EA COM Automation - How To Use

## Voraussetzungen

- Windows OS
- Enterprise Architect installiert
- Python 3.8+
- pywin32 (`pip install pywin32`)

## Quick Start

### 1. Repository-Verbindung herstellen

```python
import win32com.client

# Repository erstellen und Datei öffnen
repo = win32com.client.Dispatch("EA.Repository")
success = repo.OpenFile(r"C:\path\to\your\project.qea")

if success:
    print("Erfolgreich verbunden!")
else:
    print("Verbindung fehlgeschlagen")
```

### 2. Package-Struktur erstellen

```python
# Models abrufen
models = repo.Models

# Erstes Model holen oder erstellen
if models.Count == 0:
    model = models.AddNew("Architecture", "Package")
    model.Update()
    models.Refresh()
else:
    model = models.GetAt(0)

# Packages erstellen
packages = model.Packages
new_package = packages.AddNew("01_Business_Layer", "Package")
new_package.Update()
packages.Refresh()
```

### 3. Elemente (Klassen) erstellen

```python
# Package holen
package = repo.GetPackageByGuid("{PACKAGE-GUID}")

# Element erstellen
elements = package.Elements
new_class = elements.AddNew("Customer", "Class")
new_class.Update()

# Attribute hinzufügen
attributes = new_class.Attributes
attr = attributes.AddNew("customerId", "String")
attr.Update()
attributes.Refresh()

# Methode hinzufügen
methods = new_class.Methods
method = methods.AddNew("getCustomerData", "void")
method.Update()
methods.Refresh()
```

### 4. Diagramme erstellen

```python
# Diagramm in Package erstellen
diagrams = package.Diagrams
diagram = diagrams.AddNew("Overview", "Class")
diagram.Update()
diagrams.Refresh()

# Element zum Diagramm hinzufügen
diagramObject = diagram.DiagramObjects.AddNew("", "")
diagramObject.ElementID = new_class.ElementID
diagramObject.Update()
```

### 5. SQL-Queries ausführen

```python
# SQL Query für Package-Informationen
sql = "SELECT Package_ID, Name FROM t_package WHERE Parent_ID = 0"
result = repo.SQLQuery(sql)
print(result)  # Gibt XML-formatiertes Ergebnis zurück
```

## Wichtige Hinweise

### ⚠️ "Internal Application Error" vermeiden

**Problem:** Direkter Zugriff auf Repository ohne Initialisierung führt zu Fehler.

**Lösung:** IMMER zuerst `OpenFile()` aufrufen:

```python
# RICHTIG
repo = win32com.client.Dispatch("EA.Repository")
repo.OpenFile(project_path)  # Initialisiert Repository!

# FALSCH
ea_app = win32com.client.GetActiveObject("EA.App")
repo = ea_app.Repository  # Kann zu Internal Error führen
```

### Repository schließen

```python
# Nach der Arbeit Repository schließen
repo.CloseFile()
```

## Vollständiges Beispiel

```python
#!/usr/bin/env python3
"""Beispiel für EA COM Automation"""

import win32com.client
from pathlib import Path

def create_architecture():
    # Repository öffnen
    repo = win32com.client.Dispatch("EA.Repository")
    project_path = r"C:\Projects\Architecture.qea"
    
    if not repo.OpenFile(project_path):
        print("Fehler beim Öffnen der Datei")
        return
    
    # Model abrufen
    models = repo.Models
    if models.Count > 0:
        model = models.GetAt(0)
    else:
        model = models.AddNew("Enterprise Architecture", "Package")
        model.Update()
    
    # Package-Struktur erstellen
    layer_names = [
        "01_Business_Layer",
        "02_Application_Layer",
        "03_Data_Layer",
        "04_Technology_Layer"
    ]
    
    packages = model.Packages
    for name in layer_names:
        pkg = packages.AddNew(name, "Package")
        pkg.Update()
        print(f"Package '{name}' erstellt")
    
    packages.Refresh()
    
    # Repository schließen
    repo.CloseFile()
    print("Fertig!")

if __name__ == "__main__":
    create_architecture()
```

## Troubleshooting

### Fehler: "Internal application error"
- Repository mit `OpenFile()` initialisieren
- Nicht `GetActiveObject()` verwenden

### Fehler: "pywintypes.com_error"
- Prüfen ob EA installiert ist
- Als Administrator ausführen
- EA manuell starten und Projekt öffnen

### Packages werden nicht angezeigt
- Project Browser aktualisieren (F5)
- `Refresh()` nach Updates aufrufen
- Repository neu öffnen

## Weitere Ressourcen

- [EA Automation Interface Documentation](https://sparxsystems.com/enterprise_architect_user_guide/16.1/automation_and_scripting/automation_interface.html)
- [Python win32com Documentation](https://github.com/mhammond/pywin32)