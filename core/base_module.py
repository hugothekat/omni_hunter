# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - ENTERPRISE MODULE FOUNDATION (core/base_module.py)
📌 Formål: Objektorienteret standardisering for alle OSINT-moduler.
"""
from enum import Enum
from core.utils import C, logger

class ModuleCategory(Enum):
    PERSON = "Identitets & Person-Efterforskning"
    NETWORK = "Netværk & Infrastruktur"
    FINANCE = "Finansiel & Krypto Sporing"
    SOCIAL = "Social Media Intelligence"
    FORENSICS = "Digital Forensics & OPSEC"
    REPORTING = "Rapportering & Visualisering"
    GENERAL = "Generel Efterretning"

class BaseModule:
    """Master Class for alle PETFE GOLIATH Moduler."""
    def __init__(self):
        self.name = "Unknown Module"
        self.description = "Ingen beskrivelse angivet."
        self.category = ModuleCategory.GENERAL
        
    def check_requirements(self) -> bool:
        """Validerer om modulet har de nødvendige API-nøgler før kørsel."""
        return True

    def run(self, driver=None, target: str = "") -> dict:
        """Selve eksekverings-motoren. Skal overskrives af child-klassen."""
        raise NotImplementedError(f"Modul {self.name} mangler en run() funktion.")
