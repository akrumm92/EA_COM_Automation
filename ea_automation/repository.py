import os
from pathlib import Path
from typing import Any, Optional
import win32com.client

from .exceptions import EAConnectionError, EAError
from .logging_conf import logger


def open_repository(path: str) -> Any:
    try:
        repo_path = Path(path).resolve()
        
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository nicht gefunden: {repo_path}")
        
        if repo_path.suffix not in ['.eap', '.eapx', '.qea', '.feap']:
            raise ValueError(f"Nicht unterstütztes Repository-Format: {repo_path.suffix}")
        
        ea = win32com.client.Dispatch("EA.Repository")
        
        if not ea.OpenFile(str(repo_path)):
            raise EAConnectionError(f"Konnte Repository nicht öffnen: {repo_path}")
        
        logger.info(f"Repository geöffnet: {repo_path}")
        return ea
        
    except Exception as e:
        logger.error(f"Fehler beim Öffnen des Repository: {e}")
        raise EAConnectionError(f"Fehler beim Öffnen des Repository: {e}")


def create_repository(path: str) -> Any:
    try:
        repo_path = Path(path).resolve()
        
        if repo_path.exists():
            logger.warning(f"Repository existiert bereits: {repo_path}")
            return open_repository(path)
        
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        
        ea = win32com.client.Dispatch("EA.Repository")
        
        if not ea.CreateModel(str(repo_path)):
            raise EAError(f"Konnte Repository nicht erstellen: {repo_path}")
        
        logger.info(f"Repository erstellt: {repo_path}")
        return ea
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Repository: {e}")
        raise EAError(f"Fehler beim Erstellen des Repository: {e}")


def close_repository(repo: Any) -> None:
    try:
        if repo:
            repo.CloseFile()
            repo.Exit()
            logger.info("Repository geschlossen")
    except Exception as e:
        logger.error(f"Fehler beim Schließen des Repository: {e}")
        raise EAError(f"Fehler beim Schließen des Repository: {e}")


def save(repo: Any) -> None:
    try:
        if repo:
            repo.SaveFile()
            logger.info("Repository gespeichert")
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Repository: {e}")
        raise EAError(f"Fehler beim Speichern des Repository: {e}")