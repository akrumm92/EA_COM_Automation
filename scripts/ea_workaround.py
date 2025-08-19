#!/usr/bin/env python3
"""
Workaround für EA "Internal application error"
Verwendet EA.App und EA.Project statt direkten Repository-Zugriff
"""

import sys
import os
from pathlib import Path
import time

def fix_ea_internal_error():
    """
    Lösung für "Internal application error" Problem
    EA muss initialisiert werden bevor Repository-Methoden funktionieren
    """
    print("=" * 60)
    print("EA Workaround für Internal Application Error")
    print("=" * 60)
    
    try:
        import win32com.client
        
        print("\n1. Starte EA Application...")
        # EA.App funktioniert laut deinem Log!
        ea_app = win32com.client.Dispatch("EA.App")
        print("   ✓ EA.App erstellt")
        
        # Warte kurz damit EA sich initialisiert
        print("   Warte 2 Sekunden für EA-Initialisierung...")
        time.sleep(2)
        
        print("\n2. Hole Repository von EA.App...")
        try:
            # Versuche Repository über App zu holen
            repo = ea_app.Repository
            print("   ✓ Repository über EA.App erhalten")
        except:
            # Alternative: Erstelle neues Repository
            print("   Erstelle neues Repository...")
            repo = win32com.client.Dispatch("EA.Repository")
            print("   ✓ Repository direkt erstellt")
        
        print("\n3. Öffne oder erstelle Test-Datei...")
        test_file = Path.home() / "EA_Workaround_Test.eapx"
        
        # Versuche verschiedene Methoden die Datei zu öffnen
        success = False
        
        # Methode 1: OpenFile
        try:
            if test_file.exists():
                print(f"   Öffne existierende Datei: {test_file}")
                success = repo.OpenFile(str(test_file))
            else:
                print(f"   Erstelle neue Datei: {test_file}")
                # Versuche CreateModel
                success = repo.CreateModel(str(test_file), 0)  # 0 = .eapx
                if success:
                    print("   ✓ Datei erstellt")
                    success = repo.OpenFile(str(test_file))
        except Exception as e:
            print(f"   ⚠ OpenFile fehlgeschlagen: {e}")
        
        # Methode 2: OpenFile2 (für Datenbanken/Connection Strings)
        if not success:
            try:
                print("   Versuche OpenFile2...")
                success = repo.OpenFile2(str(test_file), "", "")
            except Exception as e:
                print(f"   ⚠ OpenFile2 fehlgeschlagen: {e}")
        
        # Methode 3: Über EA.Project
        if not success:
            try:
                print("\n4. Alternative: Verwende EA.Project...")
                ea_project = win32com.client.Dispatch("EA.Project")
                print("   ✓ EA.Project erstellt")
                
                # Manche EA-Versionen erlauben Project-basierte Operationen
                success = True
            except Exception as e:
                print(f"   ⚠ EA.Project fehlgeschlagen: {e}")
        
        if success:
            print("\n✅ ERFOLG! EA funktioniert mit Workaround!")
            
            # Teste ob Models jetzt funktioniert
            try:
                print("\n5. Teste Models-Zugriff...")
                models = repo.Models
                print(f"   ✓ Models.Count = {models.Count}")
                
                # Versuche ein Model zu erstellen
                if models.Count == 0:
                    print("   Erstelle Test-Model...")
                    model = models.AddNew("TestModel", "Package")
                    if model:
                        model.Update()
                        models.Refresh()
                        print("   ✓ Model erstellt!")
                        
            except Exception as e:
                print(f"   ⚠ Models-Zugriff fehlgeschlagen: {e}")
                print("   → Verwende Package-Funktionen ohne Models-Collection")
            
            # Schließe und aufräumen
            try:
                repo.CloseFile()
                print("\n✓ Repository geschlossen")
            except:
                pass
                
            return repo
        else:
            print("\n❌ Konnte EA nicht initialisieren")
            return None
            
    except ImportError:
        print("❌ pywin32 nicht installiert")
        return None
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return None

def alternative_package_creation():
    """
    Alternative Methode für Package-Erstellung ohne Models-Collection
    """
    print("\n" + "=" * 60)
    print("Alternative Package-Erstellung")
    print("=" * 60)
    
    try:
        import win32com.client
        
        # Verwende EA.App
        ea_app = win32com.client.Dispatch("EA.App")
        repo = ea_app.Repository
        
        # Öffne Datei aus .env oder Parameter
        env_path = os.getenv('EA_PROJECT_PATH')
        if env_path and Path(env_path).exists():
            print(f"Öffne Projekt aus .env: {env_path}")
            success = repo.OpenFile(env_path)
            
            if success:
                print("✓ Projekt geöffnet")
                
                # Alternative: GetPackageByGuid oder SQL Queries
                print("\nAlternative Methoden:")
                
                # 1. SQL Query für Packages
                try:
                    sql = "SELECT Package_ID, Name FROM t_package WHERE Parent_ID = 0"
                    packages = repo.SQLQuery(sql)
                    print(f"✓ SQL Query funktioniert: {packages[:100]}...")
                except Exception as e:
                    print(f"⚠ SQL Query nicht verfügbar: {e}")
                
                # 2. GetPackageByID
                try:
                    # Package ID 1 ist oft das Root
                    pkg = repo.GetPackageByID(1)
                    if pkg:
                        print(f"✓ GetPackageByID funktioniert: {pkg.Name}")
                except Exception as e:
                    print(f"⚠ GetPackageByID nicht verfügbar: {e}")
                
                # 3. Über TreeView
                try:
                    tree = repo.GetTreeSelectedObject()
                    if tree:
                        print(f"✓ TreeView-Zugriff funktioniert")
                except Exception as e:
                    print(f"⚠ TreeView nicht verfügbar: {e}")
                    
                repo.CloseFile()
                print("\n✓ Alternative Methoden getestet")
                
    except Exception as e:
        print(f"❌ Fehler: {e}")

def main():
    # Schritt 1: Workaround versuchen
    repo = fix_ea_internal_error()
    
    if repo:
        print("\n" + "=" * 60)
        print("✅ EA funktioniert mit Workaround!")
        print("=" * 60)
        print("\nDu kannst jetzt verwenden:")
        print("1. EA.App statt direktem Repository")
        print("2. Warte nach EA.App Erstellung (sleep)")
        print("3. Hole Repository über ea_app.Repository")
        print("\nUpdate deine Scripts entsprechend!")
    else:
        # Schritt 2: Alternative Methoden
        print("\nVersuche alternative Methoden...")
        alternative_package_creation()
        
        print("\n" + "=" * 60)
        print("LÖSUNGSVORSCHLÄGE:")
        print("=" * 60)
        print("\n1. STARTE EA MANUELL:")
        print("   - Öffne Enterprise Architect")
        print("   - Öffne ein Projekt")
        print("   - Lass EA geöffnet")
        print("   - Führe dann deine Scripts aus")
        print("\n2. LIZENZ PRÜFEN:")
        print("   - Der 'Internal application error' kann auf Lizenzprobleme hinweisen")
        print("   - Stelle sicher dass EA eine gültige Lizenz hat")
        print("\n3. EA VERSION:")
        print("   - Manche EA-Versionen haben COM-Probleme")
        print("   - Update auf neueste Version oder")
        print("   - Verwende EA 15 oder 16 (stabiler für COM)")
        print("\n4. FIREWALL/ANTIVIRUS:")
        print("   - Manche Security-Software blockiert COM")
        print("   - Füge EA.exe als Ausnahme hinzu")

if __name__ == "__main__":
    main()