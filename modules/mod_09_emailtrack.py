# modules/mod_09_emailtrack.py
import json
import os
import hashlib
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# Henter fra Core
from core.utils import C, session
from core.network import CONFIG

class EmailTracker:
    def __init__(self, email):
        self.email = email.strip()
        self.api_key = CONFIG.get("api_keys", {}).get("hunter_io", "")
        self.data = {
            "Email": self.email, 
            "Gravatar_Hash": hashlib.md5(self.email.lower().encode()).hexdigest(), 
            "Gravatar_Data": {}, 
            "Holehe_Hits": [], 
            "Hunter_Data": {},
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, _=None):
        print(f"\n{C.CYAN}{'='*60}\n[09] E-mail Tracker (Hunter.io, Gravatar & Holehe)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        # 1. Hunter.io Intelligence
        self._check_hunter()
        
        # 2. Gravatar Tjek
        h = self.data["Gravatar_Hash"]
        print(f"\n{C.YELLOW}[*] Checker Gravatar API...{C.RESET}")
        try:
            res = requests.get(f"https://en.gravatar.com/{h}.json", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if res.status_code == 200:
                grav_json = res.json()
                if "entry" in grav_json and grav_json["entry"]:
                    entry = grav_json["entry"][0]
                    print(f"{C.GREEN}    ✓ Offentlig Gravatar Profil Fundet!{C.RESET}")
                    if "displayName" in entry:
                        self.data["Gravatar_Data"]["Navn"] = entry["displayName"]
                        print(f"      -> Navn: {entry['displayName']}")
        except Exception: pass

        # 3. Holehe Integration 
        print(f"\n{C.YELLOW}[*] Kører Holehe OSINT engine for at finde registrerede profiler...{C.RESET}")
        try:
            result = subprocess.run(['holehe', self.email, '--only-used'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "[+]" in line:
                    site = line.split("]")[1].strip()
                    print(f"{C.GREEN}    ✓ Konto fundet på: {site}{C.RESET}")
                    self.data["Holehe_Hits"].append(site)
            if not self.data["Holehe_Hits"]:
                print(f"{C.DIM}    [-] Holehe fandt ingen åbne profiler.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}    [!] 'holehe' er ikke installeret.{C.RESET}")

        self.save()

    def _check_hunter(self):
        """Bruger Hunter.io til Verification og Person Enrichment"""
        if not self.api_key:
            print(f"{C.DIM}[-] Springer Hunter.io over (Mangler API-nøgle i config.json){C.RESET}")
            return

        print(f"{C.YELLOW}[*] Kontakter Hunter.io for Corporate Intelligence...{C.RESET}")
        
        # A. Email Verifier
        ver_url = f"https://api.hunter.io/v2/email-verifier?email={self.email}&api_key={self.api_key}"
        try:
            res = requests.get(ver_url, timeout=10).json()
            if "data" in res:
                status = res["data"]["status"]
                score = res["data"]["score"]
                
                # Farvekodning baseret på score
                color = C.GREEN if score > 70 else (C.YELLOW if score > 40 else C.RED)
                print(f"{color}    ✓ Status: {status.upper()} (Sikkerhedsscore: {score}/100){C.RESET}")
                self.data["Hunter_Data"]["Verification"] = res["data"]
        except Exception as e:
            print(f"{C.DIM}    [!] Kunne ikke verificere email: {e}{C.RESET}")

        # B. Combined Enrichment (Person + Company)
        enr_url = f"https://api.hunter.io/v2/combined/find?email={self.email}&api_key={self.api_key}"
        try:
            res = requests.get(enr_url, timeout=10).json()
            if "data" in res and res["data"]:
                data = res["data"]
                print(f"{C.GREEN}    🔥 Person & Firma Berigelse Fundet!{C.RESET}")
                
                first = data.get("first_name", "")
                last = data.get("last_name", "")
                company = data.get("company", "")
                position = data.get("position", "")
                twitter = data.get("twitter", "")
                linkedin = data.get("linkedin", "")

                if first or last: print(f"      -> Navn: {first} {last}")
                if company: print(f"      -> Firma: {company}")
                if position: print(f"      -> Stilling: {position}")
                if linkedin: print(f"      -> LinkedIn: {linkedin}")
                if twitter: print(f"      -> Twitter: {twitter}")

                self.data["Hunter_Data"]["Enrichment"] = data
        except Exception:
            pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/09_EMAILTRACK_{self.email.replace('@', '_at_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")