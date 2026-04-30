# -*- coding: utf-8 -*-
import json
import re
from datetime import datetime
from typing import Dict, Any

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class CredentialExposureHeuristic(BaseModule):
    """
    GOLIATH V36: Credential Exposure Heuristic
    Passiv bruteforce/dorking efter konfigurationsfiler og glemte API nøgler på clearnet.
    """
    def __init__(self):
        super().__init__()
        self.name = "CREDENTIAL EXPOSURE HEURISTIC"
        self.description = "Passiv detektion af lækkede config filer og API nøgler."
        self.category = ModuleCategory.FORENSICS
        self.data = {
            "Target": "",
            "Exposure_Findings": [],
            "Severity_Score": 0,
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[34] CREDENTIAL EXPOSURE HEURISTIC V36\n{'='*60}{C.RESET}")
        domain = target.replace("http://", "").replace("https://", "").split("/")[0]
        self.data["Target"] = domain

        # Farlige Google Dorks for konfigurationsfejl
        dorks = [
            f'site:{domain} ext:env OR ext:config OR ext:php "DB_PASSWORD"',
            f'site:{domain} "BEGIN RSA PRIVATE KEY" OR "api_key"',
            f'site:github.com "{domain}" ("password" OR "token" OR "secret")',
            f'site:pastebin.com "{domain}" ("admin" OR "root" OR "password")'
        ]

        if not driver:
            print(f"{C.RED}[!] Modul 34 kræver WebDriver til Dorking. Afbryder.{C.RESET}")
            return self.data

        print(f"{C.YELLOW}[*] Udfører 100% Passiv Reconnaissance efter glemte credentials...{C.RESET}")
        
        hits_found = 0
        for dork in dorks:
            hits = omni_dork_search(driver, dork, max_links=3)
            for hit in hits:
                hits_found += 1
                context = hit.get('snippet', '')
                self.data["Exposure_Findings"].append({
                    "URL": hit.get('url'),
                    "Kontekst": context
                })
                print(f"{C.RED}    🔥 KRITISK FUND: {hit.get('url')}\n       Lækage: {context[:80]}...{C.RESET}")
                self.data["Severity_Score"] += 10

        if hits_found == 0:
            print(f"{C.GREEN}    ✓ Ingen åbne credentials fundet på clearnet/github.{C.RESET}")
            
        datalake.ingest(self.name, domain, self.data)
        return self.data