import subprocess
import json
import os
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class OfflineDatabaseAnalyzer:
    def __init__(self, target, file_path):
        self.target = target.strip()
        self.file_path = file_path.strip()
        self.data = {"Mål": self.target, "Fil": self.file_path, "Hits": [], "Credentials": [], "Timestamp": datetime.now().isoformat()}

    def run(self):
        print(f"\n{C.CYAN}{'='*60}\n[05] Offline Database Analyse (Ripgrep Context Engine)\n{'='*60}{C.RESET}")
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Databasefil ikke fundet: {self.file_path}{C.RESET}")
            return
            
        print(f"{C.YELLOW}[*] Kører High-Speed scan på {os.path.basename(self.file_path)} med kontekst...{C.RESET}")
        try:
            # -z (komprimeret support), -i (ignore case), -m (max hits), -C 1 (1 linje kontekst før/efter)
            result = subprocess.run(['rg', '-z', '-i', '-m', '100', '-C', '1', self.target, self.file_path], capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and "--" not in line: # fjerner ripgrep separators
                        clean_line = line.strip()
                        print(f"{C.GREEN}    🔥 HIT: {clean_line[:150]}...{C.RESET}")
                        self.data["Hits"].append(clean_line)
                        
                        # Auto-ekstrahering af credentials (hvis formatet er email:password)
                        if ":" in clean_line and self.target in clean_line:
                            parts = clean_line.split(":")
                            if len(parts) >= 2:
                                self.data["Credentials"].append({"Konto": parts[0], "Secret": parts[-1]})
                                
                print(f"\n{C.YELLOW}[*] Fandt {len(self.data['Hits'])} rå matches og isolerede {len(self.data['Credentials'])} mulige passwords.{C.RESET}")
            else:
                print(f"{C.DIM}    [-] Ingen matches i databasen.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}[!] Fejl: Ripgrep er ikke installeret. Kør 'sudo apt install ripgrep'.{C.RESET}")
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/05_OFFLINE_{self.target.replace('@','_at_').replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")