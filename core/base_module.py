# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - ENTERPRISE MODULE FOUNDATION (core/base_module.py)
📌 Formål: Objektorienteret standardisering og Type Hinting for alle OSINT-moduler.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
import sys
import json
from datetime import datetime

class ModuleCategory(Enum):
    PERSON = "Identitets & Person-Efterforskning"
    NETWORK = "Netværk & Infrastruktur"
    FINANCE = "Finansiel & Krypto Sporing"
    SOCIAL = "Social Media Intelligence"
    FORENSICS = "Digital Forensics & OPSEC"
    REPORTING = "Rapportering & Visualisering"
    GENERAL = "Generel Efterretning"

class BaseModule(ABC):
    """Master Class for alle PETFE GOLIATH Moduler (Python 3.10+ Compliant)."""
    
    def __init__(self) -> None:
        self.name: str = "Unknown Module"
        self.description: str = "Ingen beskrivelse angivet."
        self.category: ModuleCategory = ModuleCategory.GENERAL
        self.data: Dict[str, Any] = {}
        
    def check_requirements(self) -> bool:
        """Validerer om modulet har de nødvendige API-nøgler og afhængigheder før kørsel."""
        return True

    def _log(self, message: str, color: str = '\033[96m') -> None:
        """Standardiseret tidsstemplet logning til TUI."""
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r\033[2m[{ts}]\033[0m {color}{message}\033[0m\n")

    @abstractmethod
    def run(self, driver: Any = None, target: str = "") -> Dict[str, Any]:
        """Selve eksekverings-motoren. SKAL overskrives af child-klassen."""
        pass

    def save_to_loot(self, filename: str) -> None:
        """Standardiseret metode til at gemme modul-data i loot-mappen."""
        from core.utils import session, datalake
        import os
        loot_dir = session.get("loot_folder", "loot_evidence")
        os.makedirs(loot_dir, exist_ok=True)
        path = os.path.join(loot_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        self._log(f"Data arkiveret: {path}", '\033[92m')