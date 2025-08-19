#!/usr/bin/env python3
"""
BDD Demo Test Script - Erstellt Block Definition Diagrams für CoffeeMachine

Dieses Script demonstriert die BDD-Erstellung in verschiedenen Layouts und
kann als Vorlage für eigene BDD-Tests verwendet werden.

Verwendung:
    python scripts/test_bdd_demo.py --repo "C:\\path\\to\\project.qea"
    python scripts/test_bdd_demo.py --repo "test.qea" --create-elements
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from typing import List, Dict, Any
import time

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

import win32com.client
from ea_automation.elements import create_element, add_attribute, add_operation
from ea_automation.diagrams import create_diagram, auto_place_grid, open_diagram_in_ea
from ea_automation.exceptions import EAError

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BDDTestSuite:
    """Test Suite für Block Definition Diagram Erstellung."""
    
    def __init__(self, repo_path: str):
        """
        Initialisiert die BDD Test Suite.
        
        Args:
            repo_path: Pfad zur EA Repository-Datei
        """
        self.repo_path = repo_path
        self.repo = None
        self.target_package = None
        self.created_elements = {}
        self.created_diagrams = []
        
        # CoffeeMachine Element-Definitionen
        self.coffee_elements = {
            "CoffeeMachine": {
                "type": "SysML1.4::Block",
                "stereotype": "block", 
                "notes": "Main coffee machine system block",
                "attributes": [
                    {"name": "powerState", "type": "Boolean"},
                    {"name": "waterLevel", "type": "Double"},
                    {"name": "coffeeBeansLevel", "type": "Double"}
                ],
                "operations": [
                    {"name": "powerOn", "returnType": "void"},
                    {"name": "powerOff", "returnType": "void"},
                    {"name": "brewCoffee", "returnType": "Boolean"}
                ]
            },
            "Boiler": {
                "type": "SysML1.4::Block",
                "stereotype": "block",
                "notes": "Water heating subsystem",
                "attributes": [
                    {"name": "temperature", "type": "Double"},
                    {"name": "capacity", "type": "Double"},
                    {"name": "isHeating", "type": "Boolean"}
                ],
                "operations": [
                    {"name": "heatWater", "returnType": "void"},
                    {"name": "getTemperature", "returnType": "Double"},
                    {"name": "maintainTemperature", "returnType": "void"}
                ]
            },
            "Pump": {
                "type": "SysML1.4::Block",
                "stereotype": "block",
                "notes": "Water pump for coffee extraction",
                "attributes": [
                    {"name": "flowRate", "type": "Double"},
                    {"name": "pressure", "type": "Double"},
                    {"name": "isRunning", "type": "Boolean"}
                ],
                "operations": [
                    {"name": "start", "returnType": "void"},
                    {"name": "stop", "returnType": "void"},
                    {"name": "setPressure", "returnType": "void"}
                ]
            },
            "Grinder": {
                "type": "SysML1.4::Block",
                "stereotype": "block", 
                "notes": "Coffee bean grinder subsystem",
                "attributes": [
                    {"name": "grindLevel", "type": "Integer"},
                    {"name": "isGrinding", "type": "Boolean"}
                ],
                "operations": [
                    {"name": "grindBeans", "returnType": "void"},
                    {"name": "setGrindLevel", "returnType": "void"}
                ]
            },
            "WaterTank": {
                "type": "SysML1.4::Block",
                "stereotype": "block",
                "notes": "Water storage tank component",
                "attributes": [
                    {"name": "capacity", "type": "Double"},
                    {"name": "currentLevel", "type": "Double"}
                ],
                "operations": [
                    {"name": "fill", "returnType": "void"},
                    {"name": "checkLevel", "returnType": "Double"}
                ]
            },
            "ControlUnit": {
                "type": "Class",
                "stereotype": "controller",
                "notes": "Main control unit for coffee machine",
                "attributes": [
                    {"name": "currentState", "type": "String"},
                    {"name": "selectedProgram", "type": "Integer"}
                ],
                "operations": [
                    {"name": "executeProgram", "returnType": "void"},
                    {"name": "checkSensors", "returnType": "Boolean"},
                    {"name": "displayStatus", "returnType": "void"}
                ]
            }
        }
        
        # BDD Test Cases
        self.test_cases = {
            "Compact_Layout": {
                "description": "Kompaktes 3x2 Grid Layout",
                "elements": ["CoffeeMachine", "Boiler", "Pump", "Grinder", "WaterTank", "ControlUnit"],
                "cols": 3,
                "cell_width": 280,
                "cell_height": 200,
                "margin": 40
            },
            "Wide_Layout": {
                "description": "Breites 4x2 Grid Layout",
                "elements": ["CoffeeMachine", "Boiler", "Pump", "Grinder", "WaterTank", "ControlUnit"],
                "cols": 4,
                "cell_width": 320,
                "cell_height": 220,
                "margin": 50
            },
            "Vertical_Layout": {
                "description": "Vertikales 2x3 Grid Layout",
                "elements": ["CoffeeMachine", "Boiler", "Pump", "Grinder"],
                "cols": 2,
                "cell_width": 350,
                "cell_height": 250,
                "margin": 60
            },
            "Horizontal_Layout": {
                "description": "Horizontales 6x1 Grid Layout",
                "elements": ["CoffeeMachine", "Boiler", "Pump", "Grinder", "WaterTank", "ControlUnit"],
                "cols": 6,
                "cell_width": 250,
                "cell_height": 300,
                "margin": 30
            }
        }
    
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
    
    def find_or_create_package(self, package_name: str = "02_Architecture") -> Any:
        """
        Findet oder erstellt das Target-Package.
        
        Args:
            package_name: Name des Packages (default: "02_Architecture")
            
        Returns:
            EA Package Objekt
        """
        logger.info(f"Suche Package: {package_name}")
        
        # Suche in allen Models
        models = self.repo.Models
        for i in range(models.Count):
            model = models.GetAt(i)
            
            # Prüfe Model selbst
            if model.Name == package_name:
                self.target_package = model
                logger.info(f"[FOUND] Package als Model: {package_name}")
                return model
            
            # Suche in Sub-Packages
            packages = model.Packages
            for j in range(packages.Count):
                pkg = packages.GetAt(j)
                if pkg.Name == package_name:
                    self.target_package = pkg
                    logger.info(f"[FOUND] Package: {package_name}")
                    return pkg
        
        # Package nicht gefunden - erstelle es
        if models.Count > 0:
            model = models.GetAt(0)
            logger.info(f"[CREATE] Package: {package_name}")
            new_pkg = model.Packages.AddNew(package_name, "Package")
            new_pkg.Update()
            model.Packages.Refresh()
            self.target_package = new_pkg
            return new_pkg
        
        raise EAError(f"Konnte Package '{package_name}' nicht finden oder erstellen")
    
    def create_coffee_elements(self) -> bool:
        """Erstellt alle CoffeeMachine Elemente."""
        logger.info("\\n" + "="*50)
        logger.info("ERSTELLE COFFEEMACHINE ELEMENTE")
        logger.info("="*50)
        
        try:
            for elem_name, elem_spec in self.coffee_elements.items():
                logger.info(f"\\n[ELEMENT] {elem_name}")
                
                # Erstelle Element
                element = create_element(
                    self.target_package,
                    elem_name,
                    elem_spec["type"],
                    stereotype=elem_spec.get("stereotype"),
                    notes=elem_spec.get("notes")
                )
                
                # Füge Attribute hinzu
                for attr in elem_spec.get("attributes", []):
                    add_attribute(element, attr["name"], attr.get("type", "String"))
                    logger.info(f"  [ATTR] {attr['name']}: {attr.get('type', 'String')}")
                
                # Füge Operationen hinzu  
                for op in elem_spec.get("operations", []):
                    add_operation(element, op["name"], op.get("returnType", "void"))
                    logger.info(f"  [OP] {op['name']}(): {op.get('returnType', 'void')}")
                
                self.created_elements[elem_name] = element
                logger.info(f"  [OK] Element erstellt")
            
            logger.info(f"\\n[SUCCESS] {len(self.created_elements)} Elemente erstellt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Elemente: {e}")
            return False
    
    def find_existing_elements(self) -> bool:
        """Findet bereits existierende Elemente im Package."""
        logger.info("\\n" + "="*50)  
        logger.info("SUCHE EXISTIERENDE ELEMENTE")
        logger.info("="*50)
        
        try:
            elements = self.target_package.Elements
            found_elements = {}
            
            for elem_name in self.coffee_elements.keys():
                for i in range(elements.Count):
                    elem = elements.GetAt(i)
                    if elem.Name == elem_name:
                        found_elements[elem_name] = elem
                        logger.info(f"[FOUND] {elem_name} (ID: {elem.ElementID})")
                        break
                else:
                    logger.warning(f"[MISSING] {elem_name}")
            
            self.created_elements.update(found_elements)
            logger.info(f"\\n[RESULT] {len(found_elements)} Elemente gefunden")
            
            return len(found_elements) > 0
            
        except Exception as e:
            logger.error(f"Fehler beim Suchen der Elemente: {e}")
            return False
    
    def create_bdd_test(self, test_name: str, test_config: Dict) -> bool:
        """
        Erstellt einen BDD Test Case.
        
        Args:
            test_name: Name des Test Cases
            test_config: Test-Konfiguration
            
        Returns:
            True bei Erfolg
        """
        logger.info(f"\\n" + "="*50)
        logger.info(f"BDD TEST: {test_name}")
        logger.info(f"DESC: {test_config['description']}")
        logger.info("="*50)
        
        try:
            diagram_name = f"BDD_{test_name}"
            
            # Erstelle Diagramm
            logger.info(f"Erstelle Diagramm: {diagram_name}")
            diagram = create_diagram(
                self.target_package,
                diagram_name,
                "SysML1.4::BlockDefinition"
            )
            
            if not diagram:
                logger.error("Konnte Diagramm nicht erstellen")
                return False
            
            # Sammle Elemente für diesen Test
            test_elements = []
            missing_elements = []
            
            for elem_name in test_config["elements"]:
                if elem_name in self.created_elements:
                    test_elements.append(self.created_elements[elem_name])
                    logger.info(f"  [INCLUDE] {elem_name}")
                else:
                    missing_elements.append(elem_name)
                    logger.warning(f"  [MISSING] {elem_name}")
            
            if not test_elements:
                logger.error("Keine Elemente für Test verfügbar")
                return False
            
            # Platziere Elemente im Grid
            logger.info(f"Platziere {len(test_elements)} Elemente...")
            logger.info(f"Grid: {test_config['cols']} Spalten")
            logger.info(f"Zellgröße: {test_config['cell_width']}x{test_config['cell_height']}px")
            
            diagram_objects = auto_place_grid(
                diagram,
                test_elements,
                cols=test_config["cols"],
                cell_w=test_config["cell_width"],
                cell_h=test_config["cell_height"],
                margin=test_config["margin"]
            )
            
            logger.info(f"[SUCCESS] {len(diagram_objects)} Elemente platziert")
            
            # Speichere Diagramm-Info
            self.created_diagrams.append({
                "name": diagram_name,
                "diagram": diagram,
                "elements": len(diagram_objects),
                "test_config": test_config
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim BDD Test '{test_name}': {e}")
            return False
    
    def run_all_tests(self, create_elements: bool = False) -> bool:
        """Führt alle BDD Tests aus."""
        logger.info("\\n" + "="*60)
        logger.info("BDD DEMO TEST SUITE - COFFEEMACHINE")
        logger.info("="*60)
        
        try:
            # 1. Finde/Erstelle Package
            self.find_or_create_package("02_Architecture")
            
            # 2. Elemente bereitstellen
            if create_elements:
                if not self.create_coffee_elements():
                    logger.error("Konnte Elemente nicht erstellen")
                    return False
            else:
                if not self.find_existing_elements():
                    logger.warning("Keine existierenden Elemente gefunden")
                    logger.info("Tipp: Verwende --create-elements um Elemente zu erstellen")
                    return False
            
            # 3. Führe BDD Tests aus
            success_count = 0
            for test_name, test_config in self.test_cases.items():
                if self.create_bdd_test(test_name, test_config):
                    success_count += 1
                time.sleep(1)  # Kurze Pause zwischen Tests
            
            # 4. Zusammenfassung
            logger.info("\\n" + "="*60)
            logger.info("TEST ZUSAMMENFASSUNG")
            logger.info("="*60)
            logger.info(f"✓ Package: {self.target_package.Name}")
            logger.info(f"✓ Elemente verfügbar: {len(self.created_elements)}")
            logger.info(f"✓ BDD Tests erfolgreich: {success_count}/{len(self.test_cases)}")
            logger.info(f"✓ Diagramme erstellt: {len(self.created_diagrams)}")
            
            for diag_info in self.created_diagrams:
                logger.info(f"  - {diag_info['name']} ({diag_info['elements']} Elemente)")
            
            if success_count == len(self.test_cases):
                logger.info("\\n[SUCCESS] Alle BDD Tests erfolgreich!")
                logger.info("\\nÖffne EA und navigiere zu:")
                logger.info(f"  Package: {self.target_package.Name}")
                logger.info("  Diagramme: BDD_Compact_Layout, BDD_Wide_Layout, etc.")
                return True
            else:
                logger.warning(f"\\n[PARTIAL] {success_count} von {len(self.test_cases)} Tests erfolgreich")
                return False
            
        except Exception as e:
            logger.error(f"Fehler beim Ausführen der Tests: {e}")
            return False


def parse_arguments():
    """Parse Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description='BDD Demo Test Script für CoffeeMachine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Teste mit existierenden Elementen
  python scripts/test_bdd_demo.py --repo "project.qea"
  
  # Erstelle Elemente und teste
  python scripts/test_bdd_demo.py --repo "project.qea" --create-elements
  
  # Mit Debug-Ausgabe
  python scripts/test_bdd_demo.py --repo "project.qea" --debug
        """
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
        default='02_Architecture',
        help='Name des Target-Packages (default: "02_Architecture")'
    )
    
    parser.add_argument(
        '--create-elements',
        action='store_true',
        help='Erstellt die CoffeeMachine Elemente neu (idempotent)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Aktiviert Debug-Logging'
    )
    
    return parser.parse_args()


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
        logger.info("\\nTipp: Erstelle zuerst ein EA Projekt oder verwende ein existierendes")
        sys.exit(1)
    
    # Initialisiere Test Suite
    test_suite = BDDTestSuite(str(repo_path))
    
    try:
        # Verbinde mit Repository
        if not test_suite.connect():
            logger.error("Konnte nicht mit Repository verbinden")
            sys.exit(1)
        
        # Führe Tests aus
        success = test_suite.run_all_tests(create_elements=args.create_elements)
        
        if success:
            logger.info("\\n🎉 BDD Demo erfolgreich abgeschlossen!")
            sys.exit(0)
        else:
            logger.error("\\n❌ BDD Demo unvollständig")
            sys.exit(1)
        
    finally:
        # Trenne Verbindung
        test_suite.disconnect()


if __name__ == "__main__":
    main()