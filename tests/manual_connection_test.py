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