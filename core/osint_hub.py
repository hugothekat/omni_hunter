# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V61: OSINT HUB ENGINE
📌 Formål: Centraliseret logik for passiv informationsindhentning.
"""
import socket
import concurrent.futures
from core.network import omni_dork_search

class OSINTHub:
    def __init__(self, target):
        self.target = target
        self.results = {"IP_Adresser": set(), "Sociale_Spor": set()}

    def run_all(self, driver=None):
        """Kører den fulde passive OSINT-cyklus asynkront."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(self.get_network_info)
            if driver:
                executor.submit(self.get_social_intel, driver)
                
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