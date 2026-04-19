# modules/mod_25_wayback.py
import os
import json
import requests
from datetime import datetime
from core.utils import C, session

class WaybackMachineIntelligence:
    def __init__(self, url):
        self.url = url.strip()
        self.data = {"Mål": self.url, "Arkiveret_Link": None, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[25] Wayback Bevissikring (Auto-Downloader)\n{'='*60}{C.RESET}")
        print(f"[*] Søger i Internet Archive efter slettet indhold: {self.url}")
        
        try:
            res = requests.get(f"http://archive.org/wayback/available?url={self.url}", timeout=10).json()
            if "closest" in res.get("archived_snapshots", {}):
                hit = res["archived_snapshots"]["closest"]["url"]
                self.data["Arkiveret_Link"] = hit
                print(f"{C.GREEN}    🔥 ARKIVERET VERSION FUNDET: {hit}{C.RESET}")
                
                # Bevissikring: Download hele siden offline
                self._download_archive(hit)
            else:
                print(f"{C.YELLOW}    [-] Ingen arkiveret version fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved arkiv-søgning: {e}{C.RESET}")
        
        self.save()

    def _download_archive(self, archive_url):
        print(f"{C.YELLOW}    [*] Downloader offline kopi til bevissikring...{C.RESET}")
        try:
            # Wayback machine tilføjer "id_" til URL'en for at give dig den RÅ originale HTML uden deres top-bar
            raw_url = archive_url.replace("/web/", "/web/id_/", 1)
            page_data = requests.get(raw_url, timeout=20).text
            
            mappe = os.path.join(session["loot_folder"], "wayback_archives")
            os.makedirs(mappe, exist_ok=True)
            
            safe_name = self.url.replace("https://", "").replace("http://", "").replace("/", "_")
            filsti = os.path.join(mappe, f"OFFLINE_{safe_name}.html")
            
            with open(filsti, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(page_data)
                
            print(f"{C.GREEN}    ✓ Komplet webside sikret offline: {filsti}{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [-] Kunne ikke downloade rå HTML: {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        safe_url = self.url.replace("https://", "").replace("/", "_")
        filename = f"{session['loot_folder']}/25_WAYBACK_{safe_url}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)