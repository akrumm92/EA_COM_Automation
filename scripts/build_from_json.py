#!/usr/bin/env python3
"""
Orchestrator zum Erstellen von EA-Modellen aus JSON-Spezifikationen.

Verwendung:
    python scripts/build_from_json.py --repo "C:\\path\\to\\project.qea" --json "examples/coffee_machine.json"
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from typing import Dict, List, Optional, Any

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

import win32com.client
from ea_automation.json_io import load_model_spec
from ea_automation.elements import create_element, add_attribute, add_operation
from ea_automation.exceptions import EAError

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelBuilder:
    """Orchestrator für den Aufbau von EA-Modellen aus JSON-Spezifikationen."""
    
    def __init__(self, repo_path: str, spec: Dict):
        """
        Initialisiert den ModelBuilder.
        
        Args:
            repo_path: Pfad zur EA Repository-Datei
            spec: Model-Spezifikation (aus JSON geladen)
        """
        self.repo_path = repo_path
        self.spec = spec
        self.repo = None
        self.created_packages = {}  # Package-Name -> EA Package Objekt
        self.created_elements = {}  # Element-Name -> EA Element Objekt
        self.created_connectors = []
        
    def connect(self) -> bool:
        """Verbindet mit dem EA Repository."""
        try:
            logger.info(f"Verbinde mit Repository: {self.repo_path}")
            self.repo = win32com.client.Dispatch("EA.Repository")
            
            if not self.repo.OpenFile(str(self.repo_path)):
                logger.error("Konnte Repository nicht öffnen")
                return False
            
            logger.info("[OK] Repository geöffnet")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Verbinden: {e}")
            return False
    
    def disconnect(self):
        """Trennt die Verbindung zum Repository."""
        if self.repo:
            try:
                self.repo.CloseFile()
                logger.info("[OK] Repository geschlossen")
            except:
                pass
    
    def ensure_root_model(self) -> Any:
        """
        Stellt sicher, dass das Root-Model existiert.
        
        Returns:
            EA Model Objekt
        """
        model_name = self.spec.get('model', 'Model')
        logger.info(f"\n1. ROOT MODEL: {model_name}")
        logger.info("-" * 40)
        
        try:
            models = self.repo.Models
            
            # Suche existierendes Model
            for i in range(models.Count):
                model = models.GetAt(i)
                if model.Name == model_name:
                    logger.info(f"[OK] Model existiert bereits: {model_name}")
                    return model
            
            # Erstelle neues Model
            logger.info(f"Erstelle neues Model: {model_name}")
            new_model = models.AddNew(model_name, "Package")
            new_model.Update()
            models.Refresh()
            logger.info(f"[OK] Model erstellt: {model_name}")
            return new_model
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Root-Models: {e}")
            raise EAError(f"Fehler beim Erstellen des Root-Models: {e}")
    
    def create_packages(self, model: Any):
        """
        Erstellt alle Packages aus der Spezifikation.
        
        Args:
            model: EA Model Objekt
        """
        packages = self.spec.get('packages', [])
        if not packages:
            logger.info("\n2. PACKAGES: Keine Packages definiert")
            return
        
        logger.info(f"\n2. PACKAGES: {len(packages)} zu erstellen")
        logger.info("-" * 40)
        
        model_packages = model.Packages
        
        for package_name in packages:
            try:
                # Prüfe ob Package existiert
                exists = False
                for i in range(model_packages.Count):
                    pkg = model_packages.GetAt(i)
                    if pkg.Name == package_name:
                        logger.info(f"[EXISTS] Package: {package_name}")
                        self.created_packages[package_name] = pkg
                        exists = True
                        break
                
                if not exists:
                    # Erstelle neues Package
                    logger.info(f"[CREATE] Package: {package_name}")
                    new_pkg = model_packages.AddNew(package_name, "Package")
                    new_pkg.Update()
                    self.created_packages[package_name] = new_pkg
                    
            except Exception as e:
                logger.error(f"[ERROR] Package '{package_name}': {e}")
        
        model_packages.Refresh()
        logger.info(f"[OK] {len(self.created_packages)} Packages verarbeitet")
    
    def create_elements(self):
        """Erstellt alle Elemente aus der Spezifikation."""
        elements = self.spec.get('elements', [])
        if not elements:
            logger.info("\n3. ELEMENTS: Keine Elemente definiert")
            return
        
        logger.info(f"\n3. ELEMENTS: {len(elements)} zu erstellen")
        logger.info("-" * 40)
        
        for elem_spec in elements:
            try:
                package_name = elem_spec['package']
                elem_name = elem_spec['name']
                elem_type = elem_spec['type']
                
                logger.info(f"\n[ELEMENT] {elem_name} ({elem_type}) in {package_name}")
                
                # Finde Target-Package
                target_package = self._find_or_create_package(package_name)
                if not target_package:
                    logger.error(f"  Package '{package_name}' nicht gefunden")
                    continue
                
                # Erstelle Element (idempotent)
                element = create_element(
                    target_package,
                    elem_name,
                    elem_type,
                    stereotype=elem_spec.get('stereotype'),
                    notes=elem_spec.get('notes')
                )
                
                self.created_elements[elem_name] = element
                
                # Füge Attribute hinzu
                for attr in elem_spec.get('attributes', []):
                    add_attribute(element, attr['name'], attr.get('type', 'String'))
                    logger.info(f"  [ATTR] {attr['name']}")
                
                # Füge Operationen hinzu
                for op in elem_spec.get('operations', []):
                    add_operation(element, op['name'], op.get('returnType', 'void'))
                    logger.info(f"  [OP] {op['name']}")
                
                logger.info(f"  [OK] Element erstellt/aktualisiert")
                
            except Exception as e:
                logger.error(f"  [ERROR] Element '{elem_spec.get('name', '?')}': {e}")
        
        logger.info(f"\n[OK] {len(self.created_elements)} Elemente verarbeitet")
    
    def create_connectors(self):
        """Erstellt alle Connectors aus der Spezifikation."""
        connectors = self.spec.get('connectors', [])
        if not connectors:
            logger.info("\n4. CONNECTORS: Keine Connectors definiert")
            return
        
        logger.info(f"\n4. CONNECTORS: {len(connectors)} zu erstellen")
        logger.info("-" * 40)
        
        for conn_spec in connectors:
            try:
                conn_type = conn_spec['type']
                client_name = conn_spec['client']
                supplier_name = conn_spec['supplier']
                
                logger.info(f"\n[CONNECTOR] {client_name} --{conn_type}--> {supplier_name}")
                
                # Finde Client und Supplier Elemente
                client_elem = self._find_element(client_name)
                supplier_elem = self._find_element(supplier_name)
                
                if not client_elem:
                    logger.error(f"  Client-Element '{client_name}' nicht gefunden")
                    continue
                    
                if not supplier_elem:
                    logger.error(f"  Supplier-Element '{supplier_name}' nicht gefunden")
                    continue
                
                # Prüfe ob Connector bereits existiert
                connectors_collection = client_elem.Connectors
                exists = False
                
                for i in range(connectors_collection.Count):
                    conn = connectors_collection.GetAt(i)
                    if (conn.Type == conn_type and 
                        conn.SupplierID == supplier_elem.ElementID):
                        logger.info(f"  [EXISTS] Connector existiert bereits")
                        exists = True
                        break
                
                if not exists:
                    # Erstelle neuen Connector
                    new_conn = connectors_collection.AddNew(
                        conn_spec.get('name', ''),
                        conn_type
                    )
                    new_conn.SupplierID = supplier_elem.ElementID
                    
                    if conn_spec.get('stereotype'):
                        new_conn.Stereotype = conn_spec['stereotype']
                    if conn_spec.get('notes'):
                        new_conn.Notes = conn_spec['notes']
                    
                    new_conn.Update()
                    connectors_collection.Refresh()
                    
                    self.created_connectors.append(new_conn)
                    logger.info(f"  [OK] Connector erstellt")
                
            except Exception as e:
                logger.error(f"  [ERROR] Connector: {e}")
        
        logger.info(f"\n[OK] {len(self.created_connectors)} Connectors verarbeitet")
    
    def create_diagrams(self):
        """Erstellt optionale Diagramme aus der Spezifikation."""
        diagrams = self.spec.get('diagrams', [])
        if not diagrams:
            logger.info("\n5. DIAGRAMS: Keine Diagramme definiert")
            return
        
        logger.info(f"\n5. DIAGRAMS: {len(diagrams)} zu erstellen")
        logger.info("-" * 40)
        
        for diag_spec in diagrams:
            try:
                package_name = diag_spec['package']
                diag_name = diag_spec['name']
                diag_type = diag_spec['type']
                
                logger.info(f"\n[DIAGRAM] {diag_name} ({diag_type}) in {package_name}")
                
                # Finde Target-Package
                target_package = self._find_or_create_package(package_name)
                if not target_package:
                    logger.error(f"  Package '{package_name}' nicht gefunden")
                    continue
                
                # Erstelle Diagramm
                diagrams_collection = target_package.Diagrams
                diagram = diagrams_collection.AddNew(diag_name, diag_type)
                diagram.Update()
                
                # Füge Elemente zum Diagramm hinzu
                for elem_name in diag_spec.get('elements', []):
                    element = self._find_element(elem_name)
                    if element:
                        diag_obj = diagram.DiagramObjects.AddNew("", "")
                        diag_obj.ElementID = element.ElementID
                        diag_obj.Update()
                        logger.info(f"  [ADD] Element: {elem_name}")
                    else:
                        logger.warning(f"  [SKIP] Element nicht gefunden: {elem_name}")
                
                diagrams_collection.Refresh()
                logger.info(f"  [OK] Diagramm erstellt")
                
            except Exception as e:
                logger.error(f"  [ERROR] Diagramm '{diag_spec.get('name', '?')}': {e}")
    
    def _find_or_create_package(self, package_name: str) -> Optional[Any]:
        """
        Findet ein Package oder erstellt es wenn nötig.
        
        Args:
            package_name: Name des Packages
        
        Returns:
            EA Package Objekt oder None
        """
        # Prüfe Cache
        if package_name in self.created_packages:
            return self.created_packages[package_name]
        
        # Suche in allen Models
        try:
            models = self.repo.Models
            for i in range(models.Count):
                model = models.GetAt(i)
                packages = model.Packages
                for j in range(packages.Count):
                    pkg = packages.GetAt(j)
                    if pkg.Name == package_name:
                        self.created_packages[package_name] = pkg
                        return pkg
            
            # Package nicht gefunden - erstelle es im ersten Model
            if models.Count > 0:
                model = models.GetAt(0)
                logger.info(f"  [AUTO-CREATE] Package: {package_name}")
                new_pkg = model.Packages.AddNew(package_name, "Package")
                new_pkg.Update()
                model.Packages.Refresh()
                self.created_packages[package_name] = new_pkg
                return new_pkg
                
        except Exception as e:
            logger.error(f"Fehler beim Suchen/Erstellen von Package '{package_name}': {e}")
        
        return None
    
    def _find_element(self, element_name: str) -> Optional[Any]:
        """
        Findet ein Element nach Name.
        
        Args:
            element_name: Name des Elements
        
        Returns:
            EA Element Objekt oder None
        """
        # Prüfe Cache
        if element_name in self.created_elements:
            return self.created_elements[element_name]
        
        # Suche in allen Packages
        for pkg in self.created_packages.values():
            try:
                elements = pkg.Elements
                for i in range(elements.Count):
                    elem = elements.GetAt(i)
                    if elem.Name == element_name:
                        self.created_elements[element_name] = elem
                        return elem
            except:
                continue
        
        # Globale Suche als Fallback
        logger.debug(f"Element '{element_name}' nicht in bekannten Packages - globale Suche...")
        return None
    
    def build(self) -> bool:
        """
        Führt den kompletten Build-Prozess aus.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # 1. Root Model
            model = self.ensure_root_model()
            
            # 2. Packages
            self.create_packages(model)
            
            # 3. Elements
            self.create_elements()
            
            # 4. Connectors
            self.create_connectors()
            
            # 5. Diagrams (optional)
            self.create_diagrams()
            
            return True
            
        except Exception as e:
            logger.error(f"Build-Fehler: {e}")
            return False


