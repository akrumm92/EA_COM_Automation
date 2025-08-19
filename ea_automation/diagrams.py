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


def create_diagram(package: Any, name: str, diagram_type: str) -> Any:
    """
    Erstellt ein Diagramm im angegebenen Package.
    
    Args:
        package: EA Package Objekt
        name: Name des Diagramms
        diagram_type: Typ des Diagramms (z.B. 'Class', 'Component', 'SysML1.4::BlockDefinition')
    
    Returns:
        EA Diagram Objekt
    """
    try:
        # Hole Package-Objekt
        ea_package = package.ea_package if hasattr(package, 'ea_package') else package
        diagrams_collection = ea_package.Diagrams
        
        # Prüfe ob Diagramm bereits existiert
        logger.debug(f"Prüfe ob Diagramm '{name}' bereits existiert...")
        for i in range(diagrams_collection.Count):
            diag = diagrams_collection.GetAt(i)
            if diag.Name == name:
                logger.info(f"Diagramm existiert bereits: {name} (ID: {diag.DiagramID})")
                return diag
        
        # Erstelle neues Diagramm
        logger.info(f"Erstelle neues Diagramm: {name} (Typ: {diagram_type})")
        
        # Handle MDG-Typen
        if '::' in diagram_type:
            # MDG-Typ (z.B. 'SysML1.4::BlockDefinition')
            # Versuche MDG-Typ, falls nicht verfügbar, verwende Fallback
            try:
                new_diagram = diagrams_collection.AddNew(name, diagram_type)
            except:
                # Fallback auf Standard-Typ
                fallback_type = 'Class' if 'Block' in diagram_type else 'Component'
                logger.warning(f"MDG-Typ '{diagram_type}' nicht verfügbar, verwende '{fallback_type}'")
                new_diagram = diagrams_collection.AddNew(name, fallback_type)
        else:
            # Standard UML-Typ
            new_diagram = diagrams_collection.AddNew(name, diagram_type)
        
        # Update und Refresh
        new_diagram.Update()
        diagrams_collection.Refresh()
        
        logger.info(f"Diagramm erfolgreich erstellt: {name} (ID: {new_diagram.DiagramID})")
        return new_diagram
        
    except Exception as e:
        error_msg = f"Fehler beim Erstellen des Diagramms '{name}': {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)


def place_on_diagram(diagram: Any, element: Any, left: int, top: int, right: int, bottom: int) -> Any:
    """
    Platziert ein Element auf einem Diagramm an den angegebenen Koordinaten.
    
    Args:
        diagram: EA Diagram Objekt
        element: EA Element Objekt
        left: Linke Koordinate
        top: Obere Koordinate
        right: Rechte Koordinate
        bottom: Untere Koordinate
    
    Returns:
        EA DiagramObject
    """
    try:
        # Hole DiagramObjects Collection
        diagram_objects = diagram.DiagramObjects if hasattr(diagram, 'DiagramObjects') else diagram.ea_diagram.DiagramObjects
        
        # Hole Element ID
        element_id = element.ElementID if hasattr(element, 'ElementID') else element.element_id
        element_name = element.Name if hasattr(element, 'Name') else element.name
        
        # Prüfe ob Element bereits auf Diagramm
        for i in range(diagram_objects.Count):
            obj = diagram_objects.GetAt(i)
            if obj.ElementID == element_id:
                logger.info(f"Element '{element_name}' bereits auf Diagramm, aktualisiere Position")
                # Aktualisiere Position
                obj.left = left
                obj.top = top
                obj.right = right
                obj.bottom = bottom
                obj.Update()
                return obj
        
        # Erstelle neues DiagramObject mit Koordinaten-String
        coords = f"l={left};r={right};t={top};b={bottom};"
        logger.debug(f"Platziere Element '{element_name}' mit Koordinaten: {coords}")
        
        new_obj = diagram_objects.AddNew(coords, "")
        new_obj.ElementID = element_id
        
        # Setze zusätzliche Properties falls nötig
        new_obj.ShowPublicAttributes = True
        new_obj.ShowPublicOperations = True
        
        # Update und Refresh
        new_obj.Update()
        diagram_objects.Refresh()
        
        logger.info(f"Element '{element_name}' auf Diagramm platziert: [{left},{top}]->[{right},{bottom}]")
        return new_obj
        
    except Exception as e:
        error_msg = f"Fehler beim Platzieren des Elements auf dem Diagramm: {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)


