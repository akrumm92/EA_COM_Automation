from typing import Any, Optional, List, Dict
from .exceptions import EAError, EATypeError
from .logging_conf import logger
from .utils import ensure_update_refresh


class Package:
    def __init__(self, ea_package: Any):
        self.ea_package = ea_package
    
    @property
    def name(self) -> str:
        return self.ea_package.Name
    
    @name.setter
    def name(self, value: str) -> None:
        self.ea_package.Name = value
        ensure_update_refresh(self.ea_package)
    
    @property
    def guid(self) -> str:
        return self.ea_package.PackageGUID
    
    @property
    def package_id(self) -> int:
        return self.ea_package.PackageID
    
    @property
    def notes(self) -> str:
        return self.ea_package.Notes
    
    @notes.setter
    def notes(self, value: str) -> None:
        self.ea_package.Notes = value
        ensure_update_refresh(self.ea_package)
    
    def add_package(self, name: str, package_type: str = "Package") -> 'Package':
        try:
            packages = self.ea_package.Packages
            new_package = packages.AddNew(name, package_type)
            ensure_update_refresh(new_package, packages)
            logger.info(f"Package erstellt: {name}")
            return Package(new_package)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Package: {e}")
            raise EAError(f"Fehler beim Erstellen des Package: {e}")
    
    def get_packages(self) -> List['Package']:
        packages = []
        for i in range(self.ea_package.Packages.Count):
            packages.append(Package(self.ea_package.Packages.GetAt(i)))
        return packages
    
    def find_package(self, name: str) -> Optional['Package']:
        for pkg in self.get_packages():
            if pkg.name == name:
                return pkg
        return None
    
    def delete_package(self, name: str) -> bool:
        try:
            packages = self.ea_package.Packages
            for i in range(packages.Count):
                if packages.GetAt(i).Name == name:
                    packages.DeleteAt(i, False)
                    packages.Refresh()
                    logger.info(f"Package gelöscht: {name}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Package: {e}")
            raise EAError(f"Fehler beim Löschen des Package: {e}")
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "package_id": self.package_id,
            "notes": self.notes,
            "packages": [pkg.to_dict() for pkg in self.get_packages()]
        }


def get_model_root(repo: Any) -> Package:
    try:
        models = repo.Models
        if models.Count > 0:
            return Package(models.GetAt(0))
        else:
            raise EAError("Kein Root-Model gefunden")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Root-Models: {e}")
        raise EAError(f"Fehler beim Abrufen des Root-Models: {e}")