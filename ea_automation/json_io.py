import json
from pathlib import Path
from typing import Any, Dict, List
from .exceptions import EAError
from .logging_conf import logger


def export_to_json(data: Any, filepath: str, indent: int = 2) -> None:
    try:
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        elif isinstance(data, list):
            data = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        logger.info(f"Daten exportiert nach: {output_path}")
    except Exception as e:
        logger.error(f"Fehler beim Exportieren nach JSON: {e}")
        raise EAError(f"Fehler beim Exportieren nach JSON: {e}")


def import_from_json(filepath: str) -> Dict:
    try:
        input_path = Path(filepath)
        
        if not input_path.exists():
            raise FileNotFoundError(f"JSON-Datei nicht gefunden: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Daten importiert von: {input_path}")
        return data
    except Exception as e:
        logger.error(f"Fehler beim Importieren von JSON: {e}")
        raise EAError(f"Fehler beim Importieren von JSON: {e}")


def export_package_structure(package: Any, filepath: str) -> None:
    try:
        package_dict = package.to_dict() if hasattr(package, 'to_dict') else {}
        export_to_json(package_dict, filepath)
    except Exception as e:
        logger.error(f"Fehler beim Exportieren der Package-Struktur: {e}")
        raise EAError(f"Fehler beim Exportieren der Package-Struktur: {e}")


def export_elements(elements: List[Any], filepath: str) -> None:
    try:
        elements_data = [elem.to_dict() if hasattr(elem, 'to_dict') else {} for elem in elements]
        export_to_json(elements_data, filepath)
    except Exception as e:
        logger.error(f"Fehler beim Exportieren der Elemente: {e}")
        raise EAError(f"Fehler beim Exportieren der Elemente: {e}")