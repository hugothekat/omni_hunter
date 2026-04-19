# modules/mod_03_breach.py
import requests
import json
import os
from datetime import datetime

# Henter fra Core
from core.utils import C
from core.network import omni_dork_search

class BreachIntelligenceAnalyst:
    """Identificerer emails i åbne paste-sites og lukkede HIBP-databaser"""
    
    def __init__(self, email, config_path="config.json"):
        self.email = email.strip()
        self.data = {
            "Email": self.email, 
            "Paste_Sites": [], 
            "Database_Dumps": [],
            "HIBP_Breaches": [],
            "Timestamp": datetime.now().isoformat()
        }
        
        # Load API key
        try:
            with open(config_path, "r") as f:
                self.config = json.load(f)
        except Exception:
            self.config = {"api_keys": {}}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[03] Lækage-analyse (Breach & HIBP)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        # 1. HIBP API INTEGRATION
        self._check_hibp()
        
        # 2. Dorking efter open pastes (Din eksisterende kode)
        print(f"\n{C.YELLOW}[*] Scanner Paste-sites og open dumps via Dorks...{C.RESET}")
        noise_filter = "-site:microsoft.com -site:wikihow.com"
        
        for site in ["pastebin.com", "throwbin.io"]:
            dork = f'site:{site} "{self.email}" {noise_filter}'
            links = omni_dork_search(driver, dork, max_links=2)
            
            for link in links:
                print(f"{C.GREEN}    ✓ PASTE FUNDET: {link['url'][:80]}{C.RESET}")
                if link["url"] not in self.data["Paste_Sites"]:
                    self.data["Paste_Sites"].append(link["url"])

        self.save()

    def _check_hibp(self):
        """Checker target email mod HaveIBeenPwned databasen"""
        api_key = self.config.get("api_keys", {}).get("hibp_api_key", "")
        
        if not api_key:
            print(f"{C.DIM}    [-] Springer HIBP over (Mangler API Nøgle i config.json){C.RESET}")
            return

        print(f"{C.YELLOW}[*] Slår op i HaveIBeenPwned API'et for lukkede databaser...{C.RESET}")
        
        headers = {
            "hibp-api-key": api_key,
            "user-agent": "OmniHunter-OSINT-Platform"
        }
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{self.email}?truncateResponse=false"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                breaches = res.json()
                print(f"{C.RED}    🔥 KRITISK: Emailen findes i {len(breaches)} kendte datalæk!{C.RESET}")
                
                for breach in breaches:
                    breach_name = breach.get("Name")
                    data_classes = breach.get("DataClasses", [])
                    
                    self.data["HIBP_Breaches"].append({
                        "Leak_Name": breach_name,
                        "Leaked_Data": data_classes
                    })
                    
                    # Fremhæv hvis der er lækket Passwords!
                    if "Passwords" in data_classes:
                        print(f"{C.RED}      -> {breach_name} (Lækker PASSWORDS i cleartext/hash!){C.RESET}")
                    else:
                        print(f"{C.YELLOW}      -> {breach_name} (Lækker: {', '.join(data_classes[:3])}){C.RESET}")
                        
            elif res.status_code == 404:
                print(f"{C.GREEN}    ✓ Ingen hits i HaveIBeenPwned (Emailen er ren!){C.RESET}")
            elif res.status_code == 429:
                print(f"{C.YELLOW}    [-] HIBP Rate limit ramt. Vent et øjeblik.{C.RESET}")
            else:
                print(f"{C.RED}    [-] HIBP API Fejl: HTTP {res.status_code}{C.RESET}")
                
        except Exception as e:
            print(f"{C.RED}    [!] Forbindelsesfejl til HIBP: {e}{C.RESET}")

    def save(self):
        loot_dir = "loot_evidence"
        os.makedirs(loot_dir, exist_ok=True)
        filename = f"{loot_dir}/03_BREACH_{self.email.replace('@', '_at_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
            
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")