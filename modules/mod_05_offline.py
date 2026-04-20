# -*- coding: utf-8 -*-
import subprocess
import json
import os
import re
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class OfflineDatabaseAnalyzer:
    def __init__(self, target, file_path):
        self.target = target.strip()
        self.file_path = file_path.strip()
        self.data = {
            "Mål": self.target, 
            "Fil": self.file_path, 
            "Hits": [], 
            "Credentials": [], 
            "Hashes": [],
            "Timestamp": datetime.now().isoformat()
        }
        
        # Regex for at fange almindelige kryptografiske hashes i lækager
        self.hash_patterns = [
            r'\b[A-Fa-f0-9]{32}\b',           # MD5
            r'\b[A-Fa-f0-9]{40}\b',           # SHA1
            r'\b[A-Fa-f0-9]{64}\b',           # SHA256
            r'\$2[ayb]\$[0-9]{2}\$[A-Za-z0-9\.\/]{53}' # Bcrypt
        ]

    def run(self):
        print(f"\n{C.CYAN}{'='*60}\n[05] Offline Database Analyse (Ripgrep Context Engine)\n{'='*60}{C.RESET}")
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Databasefil ikke fundet: {self.file_path}{C.RESET}")
            return
            
        print(f"{C.YELLOW}[*] Kører High-Speed scan på {os.path.basename(self.file_path)} med kontekst...{C.RESET}")
        try:
            result = subprocess.run(['rg', '-z', '-i', '-m', '100', '-C', '1', self.target, self.file_path], capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and "--" not in line: 
                        clean_line = line.strip()
                        print(f"{C.GREEN}    🔥 HIT: {clean_line[:150]}...{C.RESET}")
                        self.data["Hits"].append(clean_line)
                        
                        # 1. Auto-ekstrahering af plaintext passwords (fx email:pass eller email;pass)
                        # Tillader :, ; og | som adskiller
                        split_chars = re.split(r'[:;|]', clean_line)
                        if len(split_chars) >= 2 and self.target in split_chars[0]:
                            self.data["Credentials"].append({"Konto": split_chars[0].strip(), "Secret": split_chars[-1].strip()})
                            
                        # 2. Advanced Hash Detection
                        for pattern in self.hash_patterns:
                            hashes = re.findall(pattern, clean_line)
                            for h in hashes:
                                if h not in self.data["Hashes"]:
                                    self.data["Hashes"].append(h)
                                    print(f"{C.RED}      -> KRYPTOGRAFISK HASH FUNDET: {h}{C.RESET}")
                                
                print(f"\n{C.YELLOW}[*] Fandt {len(self.data['Hits'])} rå matches, {len(self.data['Credentials'])} mulige passwords og {len(self.data['Hashes'])} hashes.{C.RESET}")
            else:
                print(f"{C.DIM}    [-] Ingen matches i databasen.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}[!] Fejl: Ripgrep er ikke installeret. Kør 'sudo apt install ripgrep'.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Systemfejl under database scanning: {e}{C.RESET}")
            
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/05_OFFLINE_{self.target.replace('@','_at_').replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")