def auto_place_grid(
    diagram: Any, 
    elements: List[Any], 
    cols: int = 3, 
    cell_w: int = 300, 
    cell_h: int = 220, 
    margin: int = 50
) -> List[Any]:
    """
    Platziert Elemente automatisch in einem Raster auf dem Diagramm.
    
    Args:
        diagram: EA Diagram Objekt
        elements: Liste von EA Element Objekten
        cols: Anzahl Spalten im Raster (default: 3)
        cell_w: Breite einer Zelle in Pixeln (default: 300)
        cell_h: Höhe einer Zelle in Pixeln (default: 220)
        margin: Abstand zwischen Zellen in Pixeln (default: 50)
    
    Returns:
        Liste von erstellten DiagramObjects
    """
    try:
        logger.info(f"Auto-Platzierung von {len(elements)} Elementen im {cols}-Spalten-Raster")
        
        diagram_objects = []
        
        # Berechne Element-Größe (abzüglich Margin)
        elem_width = cell_w - margin
        elem_height = cell_h - margin
        
        for idx, element in enumerate(elements):
            # Berechne Raster-Position
            row = idx // cols
            col = idx % cols
            
            # Berechne Pixel-Koordinaten
            # EA verwendet ein invertiertes Y-Koordinatensystem (top < bottom)
            left = margin + (col * cell_w)
            top = -margin - (row * cell_h)  # Negativ für EA's Koordinatensystem
            right = left + elem_width
            bottom = top - elem_height  # Bottom ist kleiner als Top in EA
            
            element_name = element.Name if hasattr(element, 'Name') else element.name if hasattr(element, 'name') else f"Element_{idx}"
            logger.debug(f"Platziere '{element_name}' in Raster [{col},{row}]")
            
            # Platziere Element auf Diagramm
            try:
                diag_obj = place_on_diagram(diagram, element, left, top, right, bottom)
                diagram_objects.append(diag_obj)
            except Exception as e:
                logger.warning(f"Konnte Element '{element_name}' nicht platzieren: {e}")
                continue
        
        # Refresh Diagramm
        if hasattr(diagram, 'Update'):
            diagram.Update()
        elif hasattr(diagram, 'ea_diagram'):
            diagram.ea_diagram.Update()
        
        logger.info(f"[OK] {len(diagram_objects)} Elemente erfolgreich platziert")
        
        # Optional: Versuche Diagramm zu speichern
        try:
            if hasattr(diagram, 'Save'):
                diagram.Save()
                logger.debug("Diagramm gespeichert")
        except:
            pass  # Save nicht immer verfügbar
        
        return diagram_objects
        
    except Exception as e:
        error_msg = f"Fehler bei der Auto-Platzierung: {str(e)}"
        logger.error(error_msg)
        raise EAError(error_msg)


def open_diagram_in_ea(repo: Any, diagram: Any) -> bool:
    """
    Versucht ein Diagramm in der EA GUI zu öffnen (falls GUI verfügbar).
    
    Args:
        repo: EA Repository Objekt
        diagram: EA Diagram Objekt
    
    Returns:
        True wenn erfolgreich, False sonst
    """
    try:
        diagram_id = diagram.DiagramID if hasattr(diagram, 'DiagramID') else diagram.diagram_id
        diagram_guid = diagram.DiagramGUID if hasattr(diagram, 'DiagramGUID') else diagram.guid
        
        # Methode 1: OpenDiagram
        try:
            repo.OpenDiagram(diagram_id)
            logger.info(f"Diagramm in EA geöffnet: ID {diagram_id}")
            return True
        except:
            pass
        
        # Methode 2: ShowInProjectView
        try:
            repo.ShowInProjectView(diagram_guid)
            logger.info(f"Diagramm in Project View angezeigt: {diagram_guid}")
            return True
        except:
            pass
        
        # Methode 3: Über SQL und ActivateDiagram
        try:
            repo.ActivateDiagram(diagram_id)
            logger.info(f"Diagramm aktiviert: ID {diagram_id}")
            return True
        except:
            pass
        
        logger.warning("Konnte Diagramm nicht in EA GUI öffnen (GUI möglicherweise nicht verfügbar)")
        return False
        
    except Exception as e:
        logger.warning(f"Fehler beim Öffnen des Diagramms in EA: {e}")
        return False