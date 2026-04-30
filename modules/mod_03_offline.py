# -*- coding: utf-8 -*-
import subprocess
import json
import os
import re
import requests # NY V8: Tilføjet til Auto-Dehash API
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class OfflineDatabaseAnalyzer:
    def __init__(self, target, file_path):
        self.target = target.strip()
        self.file_path = file_path.strip()
        self.data = {
            "Mål": self.target, 
            "Sti": self.file_path, 
            "Hits": [], 
            "Credentials": [], 
            "Hashes": [],
            "Cracked_Hashes": [], 
            "Tokens": [],         
            "Timestamp": datetime.now().isoformat()
        }
        
        self.hash_patterns = [
            r'\b[A-Fa-f0-9]{32}\b',           # MD5
            r'\b[A-Fa-f0-9]{40}\b',           # SHA1
            r'\b[A-Fa-f0-9]{64}\b',           # SHA256
            r'\$2[ayb]\$[0-9]{2}\$[A-Za-z0-9\.\/]{53}' # Bcrypt
        ]
        
        self.token_patterns = [
            r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', # JWT Token
            r'ghp_[a-zA-Z0-9]{36}',                                       # GitHub Token
            r'xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}'             # Slack Token
        ]

    def run(self, driver=None, target=""):
        if target:
            self.target = target.strip()
            self.data["Mål"] = self.target
        
        if not self.file_path:
            self.file_path = session.get("loot_folder", "loot_evidence")

        print(f"\n{C.CYAN}{'='*60}\n[05] Offline Database Analyse (Ripgrep & Auto-Dehash V8)\n{'='*60}{C.RESET}")
        
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Database-sti ikke fundet: {self.file_path}{C.RESET}")
            return
            
        if os.path.isdir(self.file_path):
            print(f"{C.YELLOW}[*] Mapper valgt: Kører Mass-Directory Scan på alt indhold i {self.file_path}...{C.RESET}")
        else:
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
                        
                        split_chars = re.split(r'[:;|]', clean_line)
                        if len(split_chars) >= 2 and self.target.lower() in split_chars[0].lower():
                            self.data["Credentials"].append({"Konto": split_chars[0].strip(), "Secret": split_chars[-1].strip()})
                            
                        for pattern in self.hash_patterns:
                            hashes = re.findall(pattern, clean_line)
                            for h in hashes:
                                if h not in self.data["Hashes"]:
                                    self.data["Hashes"].append(h)
                                    print(f"{C.RED}      -> KRYPTOGRAFISK HASH FUNDET: {h}{C.RESET}")
                                    
                        for t_pat in self.token_patterns:
                            tokens = re.findall(t_pat, clean_line)
                            for t in tokens:
                                if t not in self.data["Tokens"]:
                                    self.data["Tokens"].append(t)
                                    print(f"{C.MAGENTA}      -> SESSION/API TOKEN FUNDET: {t[:40]}...{C.RESET}")
                                
                print(f"\n{C.YELLOW}[*] Fandt {len(self.data['Hits'])} rå matches, {len(self.data['Credentials'])} mulige passwords og {len(self.data['Hashes'])} hashes.{C.RESET}")
                
                if self.data["Hashes"]:
                    self._auto_dehash()
                    
            else:
                print(f"{C.DIM}    [-] Ingen matches i databasen for {self.target}.{C.RESET}")
                
        except FileNotFoundError:
            print(f"{C.RED}[!] Fejl: Ripgrep er ikke installeret på systemet. Kør 'sudo apt install ripgrep' først!{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Systemfejl under database scanning: {e}{C.RESET}")
            
        self.save()
        return self.data

    def _auto_dehash(self):
        print(f"\n{C.YELLOW}[*] INITIERER AUTO-DEHASH: Forsøger at knække fundne hashes i realtid...{C.RESET}")
        
        for h in self.data["Hashes"]:
            if len(h) == 32:
                try:
                    res = requests.get(f"https://nitrxgen.net/md5db/{h}", timeout=5)
                    if res.status_code == 200 and res.text:
                        cracked = res.text.strip()
                        print(f"{C.RED}      💥 HASH KNÆKKET: {h} -> {cracked}{C.RESET}")
                        self.data["Cracked_Hashes"].append({"Hash": h, "Plaintext": cracked})
                        self.data["Credentials"].append({"Konto": self.target, "Secret": cracked, "Source": "Auto-Dehash"})
                    else:
                        print(f"{C.DIM}      [-] Kunne ikke knække MD5: {h}{C.RESET}")
                except Exception:
                    pass
            elif len(h) > 32:
                print(f"{C.DIM}      [-] Hash typen (SHA1/SHA256/Bcrypt) er for kompleks til Auto-Dehash. Gemmes til Hashcat.{C.RESET}")

    def save(self):
        folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(folder, exist_ok=True)
        clean_target = sanitize_filename(self.target.replace('@','_at_'))
        filename = f"{folder}/05_OFFLINE_{clean_target}.json"
        
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Offline-scan rapport gemt: {filename}{C.RESET}")