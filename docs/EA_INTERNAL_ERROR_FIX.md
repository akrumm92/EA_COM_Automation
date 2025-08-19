# EA "Internal Application Error" - Lösung

## Problem

Der Fehler "Internal application error" (Code 61704) tritt auf wenn:
- EA COM-Objekte erstellt werden können
- Aber Methoden wie `Models`, `CreateModel` oder `OpenFile` fehlschlagen

## Ursachen

1. **EA nicht vollständig initialisiert** - COM-Objekt existiert aber EA ist intern nicht bereit
2. **Lizenzproblem** - EA hat keine gültige Lizenz oder Floating License Server nicht erreichbar
3. **Security Software** - Antivirus/Firewall blockiert COM-Operationen
4. **EA läuft bereits** - Eine andere EA-Instanz blockiert

## Lösungen

### Lösung 1: EA manuell starten (Quick Fix)

**Das funktioniert fast immer:**

1. Starte Enterprise Architect normal (Doppelklick)
2. Öffne ein beliebiges Projekt
3. **Lass EA geöffnet**
4. Führe dein Python-Skript aus

```bash
# Mit geöffnetem EA:
python scripts/init_project.py --model Test
```

### Lösung 2: Workaround-Skript verwenden

```bash
# Teste den Workaround:
python scripts/ea_workaround.py
```

Dieses Skript:
- Verwendet `EA.App` statt `EA.Repository`
- Wartet auf EA-Initialisierung
- Hat Fallback-Strategien

### Lösung 3: EAConnector Klasse verwenden

```python
from src.ea_connector import EAConnector

# Robuste Verbindung mit Workarounds
with EAConnector() as ea:
    if ea.connect("C:\\path\\to\\project.eapx"):
        models = ea.get_models_safe()
        if models:
            print(f"Erfolg! Models: {models.Count}")
```

### Lösung 4: Code anpassen

**Alt (fehleranfällig):**
```python
import win32com.client
repo = win32com.client.Dispatch("EA.Repository")
models = repo.Models  # ❌ Internal Error
```

**Neu (mit Workaround):**
```python
import win32com.client
import time

# 1. Verwende EA.App
ea_app = win32com.client.Dispatch("EA.App")

# 2. Warte auf Initialisierung
time.sleep(2)

# 3. Hole Repository über App
repo = ea_app.Repository

# 4. Jetzt funktioniert's
models = repo.Models  # ✅ Funktioniert
```

## Permanente Lösungen

### Option A: EA-Lizenz prüfen

1. Öffne EA manuell
2. Gehe zu `Help > About EA`
3. Prüfe Lizenzstatus
4. Bei Floating License: Prüfe Server-Verbindung

### Option B: EA neu installieren

1. Deinstalliere EA komplett
2. Installiere EA neu **für alle Benutzer**
3. Starte EA einmal manuell
4. Registriere COM: `EA.exe /register`

### Option C: Registry-Fix (Advanced)

```cmd
# Als Admin in CMD:
reg delete "HKEY_CLASSES_ROOT\EA.Repository" /f
"C:\Program Files\Sparx Systems\EA\EA.exe" /register
```

## Test-Checkliste

Führe diese Tests der Reihe nach aus:

1. **Basis-Test:**
   ```bash
   python scripts/test_ea_simple.py
   ```

2. **Workaround-Test:**
   ```bash
   python scripts/ea_workaround.py
   ```

3. **Mit geöffnetem EA:**
   - Starte EA manuell
   - Öffne ein Projekt
   - Führe aus: `python scripts/init_project.py --model Test`

4. **Unit-Tests:**
   ```bash
   pytest tests/test_ea_connection.py -v -s
   ```

## Bekannte Einschränkungen

Wenn der Internal Error weiterhin auftritt:

1. **Verwende SQL-Queries** statt Models-Collection:
   ```python
   sql = "SELECT * FROM t_package WHERE Parent_ID = 0"
   result = repo.SQLQuery(sql)
   ```

2. **Verwende GetPackageByID** statt Models:
   ```python
   package = repo.GetPackageByID(1)  # Root Package
   ```

3. **Arbeite mit geöffnetem EA** - Das ist die stabilste Methode

## Support

Wenn nichts hilft:

1. EA-Version prüfen (mindestens Version 14)
2. Windows Event Log prüfen
3. EA Support kontaktieren mit Error Code 61704
4. Alternative: EA API über HTTP/REST verwenden (EA 15+)