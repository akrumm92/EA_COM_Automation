#!/usr/bin/env python3
"""
Erstellt die Standard Package-Struktur in einem EA-Projekt
Verwendet die korrekte Initialisierung um "Internal application error" zu vermeiden
"""

import sys
import os
from pathlib import Path
import win32com.client
import pythoncom
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fix_and_create():
    """Hauptfunktion"""
    
    logger.info("="*60)
    logger.info("EA FIX & CREATE")
    logger.info("="*60)
    
    # Hole Projekt-Pfad aus .env
    project_path = r"C:\Users\E017093\Architecture\Test_EA__Project.qea"
    logger.info(f"\nProjekt-Pfad: {project_path}")
    
    if not Path(project_path).exists():
        logger.error(f"[FEHLER] Datei nicht gefunden: {project_path}")
        return
    
    try:
        # Initialisiere COM
        pythoncom.CoInitialize()
        
        # Methode 1: Erstelle neues Repository und öffne Datei
        logger.info("\n1. Erstelle neues Repository-Objekt...")
        repo = win32com.client.Dispatch("EA.Repository")
        
        logger.info("2. Öffne Projekt-Datei...")
        success = repo.OpenFile(str(project_path))
        
        if success:
            logger.info("   [OK] Datei geöffnet!")
            
            # Warte kurz für Initialisierung
            time.sleep(2)
            
            # Teste ob Models jetzt funktioniert
            logger.info("\n3. Teste Models-Zugriff...")
            try:
                models = repo.Models
                logger.info(f"   - Models.Count: {models.Count}")
                
                if models.Count == 0:
                    logger.info("   - Erstelle Root Model...")
                    model = models.AddNew("Architecture", "Package")
                    model.Update()
                    models.Refresh()
                    logger.info("   [OK] Model erstellt!")
                else:
                    model = models.GetAt(0)
                    logger.info(f"   - Verwende Model: {model.Name}")
                
                # Erstelle Packages
                logger.info("\n4. Erstelle Package-Struktur...")
                packages_to_create = [
                    "01_Business_Layer",
                    "02_Application_Layer", 
                    "03_Data_Layer",
                    "04_Technology_Layer",
                    "05_Implementation_Migration",
                    "99_Common"
                ]
                
                packages = model.Packages
                created = []
                
                for pkg_name in packages_to_create:
                    try:
                        logger.info(f"   - Erstelle: {pkg_name}")
                        new_pkg = packages.AddNew(pkg_name, "Package")
                        new_pkg.Update()
                        created.append(pkg_name)
                        logger.info(f"     [OK]")
                    except Exception as e:
                        logger.info(f"     [FEHLER] {e}")
                
                if created:
                    packages.Refresh()
                    logger.info(f"\n[ERFOLG] {len(created)} Packages erstellt!")
                    
                    # Speichere Änderungen
                    repo.SaveFile()
                    logger.info("[OK] Datei gespeichert")
                    
            except Exception as e:
                logger.error(f"[FEHLER] Models-Zugriff: {e}")
                
                # Alternative: GetPackageByGuid
                logger.info("\n4. Alternative: GetPackageByGuid...")
                try:
                    # Hole Root Package über SQL
                    sql = "SELECT ea_guid FROM t_package WHERE Parent_ID = 0 LIMIT 1"
                    result = repo.SQLQuery(sql)
                    
                    # Parse GUID aus XML
                    if "<ea_guid>" in result:
                        start = result.find("<ea_guid>") + len("<ea_guid>")
                        end = result.find("</ea_guid>", start)
                        if end > 0:
                            guid = result[start:end]
                            logger.info(f"   - Root GUID: {guid}")
                            
                            root_pkg = repo.GetPackageByGuid(guid)
                            if root_pkg:
                                logger.info(f"   [OK] Root Package: {root_pkg.Name}")
                                
                                # Erstelle Sub-Packages
                                packages = root_pkg.Packages
                                for pkg_name in packages_to_create:
                                    try:
                                        new_pkg = packages.AddNew(pkg_name, "Package")
                                        new_pkg.Update()
                                        logger.info(f"   [OK] {pkg_name}")
                                    except Exception as pe:
                                        logger.info(f"   [FEHLER] {pkg_name}: {pe}")
                                
                                packages.Refresh()
                                repo.SaveFile()
                                
                except Exception as guid_error:
                    logger.error(f"GetPackageByGuid failed: {guid_error}")
            
            # Schließe Repository
            repo.CloseFile()
            logger.info("\n[OK] Repository geschlossen")
            
        else:
            logger.error("[FEHLER] Konnte Datei nicht öffnen!")
            
            # Versuche mit Connection String
            logger.info("\n2b. Versuche mit OpenFile2...")
            conn_string = f"Provider=Microsoft.Jet.OLEDB.4.0;Data Source={project_path}"
            success = repo.OpenFile2(conn_string, "", "")
            
            if success:
                logger.info("   [OK] Mit OpenFile2 geöffnet!")
            else:
                logger.error("   [FEHLER] OpenFile2 auch fehlgeschlagen")
                
    except Exception as e:
        logger.error(f"\n[FATAL ERROR] {e}")
        
        # Letzter Versuch: EA.App
        logger.info("\nLetzter Versuch mit EA.App...")
        try:
            ea_app = win32com.client.GetActiveObject("EA.App")
            repo = ea_app.Repository
            
            # Schließe aktuelles Projekt
            repo.CloseFile()
            
            # Öffne neu
            success = repo.OpenFile(str(project_path))
            if success:
                logger.info("[OK] Über EA.App geöffnet!")
                # Wiederholen der Package-Erstellung...
            
        except Exception as app_error:
            logger.error(f"EA.App auch fehlgeschlagen: {app_error}")
    
    logger.info("\n" + "="*60)
    logger.info("ABSCHLUSS")
    logger.info("="*60)
    logger.info("\nPrüfe in EA ob Packages erstellt wurden.")
    logger.info("Falls nicht, gibt es folgende Optionen:")
    logger.info("\n1. NEUSTART:")
    logger.info("   - Schließe EA komplett")
    logger.info("   - Starte EA neu")
    logger.info("   - Öffne KEIN Projekt")
    logger.info("   - Führe dieses Script erneut aus")
    logger.info("\n2. TEMPLATE:")
    logger.info("   - Erstelle manuell EINE .qea Datei mit den Packages")
    logger.info("   - Verwende diese als Template für alle Projekte")
    logger.info("\n3. ALTERNATIVE TOOLS:")
    logger.info("   - Verwende EA's Automation Interface über .NET")
    logger.info("   - Oder verwende EA's API direkt aus EA heraus (Add-Ins)")

if __name__ == "__main__":
    fix_and_create()