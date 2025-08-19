import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from jsonschema import validate, ValidationError, Draft7Validator
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


# JSON-Schema für Model-Spezifikationen
MODEL_SPEC_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "EA Model Specification",
    "description": "Schema für Enterprise Architect Model-Spezifikationen",
    "type": "object",
    "required": ["model"],
    "properties": {
        "model": {
            "type": "string",
            "description": "Name des Root-Models",
            "minLength": 1
        },
        "packages": {
            "type": "array",
            "description": "Liste der zu erstellenden Packages",
            "items": {
                "type": "string",
                "minLength": 1
            },
            "uniqueItems": True
        },
        "elements": {
            "type": "array",
            "description": "Liste der zu erstellenden Elemente",
            "items": {
                "type": "object",
                "required": ["package", "name", "type"],
                "properties": {
                    "package": {
                        "type": "string",
                        "description": "Package, in dem das Element erstellt wird",
                        "minLength": 1
                    },
                    "name": {
                        "type": "string",
                        "description": "Name des Elements",
                        "minLength": 1
                    },
                    "type": {
                        "type": "string",
                        "description": "UML/MDG-Typ (z.B. 'Class', 'SysML1.4::Block')",
                        "minLength": 1
                    },
                    "stereotype": {
                        "type": "string",
                        "description": "Optionales Stereotype"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optionale Notizen/Beschreibung"
                    },
                    "attributes": {
                        "type": "array",
                        "description": "Optionale Attribute",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "default": "String"}
                            }
                        }
                    },
                    "operations": {
                        "type": "array",
                        "description": "Optionale Operationen/Methoden",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "returnType": {"type": "string", "default": "void"}
                            }
                        }
                    }
                },
                "additionalProperties": False
            }
        },
        "connectors": {
            "type": "array",
            "description": "Liste der zu erstellenden Verbindungen",
            "items": {
                "type": "object",
                "required": ["type", "client", "supplier"],
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Connector-Typ",
                        "enum": [
                            "Association", "Aggregation", "Composition",
                            "Dependency", "Generalization", "Realization",
                            "Usage", "InformationFlow", "Connector"
                        ]
                    },
                    "client": {
                        "type": "string",
                        "description": "Name des Client-Elements",
                        "minLength": 1
                    },
                    "supplier": {
                        "type": "string",
                        "description": "Name des Supplier-Elements",
                        "minLength": 1
                    },
                    "name": {
                        "type": "string",
                        "description": "Optionaler Name der Verbindung"
                    },
                    "stereotype": {
                        "type": "string",
                        "description": "Optionales Stereotype"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optionale Notizen"
                    }
                },
                "additionalProperties": False
            }
        },
        "diagrams": {
            "type": "array",
            "description": "Optionale Diagramm-Definitionen",
            "items": {
                "type": "object",
                "required": ["package", "name", "type"],
                "properties": {
                    "package": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "Class", "Component", "Deployment", "UseCase",
                            "Activity", "StateMachine", "Sequence", "Communication",
                            "Package", "Object", "Composite", "Timing"
                        ]
                    },
                    "elements": {
                        "type": "array",
                        "description": "Elemente, die im Diagramm angezeigt werden",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    },
    "additionalProperties": False
}


