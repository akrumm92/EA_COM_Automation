#!/usr/bin/env python3
"""
Unit-Tests für elements.py mit Fokus auf create_element Funktion.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call, PropertyMock
import sys
from pathlib import Path

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ea_automation.elements import (
    create_element, 
    add_attribute, 
    add_operation,
    Element
)
from ea_automation.exceptions import EAError


class TestCreateElement(unittest.TestCase):
    """Tests für die create_element Funktion."""
    
    def setUp(self):
        """Setup für jeden Test."""
        # Mock Package
        self.mock_package = Mock()
        self.mock_package.ea_package = Mock()
        self.mock_package.ea_package.Elements = Mock()
        self.mock_elements = self.mock_package.ea_package.Elements
        # Setup Count property
        type(self.mock_elements).Count = PropertyMock(return_value=0)
        
    def test_create_element_standard_uml_type(self):
        """Test: Erstelle Element mit Standard UML-Typ."""
        # Setup
        type(self.mock_elements).Count = PropertyMock(return_value=0)  # Kein existierendes Element
        mock_new_element = Mock()
        mock_new_element.ElementID = 123
        mock_new_element.ElementGUID = "{GUID-123}"
        mock_new_element.Name = "TestClass"
        self.mock_elements.AddNew.return_value = mock_new_element
        
        # Execute
        result = create_element(
            self.mock_package,
            "TestClass",
            "Class",
            stereotype="entity",
            notes="Test notes"
        )
        
        # Assert
        self.mock_elements.AddNew.assert_called_once_with("TestClass", "Class")
        self.assertEqual(mock_new_element.Stereotype, "entity")
        self.assertEqual(mock_new_element.Notes, "Test notes")
        mock_new_element.Update.assert_called_once()
        self.mock_elements.Refresh.assert_called_once()
        self.assertEqual(result, mock_new_element)
    
    def test_create_element_mdg_type(self):
        """Test: Erstelle Element mit MDG-Typ (z.B. SysML Block)."""
        # Setup
        type(self.mock_elements).Count = PropertyMock(return_value=0)
        mock_new_element = Mock()
        mock_new_element.ElementID = 456
        mock_new_element.ElementGUID = "{GUID-456}"
        mock_new_element.Name = "Motor"
        self.mock_elements.AddNew.return_value = mock_new_element
        
        # Execute
        result = create_element(
            self.mock_package,
            "Motor",
            "SysML1.4::Block"
        )
        
        # Assert
        self.mock_elements.AddNew.assert_called_once_with("Motor", "Block")
        self.assertEqual(mock_new_element.MDGHead, "SysML1.4::Block")
        self.assertEqual(mock_new_element.Stereotype, "Block")
        mock_new_element.Update.assert_called_once()
        self.assertEqual(result, mock_new_element)
    
    def test_create_element_idempotent_existing_element(self):
        """Test: Idempotenz - Element existiert bereits."""
        # Setup - Element existiert
        type(self.mock_elements).Count = PropertyMock(return_value=1)
        mock_existing_element = Mock()
        mock_existing_element.Name = "ExistingClass"
        mock_existing_element.Type = "Class"
        mock_existing_element.ElementID = 789
        mock_existing_element.Notes = "Old notes"
        self.mock_elements.GetAt.return_value = mock_existing_element
        
        # Execute
        result = create_element(
            self.mock_package,
            "ExistingClass",
            "Class",
            notes="New notes"
        )
        
        # Assert - Kein neues Element erstellt
        self.mock_elements.AddNew.assert_not_called()
        # Notes sollten aktualisiert werden
        self.assertEqual(mock_existing_element.Notes, "New notes")
        mock_existing_element.Update.assert_called_once()
        self.assertEqual(result, mock_existing_element)
    
    def test_create_element_idempotent_mdg_existing(self):
        """Test: Idempotenz für MDG-Typ Element."""
        # Setup - MDG Element existiert
        type(self.mock_elements).Count = PropertyMock(return_value=1)
        mock_existing_element = Mock()
        mock_existing_element.Name = "Pumpe"
        mock_existing_element.Type = "Block"
        mock_existing_element.MDGHead = "SysML1.4::Block"
        mock_existing_element.ElementID = 999
        mock_existing_element.Notes = ""
        self.mock_elements.GetAt.return_value = mock_existing_element
        
        # Execute
        result = create_element(
            self.mock_package,
            "Pumpe",
            "SysML1.4::Block"
        )
        
        # Assert - Kein neues Element erstellt
        self.mock_elements.AddNew.assert_not_called()
        self.assertEqual(result, mock_existing_element)
    
    def test_create_element_error_handling(self):
        """Test: Fehlerbehandlung bei Exception."""
        # Setup
        type(self.mock_elements).Count = PropertyMock(return_value=0)
        self.mock_elements.AddNew.side_effect = Exception("COM Error")
        
        # Execute & Assert
        with self.assertRaises(EAError) as context:
            create_element(
                self.mock_package,
                "FailClass",
                "Class"
            )
        
        self.assertIn("FailClass", str(context.exception))
        self.assertIn("COM Error", str(context.exception))
    


class TestAddAttribute(unittest.TestCase):
    """Tests für die add_attribute Funktion."""
    
    def setUp(self):
        """Setup für jeden Test."""
        self.mock_element = Mock()
        self.mock_element.Name = "TestElement"
        self.mock_element.Attributes = Mock()
        
    def test_add_new_attribute(self):
        """Test: Füge neues Attribut hinzu."""
        # Setup
        self.mock_element.Attributes.Count = 0
        mock_new_attr = Mock()
        self.mock_element.Attributes.AddNew.return_value = mock_new_attr
        
        # Execute
        result = add_attribute(self.mock_element, "testAttr", "String")
        
        # Assert
        self.mock_element.Attributes.AddNew.assert_called_once_with("testAttr", "String")
        mock_new_attr.Update.assert_called_once()
        self.mock_element.Attributes.Refresh.assert_called_once()
        self.assertEqual(result, mock_new_attr)
    
    def test_add_attribute_idempotent(self):
        """Test: Attribut existiert bereits."""
        # Setup
        self.mock_element.Attributes.Count = 1
        mock_existing_attr = Mock()
        mock_existing_attr.Name = "existingAttr"
        mock_existing_attr.Type = "Integer"
        self.mock_element.Attributes.GetAt.return_value = mock_existing_attr
        
        # Execute
        result = add_attribute(self.mock_element, "existingAttr", "String")
        
        # Assert - Typ wird aktualisiert
        self.mock_element.Attributes.AddNew.assert_not_called()
        self.assertEqual(mock_existing_attr.Type, "String")
        mock_existing_attr.Update.assert_called_once()
        self.assertEqual(result, mock_existing_attr)
    
    def test_add_attribute_error_handling(self):
        """Test: Fehlerbehandlung."""
        # Setup
        self.mock_element.Attributes.Count = 0
        self.mock_element.Attributes.AddNew.side_effect = Exception("Attribute Error")
        
        # Execute & Assert
        with self.assertRaises(EAError) as context:
            add_attribute(self.mock_element, "failAttr", "String")
        
        self.assertIn("failAttr", str(context.exception))


class TestAddOperation(unittest.TestCase):
    """Tests für die add_operation Funktion."""
    
    def setUp(self):
        """Setup für jeden Test."""
        self.mock_element = Mock()
        self.mock_element.Name = "TestElement"
        self.mock_element.Methods = Mock()
        
    def test_add_new_operation(self):
        """Test: Füge neue Operation hinzu."""
        # Setup
        self.mock_element.Methods.Count = 0
        mock_new_method = Mock()
        self.mock_element.Methods.AddNew.return_value = mock_new_method
        
        # Execute
        result = add_operation(self.mock_element, "calculate", "Double")
        
        # Assert
        self.mock_element.Methods.AddNew.assert_called_once_with("calculate", "Double")
        mock_new_method.Update.assert_called_once()
        self.mock_element.Methods.Refresh.assert_called_once()
        self.assertEqual(result, mock_new_method)
    
    def test_add_operation_default_void(self):
        """Test: Standard-Rückgabetyp ist void."""
        # Setup
        self.mock_element.Methods.Count = 0
        mock_new_method = Mock()
        self.mock_element.Methods.AddNew.return_value = mock_new_method
        
        # Execute
        result = add_operation(self.mock_element, "initialize")
        
        # Assert
        self.mock_element.Methods.AddNew.assert_called_once_with("initialize", "void")
    
    def test_add_operation_idempotent(self):
        """Test: Operation existiert bereits."""
        # Setup
        self.mock_element.Methods.Count = 1
        mock_existing_method = Mock()
        mock_existing_method.Name = "existingMethod"
        mock_existing_method.ReturnType = "void"
        self.mock_element.Methods.GetAt.return_value = mock_existing_method
        
        # Execute
        result = add_operation(self.mock_element, "existingMethod", "Boolean")
        
        # Assert - Return-Typ wird aktualisiert
        self.mock_element.Methods.AddNew.assert_not_called()
        self.assertEqual(mock_existing_method.ReturnType, "Boolean")
        mock_existing_method.Update.assert_called_once()
        self.assertEqual(result, mock_existing_method)


class TestElementClass(unittest.TestCase):
    """Tests für die Element Wrapper-Klasse."""
    
    def test_element_wrapper_properties(self):
        """Test: Element Wrapper Properties."""
        # Setup
        mock_ea_element = Mock()
        mock_ea_element.Name = "TestElement"
        mock_ea_element.ElementGUID = "{GUID-123}"
        mock_ea_element.ElementID = 123
        mock_ea_element.Type = "Class"
        mock_ea_element.Stereotype = "entity"
        mock_ea_element.Notes = "Test notes"
        mock_ea_element.Status = "Proposed"
        
        # Execute
        element = Element(mock_ea_element)
        
        # Assert
        self.assertEqual(element.name, "TestElement")
        self.assertEqual(element.guid, "{GUID-123}")
        self.assertEqual(element.element_id, 123)
        self.assertEqual(element.element_type, "Class")
        self.assertEqual(element.stereotype, "entity")
        self.assertEqual(element.notes, "Test notes")
        self.assertEqual(element.status, "Proposed")
    
    def test_element_to_dict(self):
        """Test: Element to_dict Methode."""
        # Setup
        mock_ea_element = Mock()
        mock_ea_element.Name = "TestClass"
        mock_ea_element.ElementGUID = "{GUID}"
        mock_ea_element.ElementID = 1
        mock_ea_element.Type = "Class"
        mock_ea_element.Stereotype = ""
        mock_ea_element.Notes = ""
        mock_ea_element.Status = "Proposed"
        mock_ea_element.Attributes = Mock()
        mock_ea_element.Attributes.Count = 0
        mock_ea_element.Methods = Mock()
        mock_ea_element.Methods.Count = 0
        
        # Execute
        element = Element(mock_ea_element)
        result = element.to_dict()
        
        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "TestClass")
        self.assertEqual(result["element_id"], 1)
        self.assertEqual(result["type"], "Class")
        self.assertEqual(len(result["attributes"]), 0)
        self.assertEqual(len(result["methods"]), 0)


if __name__ == "__main__":
    unittest.main()