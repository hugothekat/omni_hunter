import json
import os
import sys
import time
import urllib.parse
import requests
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import http, CONFIG, omni_dork_search

class BusinessIntelligenceAnalyst:
    def __init__(self, name):
        self.name = name.strip()
        self.api_key = CONFIG.get("api_keys", {}).get("hunter_io", "")
        self.results = {
            "Mål": self.name, 
            "CVR_Intel": [], 
            "Hunter_Data": {}, 
            "Proff_Links": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        """Klippestabil progress bar der rydder linjen"""
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[02] Erhvervs-efterretning (CVR, Hunter & Proff)\n{'='*60}{C.RESET}")
        print(f"[*] Starter virksomheds-analyse for: {self.name}\n")
        
        self._update_progress(20, "Slår op i CVR-Registeret")
        self._check_cvr()
        
        self._update_progress(50, "Søger i Hunter.io Databasen")
        self._check_hunter()
        
        self._update_progress(80, "Dorking Proff.dk (Regnskaber & Netværk)")
        self._check_proff(driver)
        
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.GREEN}[✓] Erhvervs-analyse 100% fuldført.{C.RESET}")
        self.save()

    def _check_cvr(self):
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.YELLOW}[*] Henter virksomhedsdata via CVR API...{C.RESET}")
        headers = {"User-Agent": "OmniHunter-OSINT-Tool"}
        url = f"https://cvrapi.dk/api?search={urllib.parse.quote(self.name)}&country=dk"
        
        try:
            response = http.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and "error" not in response.text:
                raw_data = response.json()
                
                # --- INTELLIGENCE PARSER: Forhindrer "Ubrugelig JSON" ---
                p_units = raw_data.get("productionunits", [])
                
                clean_intel = {
                    "Virksomhed": raw_data.get("name"),
                    "CVR": raw_data.get("vat"),
                    "Status": raw_data.get("status", "Aktiv"),
                    "Type": raw_data.get("companydesc"),
                    "Hovedadresse": f"{raw_data.get('address')}, {raw_data.get('zipcode')} {raw_data.get('city')}",
                    "Ansatte": raw_data.get("employees"),
                    "Branche": raw_data.get("industrydesc"),
                    "Antal_Afdelinger_P_Numre": len(p_units),
                    "Udvalgte_Afdelinger": [
                        {"Navn": p.get("name"), "Adresse": f"{p.get('address')}, {p.get('city')}"} 
                        for p in p_units[:5] # Viser kun Top 5 for at undgå støj
                    ]
                }

                # Fanger ejere/direktion hvis de findes (CVR API leverer dette på nogle selskaber)
                if raw_data.get("owners"):
                    clean_intel["Ejere_Direktion"] = [o.get("name") for o in raw_data.get("owners", [])]

                print(f"{C.GREEN}    ✓ Virksomhed fundet: {clean_intel['Virksomhed']} (CVR: {clean_intel['CVR']}){C.RESET}")
                print(f"      -> Status: {clean_intel['Status']}")
                print(f"      -> Adresse: {clean_intel['Hovedadresse']}")
                print(f"      -> Ansatte: {clean_intel['Ansatte']}")
                
                if len(p_units) > 5:
                    print(f"{C.DIM}      -> Fandt {len(p_units)} afdelinger (P-numre). Gemmer kun Top 5 for at holde rapporten ren.{C.RESET}")

                # Gemmer den rensede data i toppen af JSON
                self.results["CVR_Intel"].append(clean_intel)
                
                # Gemmer den massive raw data under en anden nøgle, så vi IKKE nerfer scriptet!
                self.results["CVR_Raw_Dump"] = raw_data 

            else:
                print(f"{C.DIM}    [-] Ingen CVR matches fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] CVR API Fejl: {e}{C.RESET}")

    def _check_hunter(self):
        if not self.api_key:
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Mangler API-nøgle i config.json){C.RESET}")
            return

        domain = self.name
        if "." not in domain:
            # Novo Nordisk bruger .com - Vi laver et intelligent gæt
            forslag = self.name.lower().replace(' ', '') + ".com" 
            domain = input(f"\n{C.YELLOW}[?] Indtast domæne for email-udtræk (f.eks. {forslag}) eller tryk ENTER for at springe over: {C.RESET}").strip()
            if not domain:
                return

        print(f"\n{C.YELLOW}[*] Udfører Corporate Domain Search på '{domain}'...{C.RESET}")
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.api_key}"
        
        try:
            res = requests.get(url, timeout=10).json()
            if "data" in res and "emails" in res["data"] and len(res["data"]["emails"]) > 0:
                emails = res["data"]["emails"]
                pattern = res["data"].get("pattern", "Ukendt")
                
                print(f"{C.GREEN}    🔥 Fandt {len(emails)} e-mails tilknyttet {domain}!{C.RESET}")
                if pattern:
                    print(f"      -> Format: {pattern}")
                
                # Renere JSON for Hunter
                clean_emails = []
                for emp in emails[:15]:
                    first = emp.get("first_name", "")
                    last = emp.get("last_name", "")
                    pos = emp.get("position", "")
                    clean_emails.append({
                        "Email": emp.get("value"),
                        "Navn": f"{first} {last}".strip(),
                        "Stilling": pos
                    })
                    print(f"{C.GREEN}      ✓ {emp.get('value')} ({first} {last}) - {pos}{C.RESET}")
                    
                self.results["Hunter_Data"] = {"Format": pattern, "Emails": clean_emails}
                
                if len(emails) > 15:
                    print(f"{C.CYAN}    ... og {len(emails)-15} flere.{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen offentlige e-mails fundet for {domain}.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Hunter.io Fejl: {e}{C.RESET}")

    def _check_proff(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking Proff.dk for nøgletal og netværk...{C.RESET}")
        if driver:
            dork = f'site:proff.dk "{self.name}"'
            links = omni_dork_search(driver, dork, max_links=2)
            if links:
                print(f"{C.GREEN}    ✓ Fandt regnskabs/netværks-data på Proff.dk!{C.RESET}")
                for link in links:
                    print(f"      -> {link['url']}")
                    self.results["Proff_Links"].append(link['url'])
            else:
                print(f"{C.DIM}    [-] Intet fundet på Proff.dk.{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/02_BUSINESS_{self.name.replace(' ', '_').replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")