import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class OfflineDatabaseAnalyzer:
    """High-speed analysis of large local databases using Ripgrep (inkl. komprimerede .gz/.zip)"""
    def __init__(self, target, file_path):
        self.target = target.strip()
        self.file_path = file_path.strip()
        self.data = {"Mål": self.target, "Fil": self.file_path, "Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self):
        print(f"\n{C.CYAN}{'='*60}\n[05] Offline Database Analyse (Ripgrep Engine)\n{'='*60}{C.RESET}")
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Databasefil ikke fundet: {self.file_path}{C.RESET}"); return
            
        print(f"[*] Kører High-Speed scan på {os.path.basename(self.file_path)}...")
        try:
            # -z flaget tillader søgning direkte i komprimerede filer!
            result = subprocess.run(['rg', '-z', '-i', '-m', '50', self.target, self.file_path], capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"{C.GREEN}    🔥 HIT: {line.strip()[:150]}...{C.RESET}")
                        self.data["Hits"].append(line.strip())
                print(f"\n{C.YELLOW}[*] Fandt {len(self.data['Hits'])} matches.{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen matches i databasen.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}[!] Fejl: Ripgrep er ikke installeret. Kør 'sudo apt install ripgrep'.{C.RESET}")
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/05_OFFLINE_{self.target.replace('@','_').replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")