#!/usr/bin/env python3
"""
Diagnose-Skript für Enterprise Architect COM-Verbindung
Hilft bei der Fehlersuche wenn EA COM nicht funktioniert
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

def check_windows():
    """Prüft ob wir auf Windows laufen"""
    if platform.system() != "Windows":
        print("❌ Dieses Skript läuft nur auf Windows!")
        print(f"   Aktuelles OS: {platform.system()}")
        return False
    print(f"✓ Windows erkannt: {platform.version()}")
    return True

def check_pywin32():
    """Prüft ob pywin32 installiert ist"""
    try:
        import win32com.client
        print("✓ pywin32 ist installiert")
        return True
    except ImportError:
        print("❌ pywin32 ist nicht installiert")
        print("   Installiere mit: pip install pywin32")
        return False

def check_ea_com_registration():
    """Prüft ob EA als COM-Server registriert ist"""
    try:
        import win32com.client
        
        # Versuche verschiedene EA COM ProgIDs
        prog_ids = [
            "EA.Repository",
            "EA.App",
            "EA.Project"
        ]
        
        for prog_id in prog_ids:
            try:
                print(f"\nTeste ProgID: {prog_id}")
                obj = win32com.client.Dispatch(prog_id)
                print(f"  ✓ {prog_id} erfolgreich erstellt")
                
                # Teste Eigenschaften
                if prog_id == "EA.Repository":
                    print(f"    - Typ: {type(obj)}")
                    if hasattr(obj, 'OpenFile'):
                        print(f"    - OpenFile Methode vorhanden")
                    if hasattr(obj, 'Models'):
                        print(f"    - Models Collection vorhanden")
                    if hasattr(obj, 'GetPackageByGuid'):
                        print(f"    - GetPackageByGuid Methode vorhanden")
                    return obj
                    
            except Exception as e:
                print(f"  ❌ {prog_id} fehlgeschlagen: {e}")
                
        return None
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der COM-Registrierung: {e}")
        return None

def find_ea_installation():
    """Sucht nach EA Installation"""
    print("\nSuche EA Installation...")
    
    common_paths = [
        r"C:\Program Files\Sparx Systems\EA",
        r"C:\Program Files (x86)\Sparx Systems\EA",
        r"C:\Program Files\Sparx Systems\EA16",
        r"C:\Program Files (x86)\Sparx Systems\EA16",
        r"C:\Program Files\Sparx Systems\EA15",
        r"C:\Program Files (x86)\Sparx Systems\EA15",
    ]
    
    ea_exe = None
    for path in common_paths:
        ea_path = Path(path)
        if ea_path.exists():
            print(f"  ✓ EA-Verzeichnis gefunden: {path}")
            
            # Suche EA.exe
            ea_exe_path = ea_path / "EA.exe"
            if ea_exe_path.exists():
                print(f"    ✓ EA.exe gefunden: {ea_exe_path}")
                ea_exe = str(ea_exe_path)
                break
            else:
                print(f"    ❌ EA.exe nicht gefunden in {path}")
    
    if not ea_exe:
        print("  ❌ EA Installation nicht gefunden")
        print("     Bitte manuell registrieren oder Pfad prüfen")
        
    return ea_exe

def register_ea_com(ea_exe_path):
    """Versucht EA als COM-Server zu registrieren"""
    if not ea_exe_path:
        return False
        
    print(f"\nVersuche EA COM-Server zu registrieren...")
    print(f"  EA.exe: {ea_exe_path}")
    
    try:
        # Versuche EA mit /register zu starten
        cmd = f'"{ea_exe_path}" /register'
        print(f"  Führe aus: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✓ Registrierung erfolgreich")
            return True
        else:
            print(f"  ❌ Registrierung fehlgeschlagen: {result.stderr}")
            print("\n  Versuche als Administrator:")
            print(f'    1. Öffne CMD als Administrator')
            print(f'    2. Führe aus: "{ea_exe_path}" /register')
            return False
            
    except Exception as e:
        print(f"  ❌ Fehler bei Registrierung: {e}")
        return False

def test_repository_creation():
    """Testet ob ein Repository-Objekt erstellt werden kann"""
    print("\nTeste Repository-Erstellung...")
    
    try:
        import win32com.client
        
        # Erstelle Repository
        repo = win32com.client.Dispatch("EA.Repository")
        print("  ✓ Repository-Objekt erstellt")
        
        # Teste wichtige Methoden
        methods = ['OpenFile', 'OpenFile2', 'CreateModel', 'Models', 'GetPackageByGuid']
        for method in methods:
            if hasattr(repo, method):
                print(f"    ✓ {method} verfügbar")
            else:
                print(f"    ❌ {method} NICHT verfügbar")
                
        return repo
        
    except Exception as e:
        print(f"  ❌ Repository konnte nicht erstellt werden: {e}")
        return None

def test_open_file(repo):
    """Testet ob eine Test-Datei geöffnet werden kann"""
    if not repo:
        return False
        
    print("\nTeste Datei-Öffnung...")
    
    # Erstelle Test-Datei-Pfad
    test_file = Path.home() / "EA_Test.eapx"
    print(f"  Test-Datei: {test_file}")
    
    try:
        # Versuche neue Datei zu erstellen
        if not test_file.exists():
            print("  Erstelle neue Test-Datei...")
            success = repo.CreateModel(str(test_file), 0)  # 0 = .eapx format
            if success:
                print("  ✓ Test-Datei erstellt")
            else:
                print("  ❌ Konnte Test-Datei nicht erstellen")
                return False
        
        # Versuche Datei zu öffnen
        success = repo.OpenFile(str(test_file))
        if success:
            print("  ✓ Datei erfolgreich geöffnet")
            
            # Teste Models Collection
            models = repo.Models
            print(f"    - Anzahl Models: {models.Count}")
            
            # Schließe Datei
            repo.CloseFile()
            print("  ✓ Datei geschlossen")
            
            return True
        else:
            print("  ❌ Konnte Datei nicht öffnen")
            return False
            
    except Exception as e:
        print(f"  ❌ Fehler beim Datei-Test: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("EA COM Diagnose-Tool")
    print("=" * 60)
    
    # Schritt 1: Windows prüfen
    if not check_windows():
        sys.exit(1)
    
    # Schritt 2: pywin32 prüfen
    if not check_pywin32():
        sys.exit(2)
    
    # Schritt 3: EA COM-Registrierung prüfen
    repo = check_ea_com_registration()
    
    # Schritt 4: EA Installation suchen
    ea_exe = find_ea_installation()
    
    # Schritt 5: Falls COM nicht funktioniert, versuche zu registrieren
    if not repo and ea_exe:
        if register_ea_com(ea_exe):
            # Prüfe erneut
            repo = check_ea_com_registration()
    
    # Schritt 6: Repository-Tests
    if not repo:
        repo = test_repository_creation()
    
    # Schritt 7: Datei-Test
    if repo:
        test_open_file(repo)
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    
    if repo:
        print("✅ EA COM-Verbindung funktioniert!")
        print("\nNächste Schritte:")
        print("1. Kopiere .env.example nach .env")
        print("2. Setze EA_PROJECT_PATH zu deiner EA-Datei")
        print("3. Führe aus: python scripts/init_project.py --model Test")
    else:
        print("❌ EA COM-Verbindung funktioniert NICHT!")
        print("\nLösungsvorschläge:")
        print("1. Stelle sicher dass EA installiert ist")
        print("2. Öffne CMD als Administrator")
        print(f"3. Führe aus: \"{ea_exe if ea_exe else 'C:\\Program Files\\Sparx Systems\\EA\\EA.exe'}\" /register")
        print("4. Starte dieses Skript erneut")
        print("\nAlternativ:")
        print("- Deinstalliere und reinstalliere EA")
        print("- Stelle sicher dass die richtige EA-Version installiert ist")
        
    print("=" * 60)

if __name__ == "__main__":
    main()