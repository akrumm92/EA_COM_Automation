from typing import Any, Optional, List, Dict
from .exceptions import EAError, EATypeError
from .logging_conf import logger
from .utils import ensure_update_refresh


class Element:
    def __init__(self, ea_element: Any):
        self.ea_element = ea_element
    
    @property
    def name(self) -> str:
        return self.ea_element.Name
    
    @name.setter
    def name(self, value: str) -> None:
        self.ea_element.Name = value
        ensure_update_refresh(self.ea_element)
    
    @property
    def guid(self) -> str:
        return self.ea_element.ElementGUID
    
    @property
    def element_id(self) -> int:
        return self.ea_element.ElementID
    
    @property
    def element_type(self) -> str:
        return self.ea_element.Type
    
    @property
    def stereotype(self) -> str:
        return self.ea_element.Stereotype
    
    @stereotype.setter
    def stereotype(self, value: str) -> None:
        self.ea_element.Stereotype = value
        ensure_update_refresh(self.ea_element)
    
    @property
    def notes(self) -> str:
        return self.ea_element.Notes
    
    @notes.setter
    def notes(self, value: str) -> None:
        self.ea_element.Notes = value
        ensure_update_refresh(self.ea_element)
    
    @property
    def status(self) -> str:
        return self.ea_element.Status
    
    @status.setter
    def status(self, value: str) -> None:
        self.ea_element.Status = value
        ensure_update_refresh(self.ea_element)
    
    def add_attribute(self, name: str, attr_type: str = "String") -> Any:
        try:
            attributes = self.ea_element.Attributes
            new_attr = attributes.AddNew(name, attr_type)
            ensure_update_refresh(new_attr, attributes)
            logger.info(f"Attribut erstellt: {name}")
            return new_attr
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Attributs: {e}")
            raise EAError(f"Fehler beim Erstellen des Attributs: {e}")
    
    def add_method(self, name: str, return_type: str = "void") -> Any:
        try:
            methods = self.ea_element.Methods
            new_method = methods.AddNew(name, return_type)
            ensure_update_refresh(new_method, methods)
            logger.info(f"Methode erstellt: {name}")
            return new_method
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Methode: {e}")
            raise EAError(f"Fehler beim Erstellen der Methode: {e}")
    
    def get_attributes(self) -> List[Dict]:
        attributes = []
        for i in range(self.ea_element.Attributes.Count):
            attr = self.ea_element.Attributes.GetAt(i)
            attributes.append({
                "name": attr.Name,
                "type": attr.Type,
                "visibility": attr.Visibility,
                "notes": attr.Notes
            })
        return attributes
    
    def get_methods(self) -> List[Dict]:
        methods = []
        for i in range(self.ea_element.Methods.Count):
            method = self.ea_element.Methods.GetAt(i)
            methods.append({
                "name": method.Name,
                "return_type": method.ReturnType,
                "visibility": method.Visibility,
                "notes": method.Notes
            })
        return methods
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "element_id": self.element_id,
            "type": self.element_type,
            "stereotype": self.stereotype,
            "notes": self.notes,
            "status": self.status,
            "attributes": self.get_attributes(),
            "methods": self.get_methods()
        }


def create_element_in_package(package: Any, name: str, element_type: str = "Class") -> Element:
    try:
        elements = package.Elements if hasattr(package, 'Elements') else package.ea_package.Elements
        new_element = elements.AddNew(name, element_type)
        ensure_update_refresh(new_element, elements)
        logger.info(f"Element erstellt: {name} (Typ: {element_type})")
        return Element(new_element)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Elements: {e}")
        raise EAError(f"Fehler beim Erstellen des Elements: {e}")


def get_elements_from_package(package: Any) -> List[Element]:
    elements = []
    ea_package = package.ea_package if hasattr(package, 'ea_package') else package
    for i in range(ea_package.Elements.Count):
        elements.append(Element(ea_package.Elements.GetAt(i)))
    return elements