def parse_arguments():
    """Parse Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description='Erstellt EA-Modelle aus JSON-Spezifikationen'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='Pfad zur EA Repository-Datei (.qea, .eapx, etc.)'
    )
    
    parser.add_argument(
        '--json',
        type=str,
        required=True,
        help='Pfad zur JSON Model-Spezifikation'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Aktiviert Debug-Logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validiert nur die Spezifikation ohne Änderungen'
    )
    
    return parser.parse_args()


def main():
    """Hauptfunktion."""
    args = parse_arguments()
    
    # Setze Log-Level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Header
    logger.info("=" * 60)
    logger.info("EA MODEL BUILDER")
    logger.info("=" * 60)
    
    try:
        # Lade und validiere Spezifikation
        logger.info(f"\nLade Spezifikation: {args.json}")
        spec = load_model_spec(args.json)
        
        if args.dry_run:
            logger.info("\n[DRY-RUN] Spezifikation ist valide. Keine Änderungen vorgenommen.")
            sys.exit(0)
        
        # Initialisiere Builder
        builder = ModelBuilder(args.repo, spec)
        
        # Verbinde mit Repository
        if not builder.connect():
            logger.error("Konnte nicht mit Repository verbinden")
            sys.exit(1)
        
        try:
            # Führe Build aus
            success = builder.build()
            
            # Zusammenfassung
            logger.info("\n" + "=" * 60)
            logger.info("ZUSAMMENFASSUNG")
            logger.info("=" * 60)
            
            if success:
                logger.info(f"✓ Model: {spec.get('model', 'Model')}")
                logger.info(f"✓ Packages: {len(builder.created_packages)}")
                logger.info(f"✓ Elements: {len(builder.created_elements)}")
                logger.info(f"✓ Connectors: {len(builder.created_connectors)}")
                logger.info("\n[ERFOLG] Model erfolgreich erstellt!")
            else:
                logger.error("\n[FEHLER] Build fehlgeschlagen")
                sys.exit(1)
            
        finally:
            # Trenne Verbindung
            builder.disconnect()
        
    except EAError as e:
        logger.error(f"\nValidierungsfehler: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nUnerwarteter Fehler: {e}")
        import traceback
        if args.debug:
            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()