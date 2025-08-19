#!/usr/bin/env python3
"""
CLI Script zum Hinzufügen von SysML Block-Elementen zu einem EA-Package.

Verwendung:
    python scripts/add_blocks.py --repo "C:\\path\\to\\project.qea" --package "02_Architecture" --blocks "Motor;Pumpe;Heizelement"
"""

import argparse
import sys
import os
from pathlib import Path
import logging

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

import win32com.client
from ea_automation.elements import create_element, add_attribute, add_operation
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
        description='Fügt SysML Block-Elemente zu einem EA-Package hinzu'
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
        help='Name oder Pfad des Ziel-Packages (z.B. "02_Architecture" oder "Model/02_Architecture")'
    )
    
    parser.add_argument(
        '--blocks',
        type=str,
        required=True,
        help='Semikolon-getrennte Liste von Block-Namen (z.B. "Motor;Pumpe;Heizelement")'
    )
    
    parser.add_argument(
        '--mdg-type',
        type=str,
        default='SysML1.4::Block',
        help='MDG-Typ für die Blocks (default: SysML1.4::Block)'
    )
    
    parser.add_argument(
        '--add-attributes',
        action='store_true',
        help='Fügt Standard-Attribute zu den Blocks hinzu'
    )
    
    parser.add_argument(
        '--add-operations',
        action='store_true',
        help='Fügt Standard-Operationen zu den Blocks hinzu'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Aktiviert Debug-Logging'
    )
    
    return parser.parse_args()


def add_standard_attributes(element, block_name):
    """Fügt Standard-Attribute basierend auf Block-Typ hinzu."""
    logger.debug(f"Füge Standard-Attribute zu {block_name} hinzu")
    
    # Basis-Attribute für alle Blocks
    add_attribute(element, "id", "String")
    add_attribute(element, "status", "String")
    add_attribute(element, "timestamp", "DateTime")
    
    # Spezifische Attribute basierend auf Block-Name
    if "Motor" in block_name:
        add_attribute(element, "power", "Integer")
        add_attribute(element, "rpm", "Integer")
        add_attribute(element, "temperature", "Double")
    elif "Pumpe" in block_name:
        add_attribute(element, "flowRate", "Double")
        add_attribute(element, "pressure", "Double")
        add_attribute(element, "efficiency", "Double")
    elif "Heiz" in block_name:
        add_attribute(element, "maxTemperature", "Double")
        add_attribute(element, "currentTemperature", "Double")
        add_attribute(element, "powerConsumption", "Double")
    
    logger.info(f"Standard-Attribute zu {block_name} hinzugefügt")


def add_standard_operations(element, block_name):
    """Fügt Standard-Operationen basierend auf Block-Typ hinzu."""
    logger.debug(f"Füge Standard-Operationen zu {block_name} hinzu")
    
    # Basis-Operationen für alle Blocks
    add_operation(element, "initialize", "void")
    add_operation(element, "getStatus", "String")
    add_operation(element, "reset", "void")
    
    # Spezifische Operationen basierend auf Block-Name
    if "Motor" in block_name:
        add_operation(element, "start", "Boolean")
        add_operation(element, "stop", "Boolean")
        add_operation(element, "setSpeed", "void")
    elif "Pumpe" in block_name:
        add_operation(element, "startPumping", "Boolean")
        add_operation(element, "stopPumping", "Boolean")
        add_operation(element, "setFlowRate", "void")
    elif "Heiz" in block_name:
        add_operation(element, "heatUp", "void")
        add_operation(element, "coolDown", "void")
        add_operation(element, "setTargetTemperature", "void")
    
    logger.info(f"Standard-Operationen zu {block_name} hinzugefügt")


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
    
    # Parse Block-Namen
    block_names = [name.strip() for name in args.blocks.split(';') if name.strip()]
    if not block_names:
        logger.error("Keine Block-Namen angegeben")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("EA SysML Block Creator")
    logger.info("="*60)
    logger.info(f"Repository: {repo_path}")
    logger.info(f"Ziel-Package: {args.package}")
    logger.info(f"MDG-Typ: {args.mdg_type}")
    logger.info(f"Blocks zu erstellen: {len(block_names)}")
    
    try:
        # Verbinde mit Repository
        logger.info("\nVerbinde mit EA Repository...")
        repo = win32com.client.Dispatch("EA.Repository")
        
        if not repo.OpenFile(str(repo_path)):
            logger.error("Konnte Repository nicht öffnen")
            sys.exit(1)
        
        logger.info("[OK] Repository geöffnet")
        
        # Finde Ziel-Package
        logger.info(f"\nSuche Package: {args.package}")
        
        # Versuche verschiedene Methoden das Package zu finden
        target_package = None
        
        # Suche in Models
        try:
            models = repo.Models
            for i in range(models.Count):
                model = models.GetAt(i)
                packages = model.Packages
                for j in range(packages.Count):
                    pkg = packages.GetAt(j)
                    if pkg.Name == args.package:
                        target_package = pkg
                        logger.info(f"[OK] Package gefunden: {pkg.Name}")
                        break
                if target_package:
                    break
        except Exception as e:
            logger.warning(f"Fehler beim Suchen in Models: {e}")
        
        if not target_package:
            logger.error(f"Package '{args.package}' nicht gefunden")
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
        
        # Erstelle Blocks
        logger.info("\n" + "-"*40)
        logger.info("Erstelle SysML Blocks:")
        logger.info("-"*40)
        
        created_blocks = []
        for block_name in block_names:
            try:
                logger.info(f"\nVerarbeite: {block_name}")
                
                # Erstelle Block-Element (idempotent)
                notes = f"SysML Block für {block_name}\nAutomatisch erstellt via add_blocks.py"
                element = create_element(
                    target_package,
                    block_name,
                    args.mdg_type,
                    stereotype="block",
                    notes=notes
                )
                
                created_blocks.append(block_name)
                
                # Füge Attribute hinzu wenn gewünscht
                if args.add_attributes:
                    add_standard_attributes(element, block_name)
                
                # Füge Operationen hinzu wenn gewünscht
                if args.add_operations:
                    add_standard_operations(element, block_name)
                
                logger.info(f"[OK] Block '{block_name}' verarbeitet")
                
            except Exception as e:
                logger.error(f"[FEHLER] Block '{block_name}': {str(e)}")
                continue
        
        # Zusammenfassung
        logger.info("\n" + "="*60)
        logger.info("ZUSAMMENFASSUNG")
        logger.info("="*60)
        logger.info(f"Erfolgreich verarbeitet: {len(created_blocks)}/{len(block_names)}")
        
        if created_blocks:
            logger.info("\nErstellte/Aktualisierte Blocks:")
            for block in created_blocks:
                logger.info(f"  ✓ {block}")
        
        failed = set(block_names) - set(created_blocks)
        if failed:
            logger.warning("\nFehlgeschlagene Blocks:")
            for block in failed:
                logger.warning(f"  ✗ {block}")
        
        # Repository schließen
        repo.CloseFile()
        logger.info("\n[OK] Repository geschlossen")
        
        # Exit-Code basierend auf Erfolg
        sys.exit(0 if len(created_blocks) == len(block_names) else 1)
        
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()