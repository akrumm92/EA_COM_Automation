"""
Package-Management für Enterprise Architect
Stellt Funktionen zur Verwaltung von Packages bereit
"""

import logging
from typing import Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_root_model(repo: Any, name: str) -> Any:
    """
    Stellt sicher, dass ein Root-Model-Package existiert.
    Erstellt es falls es nicht vorhanden ist.
    
    Args:
        repo: EA Repository Objekt
        name: Name des Root-Model-Package
        
    Returns:
        Das Root-Model-Package Objekt
        
    Raises:
        Exception: Bei Fehlern in der COM-Kommunikation
    """
    if not repo:
        raise ValueError("Repository-Objekt ist None")
        
    if not name or not name.strip():
        raise ValueError("Package-Name darf nicht leer sein")
        
    name = name.strip()
    logger.info(f"Stelle Root-Model '{name}' sicher...")
    
    try:
        # Durchsuche vorhandene Models
        models = repo.Models
        
        for i in range(models.Count):
            model = models.GetAt(i)
            if model.Name == name:
                logger.info(f"Root-Model '{name}' bereits vorhanden (ID: {model.PackageID})")
                return model
        
        # Model existiert nicht, erstelle es
        logger.info(f"Erstelle neues Root-Model '{name}'...")
        
        # AddNew für Models Collection
        new_model = models.AddNew(name, "Package")
        
        if not new_model:
            raise Exception(f"Konnte Root-Model '{name}' nicht erstellen")
            
        # Update und Refresh
        success = new_model.Update()
        if not success:
            error_msg = repo.GetLastError() if hasattr(repo, 'GetLastError') else "Unbekannter Fehler"
            raise Exception(f"Fehler beim Update des Root-Models: {error_msg}")
            
        models.Refresh()
        
        logger.info(f"Root-Model '{name}' erfolgreich erstellt (ID: {new_model.PackageID})")
        return new_model
        
    except Exception as e:
        logger.error(f"Fehler beim Sicherstellen des Root-Models '{name}': {e}")
        raise