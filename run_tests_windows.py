#!/usr/bin/env python3
"""
Windows Test Runner für EA_COM_Automation
Führt alle Tests auf Windows aus und erstellt detaillierte Reports
"""

import sys
import os
import platform
import argparse
import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Stelle sicher, dass UTF-8 verwendet wird
if platform.system() == 'Windows':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

class TestRunner:
    def __init__(self, log_level=logging.INFO):
        self.log_level = log_level
        self.logger = None
        self.test_results = []
        self.start_time = None
        self.end_time = None
        self.setup_logging()
        
    def setup_logging(self):
        """Konfiguriert das Logging-System"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Log-Verzeichnis erstellen
        log_dir = Path("logs") / "test_runs" / datetime.now().strftime("%Y-%m-%d")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"test_{datetime.now().strftime('%H%M%S')}.log"
        
        # Logging konfigurieren
        logging.basicConfig(
            level=self.log_level,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Test-Runner gestartet auf {platform.system()} {platform.version()}")
        self.logger.info(f"Python-Version: {sys.version}")
        self.logger.info(f"Log-Datei: {log_file}")
        
    def check_environment(self) -> bool:
        """Überprüft die Test-Umgebung"""
        self.logger.info("Überprüfe Test-Umgebung...")
        
        # Prüfe OS
        if platform.system() != 'Windows':
            self.logger.warning(f"Tests sollten auf Windows ausgeführt werden! Aktuelles OS: {platform.system()}")
        
        # Prüfe Python-Version
        python_version = sys.version_info
        if python_version < (3, 8):
            self.logger.error(f"Python 3.8+ erforderlich! Aktuelle Version: {python_version}")
            return False
            
        # Prüfe ob pytest installiert ist
        try:
            import pytest
            self.logger.info(f"pytest Version: {pytest.__version__}")
        except ImportError:
            self.logger.error("pytest ist nicht installiert! Bitte mit 'pip install pytest' installieren.")
            return False
            
        # Prüfe ob Test-Verzeichnis existiert
        test_dir = Path("tests")
        if not test_dir.exists():
            self.logger.warning("Test-Verzeichnis 'tests' existiert nicht. Erstelle es...")
            test_dir.mkdir(parents=True, exist_ok=True)
            
        return True
        
    def run_tests(self, test_type: str = "all", coverage: bool = False) -> bool:
        """Führt die Tests aus"""
        self.start_time = datetime.now()
        self.logger.info(f"Starte {test_type} Tests...")
        
        # Pytest-Kommando aufbauen
        cmd = ["python", "-m", "pytest"]
        
        # Test-Typ bestimmen
        if test_type == "unit":
            cmd.append("tests/unit")
        elif test_type == "integration":
            cmd.append("tests/integration")
        else:
            cmd.append("tests")
            
        # Weitere Optionen
        cmd.extend([
            "-v",  # Verbose
            "--tb=short",  # Kurze Traceback
            f"--junitxml=test_reports/junit/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
            f"--html=test_reports/html/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "--self-contained-html",
        ])
        
        # Coverage wenn gewünscht
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:test_reports/coverage",
                "--cov-report=term"
            ])
            
        # Report-Verzeichnisse erstellen
        for dir_path in ["test_reports/junit", "test_reports/html", "test_reports/coverage"]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
        # Tests ausführen
        self.logger.info(f"Führe aus: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=Path.cwd()
            )
            
            self.logger.info(result.stdout)
            if result.stderr:
                self.logger.error(result.stderr)
                
            self.end_time = datetime.now()
            
            # Ergebnis auswerten
            if result.returncode == 0:
                self.logger.info("✅ Alle Tests erfolgreich!")
                return True
            else:
                self.logger.error(f"❌ Tests fehlgeschlagen! Return code: {result.returncode}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Ausführen der Tests: {e}", exc_info=True)
            self.end_time = datetime.now()
            return False
            
    def create_summary_report(self, success: bool):
        """Erstellt einen zusammenfassenden Report"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_seconds": duration,
            "environment": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": sys.version,
                "cwd": str(Path.cwd())
            }
        }
        
        # JSON-Report speichern
        report_path = Path("test_reports") / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Summary-Report gespeichert: {report_path}")
        
        # Konsolen-Ausgabe
        print("\n" + "="*60)
        print("TEST ZUSAMMENFASSUNG")
        print("="*60)
        print(f"Status: {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")
        print(f"Dauer: {duration:.2f} Sekunden")
        print(f"Platform: {platform.system()} {platform.version()}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Report: {report_path}")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Windows Test Runner für EA_COM_Automation')
    parser.add_argument('--unit', action='store_true', help='Nur Unit-Tests ausführen')
    parser.add_argument('--integration', action='store_true', help='Nur Integration-Tests ausführen')
    parser.add_argument('--debug', action='store_true', help='Debug-Logging aktivieren')
    parser.add_argument('--coverage', action='store_true', help='Code-Coverage messen')
    
    args = parser.parse_args()
    
    # Log-Level bestimmen
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # Test-Typ bestimmen
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    else:
        test_type = "all"
        
    # Test-Runner initialisieren
    runner = TestRunner(log_level=log_level)
    
    # Umgebung prüfen
    if not runner.check_environment():
        sys.exit(1)
        
    # Tests ausführen
    success = runner.run_tests(test_type=test_type, coverage=args.coverage)
    
    # Report erstellen
    runner.create_summary_report(success)
    
    # Exit-Code setzen
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()