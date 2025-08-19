#!/usr/bin/env python3
"""
Unit-Tests für json_io.py mit Fokus auf load_model_spec und Schema-Validierung.
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ea_automation.json_io import (
    load_model_spec,
    validate_json_against_schema,
    MODEL_SPEC_SCHEMA,
    _validate_model_spec_logic
)
from ea_automation.exceptions import EAError


class TestLoadModelSpec(unittest.TestCase):
    """Tests für die load_model_spec Funktion."""
    
    def setUp(self):
        """Setup für jeden Test."""
        self.valid_spec = {
            "model": "TestModel",
            "packages": ["Package1", "Package2"],
            "elements": [
                {
                    "package": "Package1",
                    "name": "Element1",
                    "type": "Class"
                }
            ],
            "connectors": []
        }
    
    def test_load_valid_spec(self):
        """Test: Lade valide Spezifikation."""
        # Erstelle temporäre JSON-Datei
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_spec, f)
            temp_path = f.name
        
        try:
            # Lade Spezifikation
            result = load_model_spec(temp_path)
            
            # Assertions
            self.assertEqual(result['model'], 'TestModel')
            self.assertEqual(len(result['packages']), 2)
            self.assertEqual(len(result['elements']), 1)
            
        finally:
            # Aufräumen
            Path(temp_path).unlink()
    
    def test_load_spec_file_not_found(self):
        """Test: Fehler wenn Datei nicht existiert."""
        with self.assertRaises(EAError) as context:
            load_model_spec("non_existent_file.json")
        
        self.assertIn("nicht gefunden", str(context.exception))
    
    def test_load_spec_invalid_json(self):
        """Test: Fehler bei ungültigem JSON."""
        # Erstelle temporäre Datei mit ungültigem JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with self.assertRaises(EAError) as context:
                load_model_spec(temp_path)
            
            self.assertIn("JSON-Syntaxfehler", str(context.exception))
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_spec_missing_required_field(self):
        """Test: Fehler wenn Pflichtfeld fehlt."""
        invalid_spec = {
            # "model" fehlt - Pflichtfeld
            "packages": ["Package1"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_spec, f)
            temp_path = f.name
        
        try:
            with self.assertRaises(EAError) as context:
                load_model_spec(temp_path)
            
            self.assertIn("Pflichtfeld fehlt", str(context.exception))
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_spec_invalid_connector_type(self):
        """Test: Fehler bei ungültigem Connector-Typ."""
        invalid_spec = {
            "model": "TestModel",
            "elements": [
                {"package": "P1", "name": "E1", "type": "Class"},
                {"package": "P1", "name": "E2", "type": "Class"}
            ],
            "connectors": [
                {
                    "type": "InvalidType",  # Ungültiger Typ
                    "client": "E1",
                    "supplier": "E2"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_spec, f)
            temp_path = f.name
        
        try:
            with self.assertRaises(EAError) as context:
                load_model_spec(temp_path)
            
            self.assertIn("nicht erlaubt", str(context.exception))
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_spec_with_mdg_types(self):
        """Test: Unterstützung für MDG-Typen."""
        spec_with_mdg = {
            "model": "SysMLModel",
            "elements": [
                {
                    "package": "Architecture",
                    "name": "SystemBlock",
                    "type": "SysML1.4::Block",
                    "stereotype": "block",
                    "notes": "A SysML Block"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec_with_mdg, f)
            temp_path = f.name
        
        try:
            result = load_model_spec(temp_path)
            
            element = result['elements'][0]
            self.assertEqual(element['type'], 'SysML1.4::Block')
            self.assertEqual(element['stereotype'], 'block')
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_spec_with_attributes_and_operations(self):
        """Test: Elemente mit Attributen und Operationen."""
        spec = {
            "model": "TestModel",
            "elements": [
                {
                    "package": "Package1",
                    "name": "TestClass",
                    "type": "Class",
                    "attributes": [
                        {"name": "id", "type": "Integer"},
                        {"name": "name"}  # type ist optional
                    ],
                    "operations": [
                        {"name": "calculate", "returnType": "Double"},
                        {"name": "reset"}  # returnType ist optional
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec, f)
            temp_path = f.name
        
        try:
            result = load_model_spec(temp_path)
            
            element = result['elements'][0]
            self.assertEqual(len(element['attributes']), 2)
            self.assertEqual(len(element['operations']), 2)
            
        finally:
            Path(temp_path).unlink()


class TestModelSpecLogicValidation(unittest.TestCase):
    """Tests für die logische Validierung von Model-Spezifikationen."""
    
    def test_validate_duplicate_elements_in_package(self):
        """Test: Fehler bei doppelten Element-Namen im gleichen Package."""
        spec = {
            "model": "Test",
            "packages": ["Package1"],
            "elements": [
                {"package": "Package1", "name": "Element1", "type": "Class"},
                {"package": "Package1", "name": "Element1", "type": "Component"}  # Duplikat
            ]
        }
        
        with self.assertRaises(EAError) as context:
            _validate_model_spec_logic(spec)
        
        self.assertIn("Doppeltes Element", str(context.exception))
    
    def test_validate_connector_undefined_client(self):
        """Test: Fehler wenn Connector undefiniertes Client-Element referenziert."""
        spec = {
            "model": "Test",
            "elements": [
                {"package": "P1", "name": "Element1", "type": "Class"}
            ],
            "connectors": [
                {
                    "type": "Association",
                    "client": "UndefinedElement",  # Existiert nicht
                    "supplier": "Element1"
                }
            ]
        }
        
        with self.assertRaises(EAError) as context:
            _validate_model_spec_logic(spec)
        
        self.assertIn("undefiniertes Client-Element", str(context.exception))
    
    def test_validate_connector_undefined_supplier(self):
        """Test: Fehler wenn Connector undefiniertes Supplier-Element referenziert."""
        spec = {
            "model": "Test",
            "elements": [
                {"package": "P1", "name": "Element1", "type": "Class"}
            ],
            "connectors": [
                {
                    "type": "Association",
                    "client": "Element1",
                    "supplier": "UndefinedElement"  # Existiert nicht
                }
            ]
        }
        
        with self.assertRaises(EAError) as context:
            _validate_model_spec_logic(spec)
        
        self.assertIn("undefiniertes Supplier-Element", str(context.exception))
    
    def test_validate_element_undefined_package_warning(self):
        """Test: Warnung (kein Fehler) wenn Element undefiniertes Package referenziert."""
        spec = {
            "model": "Test",
            "packages": ["Package1"],
            "elements": [
                {
                    "package": "UndefinedPackage",  # Nicht in packages definiert
                    "name": "Element1",
                    "type": "Class"
                }
            ]
        }
        
        # Sollte keine Exception werfen (nur Warning)
        try:
            _validate_model_spec_logic(spec)
        except EAError:
            self.fail("Should not raise exception for undefined package")


class TestValidateJsonAgainstSchema(unittest.TestCase):
    """Tests für die validate_json_against_schema Funktion."""
    
    def test_validate_valid_json(self):
        """Test: Valides JSON gegen Schema."""
        valid_data = {
            "model": "TestModel",
            "packages": ["P1", "P2"]
        }
        
        errors = validate_json_against_schema(valid_data, MODEL_SPEC_SCHEMA)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_json_wrong_type(self):
        """Test: Ungültiges JSON - falscher Typ."""
        invalid_data = {
            "model": 123,  # Sollte String sein
            "packages": ["P1"]
        }
        
        errors = validate_json_against_schema(invalid_data, MODEL_SPEC_SCHEMA)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("model" in error for error in errors))
    
    def test_validate_invalid_json_additional_property(self):
        """Test: Ungültiges JSON - zusätzliche Properties."""
        invalid_data = {
            "model": "Test",
            "unknownProperty": "value"  # Nicht erlaubt
        }
        
        errors = validate_json_against_schema(invalid_data, MODEL_SPEC_SCHEMA)
        self.assertGreater(len(errors), 0)
    
    def test_validate_empty_spec(self):
        """Test: Minimale valide Spezifikation."""
        minimal_spec = {
            "model": "MinimalModel"
        }
        
        errors = validate_json_against_schema(minimal_spec, MODEL_SPEC_SCHEMA)
        self.assertEqual(len(errors), 0)
    
    def test_validate_complete_spec(self):
        """Test: Vollständige Spezifikation mit allen Features."""
        complete_spec = {
            "model": "CompleteModel",
            "packages": ["P1", "P2"],
            "elements": [
                {
                    "package": "P1",
                    "name": "E1",
                    "type": "Class",
                    "stereotype": "entity",
                    "notes": "Test element",
                    "attributes": [{"name": "attr1", "type": "String"}],
                    "operations": [{"name": "op1", "returnType": "void"}]
                }
            ],
            "connectors": [
                {
                    "type": "Association",
                    "client": "E1",
                    "supplier": "E1",
                    "name": "self",
                    "stereotype": "uses",
                    "notes": "Self reference"
                }
            ],
            "diagrams": [
                {
                    "package": "P1",
                    "name": "Overview",
                    "type": "Class",
                    "elements": ["E1"]
                }
            ]
        }
        
        errors = validate_json_against_schema(complete_spec, MODEL_SPEC_SCHEMA)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()