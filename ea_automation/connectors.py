from typing import Any, Optional, Dict
from .exceptions import EAError
from .logging_conf import logger
from .utils import ensure_update_refresh


class Connector:
    def __init__(self, ea_connector: Any):
        self.ea_connector = ea_connector
    
    @property
    def name(self) -> str:
        return self.ea_connector.Name
    
    @name.setter
    def name(self, value: str) -> None:
        self.ea_connector.Name = value
        ensure_update_refresh(self.ea_connector)
    
    @property
    def guid(self) -> str:
        return self.ea_connector.ConnectorGUID
    
    @property
    def connector_id(self) -> int:
        return self.ea_connector.ConnectorID
    
    @property
    def connector_type(self) -> str:
        return self.ea_connector.Type
    
    @connector_type.setter
    def connector_type(self, value: str) -> None:
        self.ea_connector.Type = value
        ensure_update_refresh(self.ea_connector)
    
    @property
    def stereotype(self) -> str:
        return self.ea_connector.Stereotype
    
    @stereotype.setter
    def stereotype(self, value: str) -> None:
        self.ea_connector.Stereotype = value
        ensure_update_refresh(self.ea_connector)
    
    @property
    def notes(self) -> str:
        return self.ea_connector.Notes
    
    @notes.setter
    def notes(self, value: str) -> None:
        self.ea_connector.Notes = value
        ensure_update_refresh(self.ea_connector)
    
    @property
    def source_element_id(self) -> int:
        return self.ea_connector.ClientID
    
    @property
    def target_element_id(self) -> int:
        return self.ea_connector.SupplierID
    
    @property
    def direction(self) -> str:
        return self.ea_connector.Direction
    
    @direction.setter
    def direction(self, value: str) -> None:
        self.ea_connector.Direction = value
        ensure_update_refresh(self.ea_connector)
    
    def set_source_role(self, name: str = "", multiplicity: str = "") -> None:
        try:
            client_end = self.ea_connector.ClientEnd
            if name:
                client_end.Role = name
            if multiplicity:
                client_end.Cardinality = multiplicity
            client_end.Update()
            self.ea_connector.Update()
            logger.info(f"Source-Rolle gesetzt: {name} [{multiplicity}]")
        except Exception as e:
            logger.error(f"Fehler beim Setzen der Source-Rolle: {e}")
            raise EAError(f"Fehler beim Setzen der Source-Rolle: {e}")
    
    def set_target_role(self, name: str = "", multiplicity: str = "") -> None:
        try:
            supplier_end = self.ea_connector.SupplierEnd
            if name:
                supplier_end.Role = name
            if multiplicity:
                supplier_end.Cardinality = multiplicity
            supplier_end.Update()
            self.ea_connector.Update()
            logger.info(f"Target-Rolle gesetzt: {name} [{multiplicity}]")
        except Exception as e:
            logger.error(f"Fehler beim Setzen der Target-Rolle: {e}")
            raise EAError(f"Fehler beim Setzen der Target-Rolle: {e}")
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "connector_id": self.connector_id,
            "type": self.connector_type,
            "stereotype": self.stereotype,
            "notes": self.notes,
            "source_element_id": self.source_element_id,
            "target_element_id": self.target_element_id,
            "direction": self.direction,
            "source_role": {
                "name": self.ea_connector.ClientEnd.Role,
                "multiplicity": self.ea_connector.ClientEnd.Cardinality
            },
            "target_role": {
                "name": self.ea_connector.SupplierEnd.Role,
                "multiplicity": self.ea_connector.SupplierEnd.Cardinality
            }
        }


def create_connector(source_element: Any, target_element: Any, 
                     connector_type: str = "Association") -> Connector:
    try:
        source = source_element.ea_element if hasattr(source_element, 'ea_element') else source_element
        target = target_element.ea_element if hasattr(target_element, 'ea_element') else target_element
        
        connectors = source.Connectors
        new_connector = connectors.AddNew("", connector_type)
        new_connector.SupplierID = target.ElementID
        ensure_update_refresh(new_connector, connectors)
        
        logger.info(f"Connector erstellt: {source.Name} -> {target.Name} (Typ: {connector_type})")
        return Connector(new_connector)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Connectors: {e}")
        raise EAError(f"Fehler beim Erstellen des Connectors: {e}")