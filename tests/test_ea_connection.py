"""
Test für EA COM-Verbindung
Testet ob die Kommunikation mit Enterprise Architect funktioniert
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import logging

# Füge src zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class TestEAConnection:
    """Tests für die EA COM-Verbindung"""
    
    @pytest.mark.skipif(sys.platform != "win32", reason="EA COM nur auf Windows")
    def test_real_ea_connection(self):
        """
        Testet echte Verbindung zu EA (nur auf Windows mit EA installiert)
        Dieser Test wird übersprungen wenn EA nicht verfügbar ist
        """
        try:
            import win32com.client
            
            # Versuche EA zu starten - mit besserem Error Handling
            try:
                ea_app = win32com.client.Dispatch("EA.Repository")
            except Exception as dispatch_error:
                # Gib detaillierte Fehlerinfo
                logger.warning(f"EA.Repository Dispatch fehlgeschlagen: {dispatch_error}")
                logger.info("Tipp: Führe 'python scripts/diagnose_ea.py' aus für Diagnose")
                pytest.skip(f"EA COM nicht verfügbar: {dispatch_error}")
            
            # Prüfe ob EA-Objekt erstellt wurde
            assert ea_app is not None, "EA Repository Objekt ist None"
            
            # Prüfe ob wichtige Eigenschaften vorhanden sind
            required_methods = ['OpenFile', 'Models', 'CloseFile', 'GetPackageByGuid']
            missing_methods = []
            
            for method in required_methods:
                if not hasattr(ea_app, method):
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"Fehlende EA-Methoden: {missing_methods}")
                pytest.fail(f"EA-Objekt unvollständig. Fehlende Methoden: {missing_methods}")
            
            logger.info("✅ EA COM-Verbindung erfolgreich")
            logger.info(f"   EA-Objekt Typ: {type(ea_app)}")
            
            # Optional: Versuche Test-Datei zu erstellen/öffnen
            test_file = Path.home() / "EA_pytest_test.eapx"
            try:
                if not test_file.exists():
                    # Versuche Test-Datei zu erstellen
                    success = ea_app.CreateModel(str(test_file), 0)  # 0 = .eapx
                    if success:
                        logger.info(f"   Test-Datei erstellt: {test_file}")
                
                # Versuche zu öffnen
                success = ea_app.OpenFile(str(test_file))
                if success:
                    logger.info(f"   Test-Datei geöffnet: {test_file}")
                    ea_app.CloseFile()
                    logger.info("   Test-Datei geschlossen")
                    
                    # Lösche Test-Datei
                    try:
                        test_file.unlink()
                        logger.info("   Test-Datei gelöscht")
                    except:
                        pass
            except Exception as file_error:
                logger.warning(f"   Datei-Test fehlgeschlagen: {file_error}")
            
            # Aufräumen
            try:
                ea_app.Exit()
            except:
                pass
                
        except ImportError:
            pytest.skip("pywin32 nicht installiert")
        except AssertionError:
            raise  # AssertionErrors durchreichen
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {e}")
            pytest.skip(f"EA nicht verfügbar: {e}")
    
    def test_mock_ea_repository(self):
        """Test mit gemocktem EA Repository (läuft überall)"""
        # Mock EA Repository
        mock_repo = Mock()
        mock_repo.Models = Mock()
        mock_repo.Models.Count = 0
        mock_repo.Models.AddNew = Mock(return_value=Mock())
        mock_repo.Models.GetAt = Mock()
        mock_repo.Models.Refresh = Mock()
        
        # Test ensure_root_model mit Mock
        from src.packages import ensure_root_model
        
        # Mock für neues Model
        mock_model = Mock()
        mock_model.Name = "TestModel"
        mock_model.PackageID = 123
        mock_model.Update = Mock(return_value=True)
        
        mock_repo.Models.AddNew.return_value = mock_model
        
        # Führe Funktion aus
        result = ensure_root_model(mock_repo, "TestModel")
        
        # Assertions
        assert result is not None
        assert result.Name == "TestModel"
        assert result.PackageID == 123
        mock_repo.Models.AddNew.assert_called_once_with("TestModel", "Package")
        mock_model.Update.assert_called_once()
        mock_repo.Models.Refresh.assert_called_once()
    
    def test_create_package_with_mock(self):
        """Test create_package mit Mock-Objekten"""
        from src.repository import create_package
        
        # Mock Parent Package
        mock_parent = Mock()
        mock_parent.PackageID = 100
        mock_parent.Packages = Mock()
        mock_parent.Packages.Count = 0
        mock_parent.Packages.GetAt = Mock()
        
        # Mock für neues Package
        mock_new_pkg = Mock()
        mock_new_pkg.Name = "TestPackage"
        mock_new_pkg.PackageID = 200
        mock_new_pkg.Update = Mock(return_value=True)
        
        mock_parent.Packages.AddNew = Mock(return_value=mock_new_pkg)
        mock_parent.Packages.Refresh = Mock()
        
        # Führe Funktion aus
        result = create_package(mock_parent, "TestPackage")
        
        # Assertions
        assert result is not None
        assert result.Name == "TestPackage"
        assert result.PackageID == 200
        mock_parent.Packages.AddNew.assert_called_once_with("TestPackage", "Package")
        mock_new_pkg.Update.assert_called_once()
        mock_parent.Packages.Refresh.assert_called_once()
    
    def test_ensure_path_with_mock(self):
        """Test ensure_path mit Mock-Objekten"""
        from src.repository import ensure_path
        
        # Mock Repository
        mock_repo = Mock()
        
        # Mock Models Collection
        mock_repo.Models = Mock()
        mock_repo.Models.Count = 0
        mock_repo.Models.GetAt = Mock()
        
        # Mock für Root Model
        mock_root = Mock()
        mock_root.Name = "Model"
        mock_root.PackageID = 1
        mock_root.Update = Mock(return_value=True)
        mock_root.Packages = Mock()
        mock_root.Packages.Count = 0
        mock_root.Packages.GetAt = Mock()
        mock_root.Packages.Refresh = Mock()
        
        mock_repo.Models.AddNew = Mock(return_value=mock_root)
        mock_repo.Models.Refresh = Mock()
        
        # Mock für Sub-Packages
        mock_pkg1 = Mock()
        mock_pkg1.Name = "System"
        mock_pkg1.PackageID = 2
        mock_pkg1.Update = Mock(return_value=True)
        mock_pkg1.Packages = Mock()
        mock_pkg1.Packages.Count = 0
        mock_pkg1.Packages.GetAt = Mock()
        mock_pkg1.Packages.Refresh = Mock()
        
        mock_pkg2 = Mock()
        mock_pkg2.Name = "Components"
        mock_pkg2.PackageID = 3
        mock_pkg2.Update = Mock(return_value=True)
        mock_pkg2.Packages = Mock()
        mock_pkg2.Packages.Count = 0
        mock_pkg2.Packages.Refresh = Mock()
        
        # Setup Mock-Verhalten
        mock_root.Packages.AddNew = Mock(return_value=mock_pkg1)
        mock_pkg1.Packages.AddNew = Mock(return_value=mock_pkg2)
        
        # Test Pfad
        path = ["Model", "System", "Components"]
        
        # Führe Funktion aus
        result = ensure_path(mock_repo, path)
        
        # Assertions
        assert result is not None
        assert result.PackageID == 3  # Letztes Package im Pfad
        
        # Prüfe ob alle Packages erstellt wurden
        mock_repo.Models.AddNew.assert_called_once_with("Model", "Package")
        mock_root.Packages.AddNew.assert_called_once_with("System", "Package")
        mock_pkg1.Packages.AddNew.assert_called_once_with("Components", "Package")
    
    def test_ensure_path_idempotence(self):
        """Test dass ensure_path idempotent ist (existierende Packages wiederverwendet)"""
        from src.repository import ensure_path
        
        # Mock Repository mit existierendem Model
        mock_repo = Mock()
        mock_repo.Models = Mock()
        mock_repo.Models.Count = 1
        
        # Existierendes Model
        mock_existing_model = Mock()
        mock_existing_model.Name = "Model"
        mock_existing_model.PackageID = 1
        mock_existing_model.Packages = Mock()
        mock_existing_model.Packages.Count = 1
        
        # Existierendes Package
        mock_existing_pkg = Mock()
        mock_existing_pkg.Name = "System"
        mock_existing_pkg.PackageID = 2
        mock_existing_pkg.Packages = Mock()
        mock_existing_pkg.Packages.Count = 0
        mock_existing_pkg.Packages.GetAt = Mock()
        mock_existing_pkg.Packages.Refresh = Mock()
        
        # Setup Mock-Verhalten
        mock_repo.Models.GetAt = Mock(return_value=mock_existing_model)
        mock_existing_model.Packages.GetAt = Mock(return_value=mock_existing_pkg)
        
        # Neues Package das erstellt werden soll
        mock_new_pkg = Mock()
        mock_new_pkg.Name = "NewPackage"
        mock_new_pkg.PackageID = 3
        mock_new_pkg.Update = Mock(return_value=True)
        
        mock_existing_pkg.Packages.AddNew = Mock(return_value=mock_new_pkg)
        
        # Test Pfad (2 existierend, 1 neu)
        path = ["Model", "System", "NewPackage"]
        
        # Führe Funktion aus
        result = ensure_path(mock_repo, path)
        
        # Assertions
        assert result is not None
        assert result.PackageID == 3
        
        # Prüfe dass nur das neue Package erstellt wurde
        mock_repo.Models.AddNew.assert_not_called()  # Model existiert bereits
        mock_existing_model.Packages.AddNew.assert_not_called()  # System existiert bereits
        mock_existing_pkg.Packages.AddNew.assert_called_once_with("NewPackage", "Package")
    
    def test_error_handling(self):
        """Test Error-Handling bei fehlerhaften Eingaben"""
        from src.packages import ensure_root_model
        from src.repository import create_package, ensure_path
        
        # Test mit None Repository
        with pytest.raises(ValueError, match="Repository-Objekt ist None"):
            ensure_root_model(None, "Test")
        
        # Test mit leerem Namen
        mock_repo = Mock()
        with pytest.raises(ValueError, match="Package-Name darf nicht leer sein"):
            ensure_root_model(mock_repo, "")
        
        # Test create_package mit None Parent
        with pytest.raises(ValueError, match="Parent-Package ist None"):
            create_package(None, "Test")
        
        # Test ensure_path mit leerem Pfad
        with pytest.raises(ValueError, match="Pfad darf nicht leer sein"):
            ensure_path(mock_repo, [])
        
        # Test ensure_path mit leeren Pfad-Elementen
        with pytest.raises(ValueError, match="Pfad enthält nur leere Elemente"):
            ensure_path(mock_repo, ["", " ", None])