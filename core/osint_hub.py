# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V61: OSINT HUB ENGINE
📌 Formål: Centraliseret logik for passiv informationsindhentning.
"""
import socket
import concurrent.futures
import re
from core.network import omni_dork_search
from core.utils import logger
from modules.mod_scor_hunter import ScorHunter

class AbstractTargetTask:
    """Basisklasse for dynamisk routing af OSINT opgaver baseret på input."""
    pattern = re.compile(r"")
    def run(self, target: str): pass

class ScorProfileTask(AbstractTargetTask):
    pattern = re.compile(r"^[a-zA-Z0-9_-]{3,25}$") # Matcher typiske brugernavne, ikke domæner
    def run(self, target: str):
        logger.info(f"OSINT Hub Dispatcher: Mål '{target}' triggede automatisk Scor.dk scraping.")
        hunter = ScorHunter(target_username=target, headless=True)
        hunter.stealth_extract_profile()

class OSINTHub:
    def __init__(self, target):
        self.target = target
        self.results = {"IP_Adresser": set(), "Sociale_Spor": set()}
        # Simpel regex til at skelne domæner fra brugernavne
        self.domain_regex = re.compile(r'\.[a-zA-Z]{2,}$')
        # GOLIATH EXPANSION: Dynamisk Task Registry
        self.registered_tasks = [ScorProfileTask()]

    def run_all(self, driver=None):
        """Kører den fulde passive OSINT-cyklus asynkront."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            executor.submit(self.get_network_info)
            if driver:
                executor.submit(self.get_social_intel, driver)
                
            # Dynamisk routing af special-scrapers i parallelle tråde
            for task in self.registered_tasks:
                if task.pattern.match(self.target) and not self.domain_regex.search(self.target):
                    executor.submit(task.run, self.target)
                    
        # Konverter sets til lister for JSON-kompatibilitet
        return {k: list(v) for k, v in self.results.items()}

    def get_network_info(self):
        """Henter IP-data uden at røre målets servere direkte."""
        try:
            ip = socket.gethostbyname(self.target)
            self.results["IP_Adresser"].add(ip)
        except Exception:
            pass

    def get_social_intel(self, driver):
        """Dorking logik for at finde profiler asynkront."""
        hits = omni_dork_search(driver, f'"{self.target}"', max_links=5)
        for hit in hits:
            if hit.get('url'):
                self.results["Sociale_Spor"].add(hit['url'])

    def run_scor_profile_hunt(self):
        """
        GOLIATH EXPANSION: Kører specialiseret Scor.dk scraper, hvis målet er et brugernavn.
        Kører i parallel med andre OSINT-funktioner.
        """
        # Kør kun, hvis målet IKKE ligner et domæne (heuristisk tjek)
        if not self.domain_regex.search(self.target):
            logger.info(f"OSINT Hub: Mål '{self.target}' ligner et brugernavn. Starter ScorHunter i baggrunden.")
            try:
                hunter = ScorHunter(target_username=self.target, headless=True)
                hunter.stealth_extract_profile()
            except Exception as e:
                logger.error(f"OSINT Hub: Fejl under kørsel af ScorHunter for '{self.target}': {e}")