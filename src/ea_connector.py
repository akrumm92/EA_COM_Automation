"""
EA Connector mit Workaround für Internal Application Error
Verwendet EA.App für stabilere Verbindung
"""

import time
import logging
from typing import Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EAConnector:
    """
    Robuster EA-Connector mit Workarounds für bekannte Probleme
    """
    
    def __init__(self):
        self.ea_app = None
        self.repository = None
        self.is_connected = False
        
    def connect(self, file_path: Optional[str] = None, retry_count: int = 3) -> bool:
        """
        Verbindet mit EA Repository mit Workarounds
        
        Args:
            file_path: Pfad zur EA-Datei (optional)
            retry_count: Anzahl Wiederholungsversuche
            
        Returns:
            True wenn erfolgreich verbunden
        """
        for attempt in range(retry_count):
            try:
                logger.info(f"Verbindungsversuch {attempt + 1}/{retry_count}...")
                
                import win32com.client
                
                # Workaround 1: Verwende EA.App statt direkt Repository
                logger.debug("Erstelle EA.App Objekt...")
                self.ea_app = win32com.client.Dispatch("EA.App")
                
                # Workaround 2: Warte auf EA-Initialisierung
                logger.debug("Warte auf EA-Initialisierung...")
                time.sleep(1)
                
                # Workaround 3: Hole Repository über App
                try:
                    self.repository = self.ea_app.Repository
                    logger.debug("Repository über EA.App erhalten")
                except:
                    # Fallback: Direkte Repository-Erstellung
                    logger.debug("Fallback: Erstelle Repository direkt")
                    self.repository = win32com.client.Dispatch("EA.Repository")
                
                # Wenn Datei angegeben, öffne sie
                if file_path:
                    success = self._open_file(file_path)
                    if not success and attempt < retry_count - 1:
                        logger.warning(f"Öffnen fehlgeschlagen, versuche erneut...")
                        time.sleep(2)
                        continue
                        
                self.is_connected = True
                logger.info("✓ EA-Verbindung erfolgreich hergestellt")
                return True
                
            except Exception as e:
                logger.error(f"Verbindungsfehler (Versuch {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    
        return False
    
    def _open_file(self, file_path: str) -> bool:
        """
        Öffnet EA-Datei mit verschiedenen Methoden
        """
        file_path = str(Path(file_path).resolve())
        
        # Methode 1: Standard OpenFile
        try:
            logger.debug(f"Versuche OpenFile: {file_path}")
            success = self.repository.OpenFile(file_path)
            if success:
                logger.info(f"✓ Datei geöffnet: {file_path}")
                return True
        except Exception as e:
            logger.debug(f"OpenFile fehlgeschlagen: {e}")
        
        # Methode 2: OpenFile2 (für spezielle Fälle)
        try:
            logger.debug("Versuche OpenFile2...")
            success = self.repository.OpenFile2(file_path, "", "")
            if success:
                logger.info(f"✓ Datei geöffnet mit OpenFile2: {file_path}")
                return True
        except Exception as e:
            logger.debug(f"OpenFile2 fehlgeschlagen: {e}")
            
        return False
    
    def get_models_safe(self) -> Optional[Any]:
        """
        Sicherer Zugriff auf Models mit Error-Handling
        """
        if not self.repository:
            logger.error("Kein Repository vorhanden")
            return None
            
        try:
            models = self.repository.Models
            logger.debug(f"Models-Collection erhalten (Count: {models.Count})")
            return models
        except Exception as e:
            if "Internal application error" in str(e):
                logger.error("EA Internal Error - Mögliche Lösungen:")
                logger.error("1. Starte EA manuell und öffne ein Projekt")
                logger.error("2. Prüfe EA-Lizenz")
                logger.error("3. Verwende alternative Methoden (SQL, GetPackageByID)")
            else:
                logger.error(f"Fehler beim Models-Zugriff: {e}")
            return None
    
    def create_model_safe(self, name: str) -> Optional[Any]:
        """
        Erstellt Model mit Fallback-Strategien
        """
        models = self.get_models_safe()
        
        if models:
            # Standard-Methode
            try:
                model = models.AddNew(name, "Package")
                if model:
                    model.Update()
                    models.Refresh()
                    logger.info(f"✓ Model '{name}' erstellt")
                    return model
            except Exception as e:
                logger.error(f"AddNew fehlgeschlagen: {e}")
        
        # Fallback: SQL Insert
        try:
            logger.info("Versuche SQL-Fallback für Model-Erstellung...")
            sql = f"INSERT INTO t_package (Name, Parent_ID) VALUES ('{name}', 0)"
            self.repository.Execute(sql)
            logger.info(f"✓ Model '{name}' per SQL erstellt")
            
            # Hole das erstellte Model
            sql = f"SELECT Package_ID FROM t_package WHERE Name = '{name}' AND Parent_ID = 0"
            result = self.repository.SQLQuery(sql)
            # Parse XML result und hole Package
            # ... (XML parsing code)
            
        except Exception as e:
            logger.error(f"SQL-Fallback fehlgeschlagen: {e}")
            
        return None
    
    def disconnect(self):
        """
        Trennt Verbindung zu EA
        """
        try:
            if self.repository:
                self.repository.CloseFile()
                logger.info("Repository geschlossen")
                
            if self.ea_app:
                try:
                    self.ea_app.Exit()
                except:
                    pass  # EA.App.Exit kann fehlschlagen
                    
            self.is_connected = False
            logger.info("EA-Verbindung getrennt")
            
        except Exception as e:
            logger.error(f"Fehler beim Trennen: {e}")
    
    def __enter__(self):
        """Context Manager Support"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Cleanup"""
        self.disconnect()


def get_repository(file_path: Optional[str] = None) -> Optional[Any]:
    """
    Hilfsfunktion zum schnellen Repository-Zugriff
    
    Args:
        file_path: Pfad zur EA-Datei
        
    Returns:
        Repository-Objekt oder None
    """
    connector = EAConnector()
    
    # Versuche aus Umgebungsvariable wenn kein Pfad angegeben
    if not file_path:
        import os
        file_path = os.getenv('EA_PROJECT_PATH')
        
    if connector.connect(file_path):
        return connector.repository
    
    return None


# Beispiel-Verwendung
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Mit Context Manager
    with EAConnector() as ea:
        if ea.connect():
            print("Verbunden!")
            models = ea.get_models_safe()
            if models:
                print(f"Models gefunden: {models.Count}")
        else:
            print("Verbindung fehlgeschlagen")