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