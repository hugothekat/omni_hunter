# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - NATIVE CERTIFICATE INTELLIGENCE (core/cert_intel.py)
📌 Formål: Opsnapper skjulte subdomæner og infrastruktur via Certificate Transparency logs.
🔧 Features:
   - Native REST API integration (Ingen afhængighed af forældede pip-pakker)
   - Multi-Source Failover (crt.sh -> HackerTarget)
   - Wildcard parsing og automatisk deduplikering
   - Resilient timeout og JSON error handling
"""

import re
import json
import requests
from typing import List, Set
from core.utils import C, logger
from core.network import safe_get_with_retry

class CertificateIntelligenceEngine:
    def __init__(self, target_domain: str):
        # Sikrer rent domæne-format
        self.domain = target_domain.replace("http://", "").replace("https://", "").split("/")[0]
        self.subdomains: Set[str] = set()
        self.errors: List[str] = []

    def execute_recon(self) -> List[str]:
        """Kører den fulde reconnaissance sekvens."""
        print(f"\n{C.YELLOW}[*] Initierer Native Certificate Transparency Scan for: {self.domain}...{C.RESET}")
        
        # Forsøg 1: Primary Source (crt.sh)
        if not self._query_crt_sh():
            print(f"{C.YELLOW}    [!] crt.sh fejlede eller timede ud. Falder tilbage til Secondary Source...{C.RESET}")
            # Forsøg 2: Secondary Source (HackerTarget)
            self._query_hackertarget()

        clean_list = list(self.subdomains)
        if clean_list:
            print(f"{C.GREEN}    [+] Certificate Engine returnerede {len(clean_list)} unikke subdomæner.{C.RESET}")
        else:
            print(f"{C.DIM}    [-] Ingen certifikat-data fundet for domænet.{C.RESET}")
            
        return clean_list

    def _query_crt_sh(self) -> bool:
        """Klarer direkte JSON forespørgsler til crt.sh databasen."""
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"
        headers = {"User-Agent": "PETFE-GOLIATH-OSINT-ENGINE"}
        
        try:
            # crt.sh er berygtet for 502/504 fejl, vi sætter en striks timeout
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    for cert in data:
                        name_value = cert.get("name_value", "")
                        # name_value kan indeholde flere domæner adskilt af linjeskift
                        for sub in name_value.split("\n"):
                            self._clean_and_add(sub)
                    return True
                except json.JSONDecodeError:
                    self.errors.append("crt.sh returnerede ugyldig JSON.")
                    return False
            else:
                self.errors.append(f"crt.sh returnerede HTTP {response.status_code}.")
                return False
                
        except requests.exceptions.Timeout:
            self.errors.append("crt.sh timeout (Serveren er overbelastet).")
            return False
        except Exception as e:
            self.errors.append(f"crt.sh netværksfejl: {e}")
            return False

    def _query_hackertarget(self) -> bool:
        """Fallback API via HackerTarget's Host Search."""
        url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and "error" not in response.text.lower():
                lines = response.text.split("\n")
                for line in lines:
                    if line.strip():
                        # Formatet er: sub.domain.com,1.2.3.4
                        sub = line.split(",")[0]
                        self._clean_and_add(sub)
                return True
            return False
        except Exception as e:
            self.errors.append(f"HackerTarget fejl: {e}")
            return False

    def _clean_and_add(self, sub: str):
        """Renser data (fjerner wildcards) og validerer format."""
        sub = sub.strip().lower()
        # Fjern wildcard prefix hvis det findes
        if sub.startswith("*."):
            sub = sub[2:]
            
        # Sikr at det rent faktisk ender på vores target domain
        if sub.endswith(self.domain) and sub != self.domain:
            # Fjern uønskede tegn
            sub = re.sub(r'[^a-z0-9.-]', '', sub)
            if sub:
                self.subdomains.add(sub)
