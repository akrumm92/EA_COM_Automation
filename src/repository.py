"""
Repository-Management für Enterprise Architect
Erweiterte Funktionen für Package-Verwaltung
"""

import logging
from typing import Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def create_package(parent_pkg: Any, name: str) -> Any:
    """
    Erstellt ein neues Package unterhalb eines Parent-Package.
    Verwendet AddNew, Update und Refresh für robuste Erstellung.
    
    Args:
        parent_pkg: Parent-Package Objekt
        name: Name des neuen Package
        
    Returns:
        Das neu erstellte oder existierende Package
        
    Raises:
        ValueError: Bei ungültigen Parametern
        Exception: Bei COM-Fehlern
    """
    if not parent_pkg:
        raise ValueError("Parent-Package ist None")
        
    if not name or not name.strip():
        raise ValueError("Package-Name darf nicht leer sein")
        
    name = name.strip()
    logger.debug(f"Erstelle Package '{name}' unter Parent ID {parent_pkg.PackageID}")
    
    try:
        # Prüfe ob Package bereits existiert (Idempotenz)
        packages = parent_pkg.Packages
        
        for i in range(packages.Count):
            pkg = packages.GetAt(i)
            if pkg.Name == name:
                logger.info(f"Package '{name}' existiert bereits (ID: {pkg.PackageID})")
                return pkg
        
        # Package existiert nicht, erstelle es
        logger.info(f"Erstelle neues Package '{name}'...")
        
        # AddNew auf Packages Collection
        new_package = packages.AddNew(name, "Package")
        
        if not new_package:
            raise Exception(f"Konnte Package '{name}' nicht erstellen")
        
        # Update das neue Package
        success = new_package.Update()
        if not success:
            # Versuche Fehler zu ermitteln
            error_msg = "Update fehlgeschlagen"
            if hasattr(parent_pkg, 'Repository'):
                repo = parent_pkg.Repository
                if hasattr(repo, 'GetLastError'):
                    error_msg = repo.GetLastError()
            raise Exception(f"Fehler beim Update des Package '{name}': {error_msg}")
        
        # Refresh der Collection
        packages.Refresh()
        
        logger.info(f"Package '{name}' erfolgreich erstellt (ID: {new_package.PackageID})")
        return new_package
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Package '{name}': {e}")
        raise


def ensure_path(repo: Any, path: List[str]) -> Any:
    """
    Stellt sicher, dass ein kompletter Pfad von verschachtelten Packages existiert.
    Erstellt fehlende Packages automatisch.
    
    Args:
        repo: EA Repository Objekt
        path: Liste von Package-Namen die den Pfad bilden
              z.B. ["Model", "System", "Components"]
        
    Returns:
        Das letzte Package im Pfad
        
    Raises:
        ValueError: Bei ungültigen Parametern
        Exception: Bei COM-Fehlern
    """
    if not repo:
        raise ValueError("Repository-Objekt ist None")
        
    if not path:
        raise ValueError("Pfad darf nicht leer sein")
        
    # Bereinige Pfad-Elemente
    clean_path = [p.strip() for p in path if p and p.strip()]
    
    if not clean_path:
        raise ValueError("Pfad enthält nur leere Elemente")
        
    logger.info(f"Stelle Pfad sicher: {' -> '.join(clean_path)}")
    
    try:
        # Importiere packages Modul für ensure_root_model
        from .packages import ensure_root_model
        
        # Erstes Element ist das Root-Model
        root_name = clean_path[0]
        current_pkg = ensure_root_model(repo, root_name)
        
        # Durchlaufe restlichen Pfad und erstelle Packages
        for i, pkg_name in enumerate(clean_path[1:], 1):
            logger.debug(f"Verarbeite Pfad-Element {i}/{len(clean_path)}: '{pkg_name}'")
            current_pkg = create_package(current_pkg, pkg_name)
            
        logger.info(f"Pfad erfolgreich sichergestellt. Letztes Package: '{current_pkg.Name}' (ID: {current_pkg.PackageID})")
        return current_pkg
        
    except Exception as e:
        logger.error(f"Fehler beim Sicherstellen des Pfads {clean_path}: {e}")
        raise


def find_package_by_path(repo: Any, path: List[str]) -> Optional[Any]:
    """
    Sucht ein Package anhand eines Pfads.
    Gibt None zurück wenn der Pfad nicht vollständig existiert.
    
    Args:
        repo: EA Repository Objekt
        path: Liste von Package-Namen die den Pfad bilden
        
    Returns:
        Das Package am Ende des Pfads oder None
    """
    if not repo or not path:
        return None
        
    try:
        # Erstes Element in Models suchen
        models = repo.Models
        current_pkg = None
        
        for i in range(models.Count):
            model = models.GetAt(i)
            if model.Name == path[0]:
                current_pkg = model
                break
                
        if not current_pkg:
            return None
            
        # Restlichen Pfad durchlaufen
        for pkg_name in path[1:]:
            found = False
            packages = current_pkg.Packages
            
            for i in range(packages.Count):
                pkg = packages.GetAt(i)
                if pkg.Name == pkg_name:
                    current_pkg = pkg
                    found = True
                    break
                    
            if not found:
                return None
                
        return current_pkg
        
    except Exception as e:
        logger.error(f"Fehler beim Suchen des Package-Pfads {path}: {e}")
        return None