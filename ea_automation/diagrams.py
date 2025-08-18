from typing import Any, Optional, List, Dict
from .exceptions import EAError
from .logging_conf import logger
from .utils import ensure_update_refresh


class Diagram:
    def __init__(self, ea_diagram: Any):
        self.ea_diagram = ea_diagram
    
    @property
    def name(self) -> str:
        return self.ea_diagram.Name
    
    @name.setter
    def name(self, value: str) -> None:
        self.ea_diagram.Name = value
        ensure_update_refresh(self.ea_diagram)
    
    @property
    def guid(self) -> str:
        return self.ea_diagram.DiagramGUID
    
    @property
    def diagram_id(self) -> int:
        return self.ea_diagram.DiagramID
    
    @property
    def diagram_type(self) -> str:
        return self.ea_diagram.Type
    
    @property
    def notes(self) -> str:
        return self.ea_diagram.Notes
    
    @notes.setter
    def notes(self, value: str) -> None:
        self.ea_diagram.Notes = value
        ensure_update_refresh(self.ea_diagram)
    
    def add_diagram_object(self, element: Any, left: int = 10, top: int = 10, 
                          right: int = 100, bottom: int = 100) -> Any:
        try:
            diagram_objects = self.ea_diagram.DiagramObjects
            new_obj = diagram_objects.AddNew(f"l={left};r={right};t={top};b={bottom};", "")
            new_obj.ElementID = element.ElementID if hasattr(element, 'ElementID') else element.element_id
            ensure_update_refresh(new_obj, diagram_objects)
            logger.info(f"Element zum Diagramm hinzugefügt: {element.Name if hasattr(element, 'Name') else element.name}")
            return new_obj
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Elements zum Diagramm: {e}")
            raise EAError(f"Fehler beim Hinzufügen des Elements zum Diagramm: {e}")
    
    def remove_diagram_object(self, element_id: int) -> bool:
        try:
            diagram_objects = self.ea_diagram.DiagramObjects
            for i in range(diagram_objects.Count):
                obj = diagram_objects.GetAt(i)
                if obj.ElementID == element_id:
                    diagram_objects.DeleteAt(i, True)
                    diagram_objects.Refresh()
                    logger.info(f"Element aus Diagramm entfernt: {element_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Elements aus dem Diagramm: {e}")
            raise EAError(f"Fehler beim Entfernen des Elements aus dem Diagramm: {e}")
    
    def get_diagram_objects(self) -> List[Dict]:
        objects = []
        for i in range(self.ea_diagram.DiagramObjects.Count):
            obj = self.ea_diagram.DiagramObjects.GetAt(i)
            objects.append({
                "element_id": obj.ElementID,
                "left": obj.left,
                "right": obj.right,
                "top": obj.top,
                "bottom": obj.bottom
            })
        return objects
    
    def save_as_image(self, filepath: str) -> bool:
        try:
            repo = self.ea_diagram.Repository
            repo.SaveDiagramImageToFile(filepath)
            logger.info(f"Diagramm als Bild gespeichert: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Diagramms als Bild: {e}")
            raise EAError(f"Fehler beim Speichern des Diagramms als Bild: {e}")
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "diagram_id": self.diagram_id,
            "type": self.diagram_type,
            "notes": self.notes,
            "objects": self.get_diagram_objects()
        }


def create_diagram_in_package(package: Any, name: str, diagram_type: str = "Class") -> Diagram:
    try:
        ea_package = package.ea_package if hasattr(package, 'ea_package') else package
        diagrams = ea_package.Diagrams
        new_diagram = diagrams.AddNew(name, diagram_type)
        ensure_update_refresh(new_diagram, diagrams)
        logger.info(f"Diagramm erstellt: {name} (Typ: {diagram_type})")
        return Diagram(new_diagram)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Diagramms: {e}")
        raise EAError(f"Fehler beim Erstellen des Diagramms: {e}")


def get_diagrams_from_package(package: Any) -> List[Diagram]:
    diagrams = []
    ea_package = package.ea_package if hasattr(package, 'ea_package') else package
    for i in range(ea_package.Diagrams.Count):
        diagrams.append(Diagram(ea_package.Diagrams.GetAt(i)))
    return diagrams