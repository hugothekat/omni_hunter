# modules/mod_02_business.py
import json
import os
import urllib.parse
import requests
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import http, CONFIG

class BusinessIntelligenceAnalyst:
    def __init__(self, name):
        self.name = name.strip()
        self.api_key = CONFIG.get("api_keys", {}).get("hunter_io", "")
        self.results = {
            "Mål": self.name, 
            "CVR_Data": [], 
            "Hunter_Data": {}, 
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[02] Erhvervs-efterretning (CVR & Hunter.io)\n{'='*60}{C.RESET}")
        print(f"[*] Starter virksomheds-analyse for: {self.name}\n")
        
        # 1. CVR Register Opslag
        self._check_cvr()
        
        # 2. Hunter.io Domain Opslag (Medarbejder E-mails)
        self._check_hunter()
        
        self.save()

    def _check_cvr(self):
        print(f"{C.YELLOW}[*] Søger i CVR Registeret via API...{C.RESET}")
        headers = {"User-Agent": "OmniHunter-OSINT-Tool"}
        url = f"https://cvrapi.dk/api?search={urllib.parse.quote(self.name)}&country=dk"
        
        try:
            response = http.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and "error" not in response.text:
                data = response.json()
                print(f"{C.GREEN}    ✓ Virksomhed fundet: {data.get('name')} (CVR: {data.get('vat')}){C.RESET}")
                print(f"      -> Status: {data.get('status', 'Aktiv')}")
                print(f"      -> Adresse: {data.get('address')}, {data.get('zipcode')} {data.get('city')}")
                print(f"      -> Ansatte: {data.get('employees')}")
                self.results["CVR_Data"].append(data)
            else:
                print(f"{C.DIM}    [-] Ingen CVR matches fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] CVR API Fejl: {e}{C.RESET}")

    def _check_hunter(self):
        if not self.api_key:
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Mangler API-nøgle i config.json){C.RESET}")
            return

        domain = self.name
        # Hvis brugeren ikke skrev et domæne (med '.'), spørger vi om de vil tilføje det for at søge efter emails
        if "." not in domain:
            forslag = self.name.lower().replace(' ', '') + ".dk"
            domain = input(f"\n{C.YELLOW}[?] Indtast domæne for at trække medarbejder-emails (f.eks. {forslag}) eller tryk ENTER for at springe over: {C.RESET}").strip()
            if not domain:
                return

        print(f"\n{C.YELLOW}[*] Udfører Corporate Domain Search på '{domain}'...{C.RESET}")
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.api_key}"
        
        try:
            res = requests.get(url, timeout=10).json()
            if "data" in res and "emails" in res["data"]:
                emails = res["data"]["emails"]
                pattern = res["data"].get("pattern", "Ukendt")
                
                print(f"{C.GREEN}    🔥 Fandt {len(emails)} e-mails tilknyttet {domain}!{C.RESET}")
                if pattern:
                    print(f"      -> Det mest brugte e-mail format i firmaet er: {pattern}")
                print(f"      -> Viser de mest relevante:\n")
                
                for emp in emails[:10]: # Viser de 10 vigtigste profiler
                    email_addr = emp.get("value")
                    first = emp.get("first_name", "")
                    last = emp.get("last_name", "")
                    position = emp.get("position", "")
                    
                    name_str = f"{first} {last}".strip()
                    name_disp = f"({name_str})" if name_str else ""
                    pos_disp = f"- {position}" if position else ""
                    
                    print(f"{C.GREEN}      ✓ {email_addr} {name_disp} {pos_disp}{C.RESET}")
                    
                self.results["Hunter_Data"] = res["data"]
                
                if len(emails) > 10:
                    print(f"{C.CYAN}    ... og {len(emails)-10} flere (Gemt i rapporten til senere brug).{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen offentlige e-mails fundet for domænet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Hunter.io Fejl: {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/02_BUSINESS_{self.name.replace(' ', '_').replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")