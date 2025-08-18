"""
Pytest-Konfiguration für EA_COM_Automation Tests
"""

import pytest
import logging
import sys
from pathlib import Path

# Füge src zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

# Logging für Tests konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@pytest.fixture
def test_logger():
    """Fixture für Test-Logging"""
    return logging.getLogger("test")

@pytest.fixture
def test_data_dir():
    """Fixture für Test-Daten-Verzeichnis"""
    return Path(__file__).parent / "fixtures"