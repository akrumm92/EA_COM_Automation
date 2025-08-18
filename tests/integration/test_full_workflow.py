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