import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class UsernameMatrixAnalyzer:
    """Scanner +300 platforme for et specifikt brugernavn via Sherlock"""
    def __init__(self, username):
        self.username = username.strip()
        self.data = {"Brugernavn": self.username, "Platforme": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[23] Global Username Matrix (Sherlock)\n{'='*60}{C.RESET}")
        print(f"[*] Scanner 300+ platforme for brugernavnet: {self.username} (Dette kan tage et par minutter)...")
        
        try:
            # Kræver at 'sherlock' er installeret via pip (pip install sherlock-project)
            result = subprocess.run(['sherlock', self.username, '--timeout', '5', '--print-found'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "[+]" in line:
                    site_url = line.split("[+]")[1].strip()
                    print(f"{C.GREEN}    🔥 PROFIL FUNDET: {site_url}{C.RESET}")
                    self.data["Platforme"].append(site_url)
                    
            if not self.data["Platforme"]:
                print(f"{C.YELLOW}    [-] Ingen profiler fundet for {self.username}.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}    [!] 'sherlock' er ikke installeret. Kør 'pip install sherlock-project'.{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/23_MATRIX_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")