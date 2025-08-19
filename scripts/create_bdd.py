#!/usr/bin/env python3
"""
CLI Script zum Erstellen von Block Definition Diagrams (BDD) in EA.

Verwendung:
    python scripts/create_bdd.py --repo "C:\\path\\to\\project.qea" --package "02_Architecture" --diagram "BDD CoffeeMachine" --elements "CoffeeMachine;Boiler;Pump"
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from typing import List, Optional, Any

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

import win32com.client
from ea_automation.diagrams import create_diagram, auto_place_grid, open_diagram_in_ea
from ea_automation.exceptions import EAError

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description='Erstellt ein Block Definition Diagram (BDD) in EA'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='Pfad zur EA Repository-Datei (.qea, .eapx, etc.)'
    )
    
    parser.add_argument(
        '--package',
        type=str,
        required=True,
        help='Name des Packages für das Diagramm (z.B. "02_Architecture")'
    )
    
    parser.add_argument(
        '--diagram',
        type=str,
        required=True,
        help='Name des zu erstellenden Diagramms (z.B. "BDD CoffeeMachine")'
    )
    
    parser.add_argument(
        '--elements',
        type=str,
        required=True,
        help='Semikolon-getrennte Liste von Element-Namen (z.B. "Motor;Pumpe;Heizelement")'
    )
    
    parser.add_argument(
        '--type',
        type=str,
        default='SysML1.4::BlockDefinition',
        help='Diagramm-Typ (default: SysML1.4::BlockDefinition, Fallback: Class)'
    )
    
    parser.add_argument(
        '--cols',
        type=int,
        default=3,
        help='Anzahl Spalten für Auto-Layout (default: 3)'
    )
    
    parser.add_argument(
        '--cell-width',
        type=int,
        default=300,
        help='Breite einer Zelle in Pixeln (default: 300)'
    )
    
    parser.add_argument(
        '--cell-height',
        type=int,
        default=220,
        help='Höhe einer Zelle in Pixeln (default: 220)'
    )
    
    parser.add_argument(
        '--margin',
        type=int,
        default=50,
        help='Abstand zwischen Elementen in Pixeln (default: 50)'
    )
    
    parser.add_argument(
        '--open',
        action='store_true',
        help='Versucht das Diagramm in EA zu öffnen (falls GUI verfügbar)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Aktiviert Debug-Logging'
    )
    
    return parser.parse_args()


def find_package(repo: Any, package_name: str) -> Optional[Any]:
    """
    Sucht ein Package im Repository.
    
    Args:
        repo: EA Repository Objekt
        package_name: Name des Packages
    
    Returns:
        EA Package Objekt oder None
    """
    try:
        models = repo.Models
        for i in range(models.Count):
            model = models.GetAt(i)
            
            # Prüfe Model selbst
            if model.Name == package_name:
                return model
            
            # Suche in Sub-Packages
            packages = model.Packages
            for j in range(packages.Count):
                pkg = packages.GetAt(j)
                if pkg.Name == package_name:
                    return pkg
                
                # Rekursive Suche in Sub-Sub-Packages (1 Ebene tief)
                sub_packages = pkg.Packages
                for k in range(sub_packages.Count):
                    sub_pkg = sub_packages.GetAt(k)
                    if sub_pkg.Name == package_name:
                        return sub_pkg
        
        return None
        
    except Exception as e:
        logger.error(f"Fehler beim Suchen des Packages: {e}")
        return None


def find_elements(repo: Any, element_names: List[str], package: Optional[Any] = None) -> List[Any]:
    """
    Sucht Elemente im Repository oder Package.
    
    Args:
        repo: EA Repository Objekt
        element_names: Liste von Element-Namen
        package: Optional - Package zum Suchen (None = global)
    
    Returns:
        Liste von gefundenen EA Element Objekten
    """
    found_elements = []
    
    # Definiere Suchbereich
    packages_to_search = []
    if package:
        packages_to_search.append(package)
    else:
        # Globale Suche - alle Packages
        models = repo.Models
        for i in range(models.Count):
            model = models.GetAt(i)
            packages = model.Packages
            for j in range(packages.Count):
                packages_to_search.append(packages.GetAt(j))
    
    # Suche Elemente
    for elem_name in element_names:
        elem_name = elem_name.strip()
        found = False
        
        for pkg in packages_to_search:
            try:
                elements = pkg.Elements
                for i in range(elements.Count):
                    elem = elements.GetAt(i)
                    if elem.Name == elem_name:
                        found_elements.append(elem)
                        logger.info(f"Element gefunden: {elem_name} (ID: {elem.ElementID})")
                        found = True
                        break
            except:
                continue
            
            if found:
                break
        
        if not found:
            logger.warning(f"Element nicht gefunden: {elem_name}")
    
    return found_elements


def main():
    """Hauptfunktion."""
    args = parse_arguments()
    
    # Setze Log-Level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validiere Repository-Pfad
    repo_path = Path(args.repo)
    if not repo_path.exists():
        logger.error(f"Repository-Datei nicht gefunden: {repo_path}")
        sys.exit(1)
    
    # Parse Element-Namen
    element_names = [name.strip() for name in args.elements.split(';') if name.strip()]
    if not element_names:
        logger.error("Keine Element-Namen angegeben")
        sys.exit(1)
    
    # Header
    logger.info("=" * 60)
    logger.info("EA BLOCK DEFINITION DIAGRAM CREATOR")
    logger.info("=" * 60)
    logger.info(f"Repository: {repo_path}")
    logger.info(f"Package: {args.package}")
    logger.info(f"Diagramm: {args.diagram}")
    logger.info(f"Diagramm-Typ: {args.type}")
    logger.info(f"Elemente: {len(element_names)}")
    logger.info(f"Layout: {args.cols} Spalten, {args.cell_width}x{args.cell_height}px")
    
    try:
        # Verbinde mit Repository
        logger.info("\nVerbinde mit EA Repository...")
        repo = win32com.client.Dispatch("EA.Repository")
        
        if not repo.OpenFile(str(repo_path)):
            logger.error("Konnte Repository nicht öffnen")
            sys.exit(1)
        
        logger.info("[OK] Repository geöffnet")
        
        # Finde Package
        logger.info(f"\nSuche Package: {args.package}")
        target_package = find_package(repo, args.package)
        
        if not target_package:
            logger.error(f"Package '{args.package}' nicht gefunden")
            
            # Liste verfügbare Packages
            logger.info("\nVerfügbare Packages:")
            models = repo.Models
            for i in range(models.Count):
                model = models.GetAt(i)
                logger.info(f"  Model: {model.Name}")
                packages = model.Packages
                for j in range(packages.Count):
                    pkg = packages.GetAt(j)
                    logger.info(f"    - {pkg.Name}")
            
            repo.CloseFile()
            sys.exit(1)
        
        logger.info(f"[OK] Package gefunden: {target_package.Name}")
        
        # Finde Elemente
        logger.info(f"\nSuche {len(element_names)} Elemente...")
        elements = find_elements(repo, element_names, target_package)
        
        if not elements:
            logger.error("Keine Elemente gefunden!")
            repo.CloseFile()
            sys.exit(1)
        
        logger.info(f"[OK] {len(elements)} Elemente gefunden")
        
        # Erstelle Diagramm
        logger.info(f"\nErstelle Diagramm: {args.diagram}")
        diagram = create_diagram(target_package, args.diagram, args.type)
        
        if not diagram:
            logger.error("Konnte Diagramm nicht erstellen")
            repo.CloseFile()
            sys.exit(1)
        
        logger.info(f"[OK] Diagramm erstellt/gefunden")
        
        # Platziere Elemente auf Diagramm
        logger.info(f"\nPlatziere Elemente im {args.cols}-Spalten-Raster...")
        diagram_objects = auto_place_grid(
            diagram,
            elements,
            cols=args.cols,
            cell_w=args.cell_width,
            cell_h=args.cell_height,
            margin=args.margin
        )
        
        logger.info(f"[OK] {len(diagram_objects)} Elemente platziert")
        
        # Optional: Öffne Diagramm in EA
        if args.open:
            logger.info("\nVersuche Diagramm in EA zu öffnen...")
            if open_diagram_in_ea(repo, diagram):
                logger.info("[OK] Diagramm in EA geöffnet")
            else:
                logger.info("[INFO] Konnte Diagramm nicht öffnen (GUI nicht verfügbar?)")
        
        # Speichere und schließe
        try:
            # Versuche Repository zu speichern
            repo.SaveDiagram(diagram.DiagramID)
            logger.debug("Diagramm gespeichert")
        except:
            pass  # SaveDiagram nicht immer verfügbar
        
        # Zusammenfassung
        logger.info("\n" + "=" * 60)
        logger.info("ZUSAMMENFASSUNG")
        logger.info("=" * 60)
        logger.info(f"✓ Diagramm: {args.diagram}")
        logger.info(f"✓ Package: {args.package}")
        logger.info(f"✓ Elemente platziert: {len(diagram_objects)}/{len(element_names)}")
        
        if len(diagram_objects) < len(element_names):
            missing = len(element_names) - len(diagram_objects)
            logger.warning(f"⚠ {missing} Elemente konnten nicht platziert werden")
        
        logger.info("\n[ERFOLG] Block Definition Diagram erstellt!")
        logger.info("\nHinweis: Öffne EA und navigiere zum Diagramm:")
        logger.info(f"  {args.package} -> {args.diagram}")
        
        # Repository schließen
        repo.CloseFile()
        logger.info("\n[OK] Repository geschlossen")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        import traceback
        if args.debug:
            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()