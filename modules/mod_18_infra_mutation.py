# -*- coding: utf-8 -*-
import json
import requests
from datetime import datetime
from typing import Dict, Any

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.api_syndicate import syndicate

class InfraMutationTracker(BaseModule):
    """
    GOLIATH V36: DNS/WHOIS Mutation Tracker & Domain Ownership Timeline.
    Afslører hosting-skift, sikkerhedsforringelser og ejerskifte.
    """
    def __init__(self):
        super().__init__()
        self.name = "INFRA MUTATION TRACKER"
        self.description = "Historisk DNS og Ejerskabs-kortlægning."
        self.category = ModuleCategory.NETWORK
        self.data = {
            "Target": "",
            "DNS_Mutations": [],
            "Risk_Windows": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[33] DNS/WHOIS MUTATION TRACKER V36\n{'='*60}{C.RESET}")
        domain = target.replace("http://", "").replace("https://", "").split("/")[0]
        self.data["Target"] = domain

        print(f"{C.YELLOW}[*] Spuler globale DNS registre for mutationer ({domain})...{C.RESET}")
        
        # Bruger HackerTarget API som fallback for historisk DNS (Gratis lag)
        try:
            ht_url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            res = requests.get(ht_url, timeout=10)
            if res.status_code == 200 and "error" not in res.text:
                lines = res.text.strip().split('\n')
                print(f"{C.GREEN}    ✓ Fandt {len(lines)} DNS sub-mutations.{C.RESET}")
                for line in lines[:15]:
                    parts = line.split(',')
                    if len(parts) == 2:
                        self.data["DNS_Mutations"].append({"Host": parts[0], "IP": parts[1]})
        except Exception as e:
            print(f"{C.DIM}    [-] HackerTarget fejl: {e}{C.RESET}")

        # Bruger SecurityTrails fra The Syndicate for ægte historik
        import asyncio
        loop = asyncio.get_event_loop()
        st_data = loop.run_until_complete(syndicate.check_securitytrails(domain))
        
        if "error" not in st_data:
            print(f"{C.GREEN}    ✓ SecurityTrails historik hentet! Kortlægger Risk Windows...{C.RESET}")
            # Identificerer Risk Windows
            history = st_data.get("endpoint", {}).get("history", [])
            for record in history:
                if record.get("type") == "MX":
                    self.data["Risk_Windows"].append(f"Mail skift: {record.get('first_seen')} -> {record.get('last_seen')}")
                    
        # WHOIS History Tjek
        self._check_whois_mutations(domain)
        
        datalake.ingest(self.name, domain, self.data)
        print(f"\n{C.GREEN}[✓] Mutation Tracker fuldført.{C.RESET}")
        return self.data

    def _check_whois_mutations(self, domain: str):
        try:
            import whois
            w = whois.whois(domain)
            if w.creation_date:
                print(f"{C.MAGENTA}    🔥 Oprettelsesdato: {w.creation_date}{C.RESET}")
                self.data["Ownership_Creation"] = str(w.creation_date)
        except Exception:
            pass