#!/usr/bin/env python3
"""
Einfacher EA Test ohne Admin-Rechte
Testet verschiedene Methoden um EA zu verwenden
"""

import sys
import os
from pathlib import Path

def test_method_1_dispatch():
    """Versuche Standard COM Dispatch"""
    print("\n1. Teste Standard COM Dispatch...")
    try:
        import win32com.client
        ea = win32com.client.Dispatch("EA.Repository")
        print("   [OK] Funktioniert! EA.Repository verfügbar")
        return ea
    except Exception as e:
        print(f"   [FEHLER] Fehlgeschlagen: {e}")
        return None

def test_method_2_dynamic():
    """Versuche Dynamic Dispatch"""
    print("\n2. Teste Dynamic Dispatch...")
    try:
        import win32com.client.dynamic
        ea = win32com.client.dynamic.Dispatch("EA.Repository")
        print("   [OK] Funktioniert! Dynamic Dispatch erfolgreich")
        return ea
    except Exception as e:
        print(f"   [FEHLER] Fehlgeschlagen: {e}")
        return None

def test_method_3_clsid():
    """Versuche über CLSID"""
    print("\n3. Teste CLSID Methode...")
    try:
        import win32com.client
        # EA Repository CLSID
        ea = win32com.client.Dispatch("{64F919B0-65DF-11D3-8E8C-00609780B34A}")
        print("   [OK] Funktioniert! CLSID Dispatch erfolgreich")
        return ea
    except Exception as e:
        print(f"   [FEHLER] Fehlgeschlagen: {e}")
        return None

def test_method_4_gencache():
    """Versuche mit EnsureDispatch (erstellt Type Library)"""
    print("\n4. Teste EnsureDispatch...")
    try:
        import win32com.client
        ea = win32com.client.gencache.EnsureDispatch("EA.Repository")
        print("   [OK] Funktioniert! EnsureDispatch erfolgreich")
        return ea
    except Exception as e:
        print(f"   [FEHLER] Fehlgeschlagen: {e}")
        return None

def test_method_5_late_binding():
    """Versuche Late Binding"""
    print("\n5. Teste Late Binding...")
    try:
        import pythoncom
        import win32com.client
        
        pythoncom.CoInitialize()
        ea = win32com.client.Dispatch("EA.Repository")
        print("   [OK] Funktioniert! Late Binding erfolgreich")
        return ea
    except Exception as e:
        print(f"   [FEHLER] Fehlgeschlagen: {e}")
        pythoncom.CoUninitialize()
        return None

def test_ea_functionality(ea):
    """Teste EA Funktionalität"""
    if not ea:
        return False
        
    print("\nTeste EA-Funktionen...")
    try:
        # Teste wichtige Eigenschaften
        if hasattr(ea, 'OpenFile'):
            print("   [OK] OpenFile Methode vorhanden")
        if hasattr(ea, 'Models'):
            print("   [OK] Models Collection vorhanden")
        if hasattr(ea, 'CreateModel'):
            print("   [OK] CreateModel Methode vorhanden")
            
        # Versuche Test-Datei
        test_file = Path.home() / "EA_NoAdmin_Test.eapx"
        print(f"\n   Erstelle Test-Datei: {test_file}")
        
        # Versuche neue Datei zu erstellen (wenn möglich)
        try:
            if not test_file.exists():
                success = ea.CreateModel(str(test_file), 0)
                if success:
                    print("   [OK] Test-Datei erstellt!")
                else:
                    print("   ⚠️  CreateModel returned False")
        except Exception as e:
            print(f"   ⚠️  CreateModel nicht möglich: {e}")
            
        # Versuche zu öffnen
        try:
            success = ea.OpenFile(str(test_file))
            if success:
                print("   [OK] Datei geöffnet!")
                
                # Teste Models
                models = ea.Models
                print(f"   [OK] Models.Count = {models.Count}")
                
                # Schließe Datei
                ea.CloseFile()
                print("   [OK] Datei geschlossen")
                
                # Lösche Test-Datei
                if test_file.exists():
                    test_file.unlink()
                    print("   [OK] Test-Datei gelöscht")
                    
                return True
            else:
                print("   [FEHLER] Konnte Datei nicht öffnen")
                return False
        except Exception as e:
            print(f"   [FEHLER] Fehler beim Datei-Test: {e}")
            return False
            
    except Exception as e:
        print(f"   [FEHLER] Fehler: {e}")
        return False

def main():
    print("=" * 60)
    print("EA Test ohne Admin-Rechte")
    print("=" * 60)
    
    # Prüfe ob Windows
    if sys.platform != "win32":
        print("[FEHLER] Dieses Skript läuft nur auf Windows!")
        return
        
    # Prüfe pywin32
    try:
        import win32com.client
        print("[OK] pywin32 ist installiert")
    except ImportError:
        print("[FEHLER] pywin32 nicht installiert!")
        print("   Installiere mit: pip install pywin32")
        return
    
    # Teste verschiedene Methoden
    methods = [
        test_method_1_dispatch,
        test_method_2_dynamic,
        test_method_3_clsid,
        test_method_4_gencache,
        test_method_5_late_binding
    ]
    
    ea = None
    for method in methods:
        ea = method()
        if ea:
            break
    
    # Teste EA-Funktionalität
    if ea:
        print("\n" + "=" * 60)
        print("[OK] EA-Verbindung hergestellt!")
        print("=" * 60)
        
        if test_ea_functionality(ea):
            print("\n[ERFOLG] EA funktioniert ohne Admin-Rechte!")
            print("\nDu kannst jetzt die Scripts verwenden:")
            print("  python scripts/init_project.py --model Test")
        else:
            print("\n⚠️  EA-Verbindung da, aber eingeschränkte Funktionalität")
    else:
        print("\n" + "=" * 60)
        print("[FEHLER] Keine Methode funktionierte!")
        print("=" * 60)
        print("\nLösungsvorschläge:")
        print("1. Starte Enterprise Architect einmal normal")
        print("2. Öffne und schließe ein Projekt in EA")
        print("3. Versuche dann dieses Skript erneut")
        print("\nODER frage IT-Support nach:")
        print('- Ausführung von: "C:\\Program Files\\Sparx Systems\\EA\\EA.exe" /register')
        print("- Installation von EA für alle Benutzer")

if __name__ == "__main__":
    main()