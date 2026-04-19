import requests
import json
import os
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search, CONFIG

class BreachIntelligenceAnalyst:
    def __init__(self, email):
        self.email = email.strip()
        self.data = {
            "Email": self.email, 
            "Paste_Sites": [], 
            "HIBP_Breaches": [],
            "Free_Breach_Hits": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[03] Lækage-analyse (Hybrid Engine)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        api_key = CONFIG.get("api_keys", {}).get("hibp_api_key", "")
        
        if api_key:
            self._run_hibp(api_key)
        else:
            print(f"{C.YELLOW}[*] Ingen HIBP nøgle fundet. Bruger gratis alternativ (BreachDirectory)...{C.RESET}")
            self._run_free_check()
        
        # Dorking efter open pastes
        print(f"\n{C.YELLOW}[*] Scanner Paste-sites via Dorks...{C.RESET}")
        noise_filter = "-site:microsoft.com -site:wikihow.com"
        for site in ["pastebin.com", "throwbin.io"]:
            dork = f'site:{site} "{self.email}" {noise_filter}'
            links = omni_dork_search(driver, dork, max_links=2)
            for link in links:
                print(f"{C.GREEN}    ✓ PASTE FUNDET: {link['url'][:80]}{C.RESET}")
                if link["url"] not in self.data["Paste_Sites"]:
                    self.data["Paste_Sites"].append(link["url"])

        self.save()

    def _run_hibp(self, api_key):
        print(f"{C.YELLOW}[*] Slår op i HaveIBeenPwned API (Premium)...{C.RESET}")
        headers = {"hibp-api-key": api_key, "user-agent": "OmniHunter-OSINT"}
        try:
            res = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{self.email}?truncateResponse=false", headers=headers, timeout=10)
            if res.status_code == 200:
                breaches = res.json()
                print(f"{C.RED}    🔥 KRITISK: Emailen findes i {len(breaches)} datalæk!{C.RESET}")
                for breach in breaches:
                    b_name, data_classes = breach.get("Name"), breach.get("DataClasses", [])
                    self.data["HIBP_Breaches"].append({"Leak_Name": b_name, "Leaked_Data": data_classes})
                    if "Passwords" in data_classes:
                        print(f"{C.RED}      -> {b_name} (Lækker PASSWORDS!){C.RESET}")
                    else:
                        print(f"{C.YELLOW}      -> {b_name} (Lækker: {', '.join(data_classes[:2])}){C.RESET}")
            elif res.status_code == 404: print(f"{C.GREEN}    ✓ Ingen hits i HIBP.{C.RESET}")
        except Exception as e: print(f"{C.RED}    [!] HIBP Fejl: {e}{C.RESET}")

    def _run_free_check(self):
        try:
            res = requests.get(f"https://breachdirectory.org/api/report?email={self.email}", timeout=10).json()
            if res.get("found", 0) > 0:
                print(f"{C.RED}    🔥 FUNDET i {res['found']} lækkede databaser!{C.RESET}")
                for source in res.get("sources", []):
                    print(f"      -> {source}")
                    self.data["Free_Breach_Hits"].append(source)
            else: print(f"{C.GREEN}    ✓ Ingen hits i BreachDirectory.{C.RESET}")
        except Exception: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/03_BREACH_{self.email.replace('@', '_at_')}.json"
        with open(filename, 'w', encoding='utf-8') as f: json.dump(self.data, f, indent=4, ensure_ascii=False)