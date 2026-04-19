import json
import os
import re
import urllib.parse
import requests
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class DarkWebIntelligence:
    """Searches dark web (Tor/Onion) metadata via Ahmia (No-Browser API Method)"""
    def __init__(self, query):
        self.query = query.strip()
        self.data = {"Søgning": self.query, "Onion_Links": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver): # Vi beholder 'driver' som parameter så main() ikke crasher, men vi ignorerer den
        print(f"\n{C.CYAN}{'='*60}\n[08] Mørkenet-efterretning (Tor) (Ahmia)\n{'='*60}{C.RESET}")
        print(f"Query: {self.query}\n")
        
        url = f"https://ahmia.fi/search/?q={urllib.parse.quote(self.query)}"
        print(f"{C.YELLOW}[*] Sender lynhurtig request til Ahmia...{C.RESET}")
        
        try:
            # Drop Selenium, brug direkte requests!
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=10)
            
            # Find alle .onion links direkte i HTML'en via regex
            onions = set(re.findall(r'[a-z2-7]{16,56}\.onion', res.text))
            
            for o in list(onions)[:10]: # Vis top 10
                print(f"{C.GREEN}    ✓ ONION HIT: {o}{C.RESET}")
                self.data["Onion_Links"].append(o)
                
            if not onions:
                print(f"{C.YELLOW}    [-] Ingen nævneværdige .onion resultater fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] API Fejl ved Ahmia: {e}{C.RESET}")
        
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/08_DARKWEB_{self.query.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")