def load_model_spec(filepath: str) -> Dict:
    """
    Lädt und validiert eine Model-Spezifikation aus einer JSON-Datei.
    
    Args:
        filepath: Pfad zur JSON-Datei
    
    Returns:
        Validierte Model-Spezifikation als Dictionary
    
    Raises:
        EAError: Bei Validierungsfehlern oder fehlender Datei
    """
    try:
        # Prüfe ob Datei existiert
        spec_path = Path(filepath)
        if not spec_path.exists():
            error_msg = f"Model-Spezifikation nicht gefunden: {spec_path.absolute()}"
            logger.error(error_msg)
            raise EAError(error_msg)
        
        # Lade JSON
        logger.info(f"Lade Model-Spezifikation: {spec_path}")
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_data = json.load(f)
        
        # Validiere gegen Schema
        logger.debug("Validiere Model-Spezifikation gegen Schema...")
        try:
            validate(instance=spec_data, schema=MODEL_SPEC_SCHEMA)
            logger.info("[OK] Model-Spezifikation ist valide")
        except ValidationError as ve:
            # Erstelle aussagekräftige Fehlermeldung
            error_path = " -> ".join(str(p) for p in ve.absolute_path) if ve.absolute_path else "root"
            error_msg = f"Validierungsfehler in '{error_path}': {ve.message}"
            
            # Füge Kontext hinzu
            if ve.validator == "required":
                error_msg = f"Pflichtfeld fehlt in '{error_path}': {ve.message}"
            elif ve.validator == "enum":
                error_msg = f"Ungültiger Wert in '{error_path}': {ve.instance} ist nicht erlaubt. Erlaubte Werte: {ve.validator_value}"
            elif ve.validator == "type":
                error_msg = f"Falscher Typ in '{error_path}': Erwartet {ve.validator_value}, erhalten {type(ve.instance).__name__}"
            elif ve.validator == "minLength":
                error_msg = f"Wert zu kurz in '{error_path}': Mindestlänge ist {ve.validator_value}"
            
            logger.error(error_msg)
            raise EAError(error_msg)
        
        # Zusätzliche Validierungen
        _validate_model_spec_logic(spec_data)
        
        logger.info(f"Model-Spezifikation geladen: {spec_data.get('model', 'Unnamed')}")
        logger.info(f"  - Packages: {len(spec_data.get('packages', []))}")
        logger.info(f"  - Elements: {len(spec_data.get('elements', []))}")
        logger.info(f"  - Connectors: {len(spec_data.get('connectors', []))}")
        
        return spec_data
        
    except json.JSONDecodeError as je:
        error_msg = f"JSON-Syntaxfehler in Zeile {je.lineno}, Spalte {je.colno}: {je.msg}"
        logger.error(error_msg)
        raise EAError(error_msg)
    except EAError:
        raise  # Bereits behandelte Fehler weiterreichen
    except Exception as e:
        error_msg = f"Unerwarteter Fehler beim Laden der Model-Spezifikation: {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)


def _validate_model_spec_logic(spec: Dict) -> None:
    """
    Zusätzliche logische Validierungen der Model-Spezifikation.
    
    Args:
        spec: Model-Spezifikation
    
    Raises:
        EAError: Bei logischen Inkonsistenzen
    """
    # Sammle alle definierten Package-Namen
    defined_packages = set(spec.get('packages', []))
    
    # Sammle alle definierten Element-Namen
    defined_elements = set()
    element_packages = {}
    
    # Prüfe Elements
    for elem in spec.get('elements', []):
        elem_name = elem['name']
        elem_package = elem['package']
        
        # Prüfe ob Package definiert ist
        if elem_package not in defined_packages:
            logger.warning(f"Element '{elem_name}' referenziert undefiniertes Package '{elem_package}'")
            # Kein Fehler, da Package automatisch erstellt werden kann
        
        # Prüfe auf doppelte Element-Namen im gleichen Package
        elem_key = f"{elem_package}::{elem_name}"
        if elem_key in element_packages:
            error_msg = f"Doppeltes Element '{elem_name}' in Package '{elem_package}'"
            logger.error(error_msg)
            raise EAError(error_msg)
        
        defined_elements.add(elem_name)
        element_packages[elem_key] = elem
    
    # Prüfe Connectors
    for conn in spec.get('connectors', []):
        client = conn['client']
        supplier = conn['supplier']
        
        # Prüfe ob referenzierte Elemente existieren
        if client not in defined_elements:
            error_msg = f"Connector referenziert undefiniertes Client-Element '{client}'"
            logger.error(error_msg)
            raise EAError(error_msg)
        
        if supplier not in defined_elements:
            error_msg = f"Connector referenziert undefiniertes Supplier-Element '{supplier}'"
            logger.error(error_msg)
            raise EAError(error_msg)
    
    # Prüfe Diagramme
    for diag in spec.get('diagrams', []):
        diag_package = diag['package']
        if diag_package not in defined_packages:
            logger.warning(f"Diagramm '{diag['name']}' referenziert undefiniertes Package '{diag_package}'")
        
        # Prüfe referenzierte Elemente
        for elem_name in diag.get('elements', []):
            if elem_name not in defined_elements:
                logger.warning(f"Diagramm '{diag['name']}' referenziert undefiniertes Element '{elem_name}'")


def validate_json_against_schema(json_data: Dict, schema: Dict) -> List[str]:
    """
    Validiert JSON-Daten gegen ein Schema und gibt alle Fehler zurück.
    
    Args:
        json_data: Zu validierende Daten
        schema: JSON-Schema
    
    Returns:
        Liste von Fehlermeldungen (leer wenn valide)
    """
    validator = Draft7Validator(schema)
    errors = []
    
    for error in validator.iter_errors(json_data):
        error_path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"{error_path}: {error.message}")
    
    return errors