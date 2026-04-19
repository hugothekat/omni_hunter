import os
import json
import requests
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class WaybackMachineIntelligence:
    """Tjekker Internet Archive for slettede versioner af et link/domæne"""
    def __init__(self, url):
        self.url = url.strip()
        self.data = {"Mål": self.url, "Arkiveret_Link": None, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[25] Wayback Machine Intelligence\n{'='*60}{C.RESET}")
        print(f"[*] Søger i arkivet efter: {self.url}")
        try:
            res = requests.get(f"http://archive.org/wayback/available?url={self.url}", timeout=10).json()
            if "closest" in res.get("archived_snapshots", {}):
                hit = res["archived_snapshots"]["closest"]["url"]
                self.data["Arkiveret_Link"] = hit
                print(f"{C.GREEN}    🔥 ARKIVERET VERSION FUNDET: {hit}{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen arkiveret version fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved arkiv-søgning: {e}{C.RESET}")
        
        # Gem logik
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/25_WAYBACK_{self.url.replace('/', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4), encoding="utf-8")