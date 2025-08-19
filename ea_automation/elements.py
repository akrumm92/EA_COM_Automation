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


def create_element(
    package: Any, 
    name: str, 
    uml_or_mdg_type: str, 
    stereotype: Optional[str] = None,
    notes: Optional[str] = None
) -> Any:
    """
    Erstellt ein Element im Package (idempotent).
    Unterstützt Standard UML-Typen und MDG-Typen wie 'SysML1.4::Block'.
    
    Args:
        package: EA Package Objekt
        name: Name des Elements
        uml_or_mdg_type: UML-Typ (z.B. 'Class') oder MDG-Typ (z.B. 'SysML1.4::Block')
        stereotype: Optionales Stereotype
        notes: Optionale Notizen
    
    Returns:
        EA Element Objekt (neu erstellt oder existierend)
    """
    try:
        # Hole Package-Objekt
        ea_package = package.ea_package if hasattr(package, 'ea_package') else package
        elements_collection = ea_package.Elements
        
        # Prüfe ob Element bereits existiert (Idempotenz)
        logger.debug(f"Suche existierendes Element: {name} (Typ: {uml_or_mdg_type})")
        for i in range(elements_collection.Count):
            elem = elements_collection.GetAt(i)
            # Vergleiche Name und Typ/Stereotype
            if elem.Name == name:
                # Prüfe ob es der richtige Typ ist
                if '::' in uml_or_mdg_type:
                    # MDG-Typ: Prüfe Stereotype
                    expected_stereotype = uml_or_mdg_type.split('::')[-1].lower()
                    if elem.Stereotype.lower() == expected_stereotype or elem.Stereotype.lower() == stereotype.lower() if stereotype else False:
                        logger.info(f"Element existiert bereits: {name} (ID: {elem.ElementID})")
                        # Update Notes wenn angegeben
                        if notes and elem.Notes != notes:
                            elem.Notes = notes
                            elem.Update()
                            logger.debug(f"Notes aktualisiert für: {name}")
                        return elem
                else:
                    # Standard UML-Typ
                    if elem.Type == uml_or_mdg_type:
                        logger.info(f"Element existiert bereits: {name} (ID: {elem.ElementID})")
                        # Update Notes wenn angegeben
                        if notes and elem.Notes != notes:
                            elem.Notes = notes
                            elem.Update()
                            logger.debug(f"Notes aktualisiert für: {name}")
                        return elem
        
        # Element existiert nicht - neu erstellen
        logger.info(f"Erstelle neues Element: {name} (Typ: {uml_or_mdg_type})")
        
        # Unterscheide zwischen Standard UML und MDG-Typen
        if '::' in uml_or_mdg_type:
            # MDG-Typ (z.B. 'SysML1.4::Block')
            mdg_parts = uml_or_mdg_type.split('::')
            base_type = mdg_parts[-1]  # z.B. 'Block'
            mdg_tech = mdg_parts[0]     # z.B. 'SysML1.4'
            
            # Für SysML Blocks verwende Class als Basis-Typ mit block Stereotype
            if base_type.lower() == "block":
                new_element = elements_collection.AddNew(name, "Class")
                new_element.Stereotype = "block"
            else:
                # Erstelle Element mit Basis-Typ
                new_element = elements_collection.AddNew(name, base_type)
                new_element.Stereotype = stereotype if stereotype else base_type
            
            # Setze MetaType für MDG-Erkennung
            new_element.MetaType = uml_or_mdg_type
            
            logger.debug(f"MDG-Element erstellt: {mdg_tech}::{base_type}")
        else:
            # Standard UML-Typ
            new_element = elements_collection.AddNew(name, uml_or_mdg_type)
            if stereotype:
                new_element.Stereotype = stereotype
        
        # Setze Notes wenn angegeben
        if notes:
            new_element.Notes = notes
        
        # Update und Refresh
        new_element.Update()
        elements_collection.Refresh()
        
        logger.info(f"Element erfolgreich erstellt: {name} (ID: {new_element.ElementID}, GUID: {new_element.ElementGUID})")
        return new_element
        
    except Exception as e:
        error_msg = f"Fehler beim Erstellen/Finden des Elements '{name}': {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)


def add_attribute(element: Any, name: str, type_: str = "") -> Any:
    """
    Fügt ein Attribut zu einem Element hinzu.
    
    Args:
        element: EA Element Objekt
        name: Name des Attributs
        type_: Datentyp des Attributs (default: "")
    
    Returns:
        EA Attribute Objekt
    """
    try:
        # Prüfe ob Attribut bereits existiert
        attributes = element.Attributes
        for i in range(attributes.Count):
            attr = attributes.GetAt(i)
            if attr.Name == name:
                logger.info(f"Attribut existiert bereits: {name}")
                if type_ and attr.Type != type_:
                    attr.Type = type_
                    attr.Update()
                    logger.debug(f"Attribut-Typ aktualisiert: {name} -> {type_}")
                return attr
        
        # Erstelle neues Attribut
        new_attr = attributes.AddNew(name, type_)
        new_attr.Update()
        attributes.Refresh()
        
        logger.info(f"Attribut erstellt: {name} (Typ: {type_}) für Element {element.Name}")
        return new_attr
        
    except Exception as e:
        error_msg = f"Fehler beim Hinzufügen des Attributs '{name}': {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)


def add_operation(element: Any, name: str, return_type: str = "void") -> Any:
    """
    Fügt eine Operation/Methode zu einem Element hinzu.
    
    Args:
        element: EA Element Objekt
        name: Name der Operation
        return_type: Rückgabetyp (default: "void")
    
    Returns:
        EA Method Objekt
    """
    try:
        # Prüfe ob Operation bereits existiert
        methods = element.Methods
        for i in range(methods.Count):
            method = methods.GetAt(i)
            if method.Name == name:
                logger.info(f"Operation existiert bereits: {name}")
                if method.ReturnType != return_type:
                    method.ReturnType = return_type
                    method.Update()
                    logger.debug(f"Rückgabetyp aktualisiert: {name} -> {return_type}")
                return method
        
        # Erstelle neue Operation
        new_method = methods.AddNew(name, return_type)
        new_method.Update()
        methods.Refresh()
        
        logger.info(f"Operation erstellt: {name} (Return: {return_type}) für Element {element.Name}")
        return new_method
        
    except Exception as e:
        error_msg = f"Fehler beim Hinzufügen der Operation '{name}': {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)