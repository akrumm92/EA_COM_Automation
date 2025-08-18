#!/usr/bin/env python3
"""
CLI-Skript zum Initialisieren einer EA-Projektstruktur
Erstellt eine vordefinierte Package-Hierarchie im Repository
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Any, Optional

# Füge src zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repository import ensure_path

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_environment():
    """Lädt Umgebungsvariablen aus .env Datei falls vorhanden"""
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Umgebungsvariablen geladen aus {env_path}")
    except ImportError:
        logger.debug("python-dotenv nicht installiert, überspringe .env")


def connect_to_repository(repo_path: str) -> Any:
    """
    Stellt Verbindung zum EA Repository her
    
    Args:
        repo_path: Pfad zur EA Datei oder Connection String
        
    Returns:
        EA Repository Objekt
        
    Raises:
        Exception: Bei Verbindungsfehler
    """
    try:
        import win32com.client
        
        logger.info(f"Verbinde mit EA Repository: {repo_path}")
        
        # EA Application Objekt erstellen
        ea_app = win32com.client.Dispatch("EA.Repository")
        
        # Öffne Repository
        if repo_path.startswith("DBType=") or repo_path.startswith("Provider="):
            # Connection String für Datenbank
            success = ea_app.OpenFile2(repo_path, "", "")
        else:
            # Dateipfad
            repo_file = Path(repo_path)
            if not repo_file.exists():
                raise FileNotFoundError(f"EA Datei nicht gefunden: {repo_path}")
            success = ea_app.OpenFile(str(repo_file))
            
        if not success:
            raise Exception(f"Konnte Repository nicht öffnen: {repo_path}")
            
        logger.info("Verbindung erfolgreich hergestellt")
        return ea_app
        
    except ImportError:
        logger.error("pywin32 nicht installiert. Bitte mit 'pip install pywin32' installieren.")
        raise
    except Exception as e:
        logger.error(f"Fehler beim Verbinden mit Repository: {e}")
        raise


def parse_folder_structure(folders_str: str) -> List[List[str]]:
    """
    Parst die Ordnerstruktur aus dem String-Argument
    
    Args:
        folders_str: String mit Ordnerstruktur, z.B. "System;01_Requirements;02_Architecture"
        
    Returns:
        Liste von Pfaden die erstellt werden sollen
    """
    if not folders_str:
        return []
        
    # Teile bei Semikolon
    folders = [f.strip() for f in folders_str.split(';') if f.strip()]
    return folders


def create_project_structure(repo: Any, model_name: str, folders: List[str]) -> bool:
    """
    Erstellt die Projektstruktur im Repository
    
    Args:
        repo: EA Repository Objekt
        model_name: Name des Root-Models
        folders: Liste von Ordnernamen die erstellt werden sollen
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        logger.info(f"Erstelle Projektstruktur in Model '{model_name}'...")
        
        # Erstelle jeden Ordner als direktes Child des Models
        for folder_name in folders:
            path = [model_name, folder_name]
            logger.info(f"Erstelle Pfad: {' -> '.join(path)}")
            
            package = ensure_path(repo, path)
            if package:
                logger.info(f"✓ Package '{folder_name}' erstellt/gefunden (ID: {package.PackageID})")
            else:
                logger.error(f"✗ Konnte Package '{folder_name}' nicht erstellen")
                return False
                
        # Optional: Erstelle verschachtelte Struktur für bestimmte Ordner
        # Beispiel: Unter "01_Requirements" weitere Unterordner
        sub_structures = {
            "01_Requirements": ["Functional", "Non-Functional", "Use Cases"],
            "02_Architecture": ["Components", "Interfaces", "Deployment"],
            "03_Design": ["Classes", "Sequences", "Activities"]
        }
        
        for parent_folder, sub_folders in sub_structures.items():
            if parent_folder in folders:
                for sub_folder in sub_folders:
                    path = [model_name, parent_folder, sub_folder]
                    logger.info(f"Erstelle Unterpfad: {' -> '.join(path)}")
                    
                    package = ensure_path(repo, path)
                    if package:
                        logger.info(f"  ✓ Unter-Package '{sub_folder}' erstellt")
                        
        return True
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Projektstruktur: {e}")
        return False


def main():
    """Hauptfunktion des CLI-Skripts"""
    parser = argparse.ArgumentParser(
        description='Initialisiert eine EA-Projektstruktur mit vordefinierten Packages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s --repo "C:\\Projects\\test.eapx" --model "MyProject" --folders "System;Requirements;Design"
  %(prog)s --repo $EA_PROJECT_PATH --model "TestModel" --folders "01_Req;02_Arch;03_Design;04_Test"
        """
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        help='Pfad zur EA Repository Datei oder Connection String (kann auch aus EA_PROJECT_PATH gelesen werden)',
        default=os.getenv('EA_PROJECT_PATH')
    )
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Name des Root-Model Package'
    )
    
    parser.add_argument(
        '--folders',
        type=str,
        default="System;01_Requirements;02_Architecture;03_Design",
        help='Semikolon-getrennte Liste von Ordnern die erstellt werden sollen'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Aktiviert Debug-Ausgaben'
    )
    
    args = parser.parse_args()
    
    # Logging-Level setzen
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Umgebungsvariablen laden
    load_environment()
    
    # Repository-Pfad prüfen
    if not args.repo:
        logger.error("Kein Repository-Pfad angegeben. Verwende --repo oder setze EA_PROJECT_PATH")
        sys.exit(1)
        
    # Ordnerstruktur parsen
    folders = parse_folder_structure(args.folders)
    if not folders:
        logger.warning("Keine Ordner zum Erstellen angegeben")
        
    logger.info("="*60)
    logger.info("EA Projekt-Initialisierung")
    logger.info("="*60)
    logger.info(f"Repository: {args.repo}")
    logger.info(f"Model:      {args.model}")
    logger.info(f"Ordner:     {folders}")
    logger.info("="*60)
    
    repo = None
    try:
        # Mit Repository verbinden
        repo = connect_to_repository(args.repo)
        
        # Projektstruktur erstellen
        success = create_project_structure(repo, args.model, folders)
        
        if success:
            logger.info("="*60)
            logger.info("✅ Projektstruktur erfolgreich erstellt!")
            logger.info("="*60)
            sys.exit(0)
        else:
            logger.error("❌ Fehler beim Erstellen der Projektstruktur")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Datei nicht gefunden: {e}")
        sys.exit(2)
    except ImportError as e:
        logger.error(f"Fehlende Abhängigkeit: {e}")
        logger.error("Installiere mit: pip install pywin32 python-dotenv")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        sys.exit(4)
    finally:
        # Repository schließen
        if repo:
            try:
                repo.CloseFile()
                repo.Exit()
                logger.debug("Repository-Verbindung geschlossen")
            except:
                pass


if __name__ == "__main__":
    main()