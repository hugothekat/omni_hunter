import os
import json
import requests
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class BSSIDGeofencer:
    def __init__(self, bssid):
        self.bssid = bssid.strip().replace("-", ":").lower()
        self.data = {"BSSID": self.bssid, "Fundet": False, "Lat": None, "Lon": None, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[21] BSSID Geofencer (MAC Lokations-sporing)\n{'='*60}{C.RESET}")
        print(f"[*] Søger efter router MAC i global database: {self.bssid}")

        # Bruger Mylnikov Open Wifi API (Åben database)
        url = f"https://api.mylnikov.org/geolocation/wifi?v=1.1&data={self.bssid}"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("result") == 200:
                self.data["Fundet"] = True
                self.data["Lat"] = res["data"]["lat"]
                self.data["Lon"] = res["data"]["lon"]

                maps_url = f"https://www.google.com/maps?q={self.data['Lat']},{self.data['Lon']}"

                print(f"{C.GREEN}    🔥 BINGO! Fysisk lokation fastslået!{C.RESET}")
                print(f"{C.GREEN}    ✓ Breddegrad: {self.data['Lat']}{C.RESET}")
                print(f"{C.GREEN}    ✓ Længdegrad: {self.data['Lon']}{C.RESET}")
                print(f"{C.CYAN}    -> Google Maps: {maps_url}{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Routeren findes ikke i de åbne databaser.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved API opslag: {e}{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/21_BSSID_{self.bssid.replace(':', '')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")