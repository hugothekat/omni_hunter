# -*- coding: utf-8 -*-
import os
import json
import glob
import itertools
import re
from datetime import datetime
from pathlib import Path
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake

# Omdøbt fra GoliathSniperEngine til SniperModule for kompatibilitet med Modul 02 Pivot
class SniperModule(BaseModule):
    """Universal og interaktiv wordlist generator med avanceret mangling (GOLIATH V8)."""
    
    # Opdateret init for at tillade Pivot kald (name, email) OG manuelt kald
    def __init__(self, name, email="", city="", cpr="", clues="", json_folder=None):
        self.target_name = name.strip()
        self.email = email.strip()
        self.city = city.strip()
        
        super().__init__()
        self.name = "SNIPER WORDLIST GENERATOR"
        self.category = ModuleCategory.FORENSICS
        self.cpr = cpr.replace("-", "").strip()
        self.clues = [c.strip() for c in clues.split(",") if c.strip()]
        
        # Sætter json_folder til systemets loot_folder som standard for auto-ingestion
        self.json_folder = json_folder or session.get("loot_folder", "./loot")
        self.wordlist = set()
        
        self.name_parts = self.target_name.split()
        self.dates = self._extract_dates()
        
        # V8: Bygger basale seeds (ignorerer tomme strenge)
        self.seeds = {s for s in (self.name_parts + [self.city] + self.clues + [self.email.split('@')[0]]) if s}
        
        self.leaked_passwords = set() # NY V8 TILFØJELSE: Til tidligere passwords

    def run(self, driver=None, target=""):
        """NY V8: Standard run() funktion for Omni-Pivot integration"""
        print(f"\n{C.CYAN}{'='*60}\n[17] GOLIATH SNIPER (Targeted Password Profiling V8)\n{'='*60}{C.RESET}")
        print(f"[*] Initialiserer Sniper Profiling for: {self.target_name.upper() if self.target_name else target.upper()}")
        
        # Udfører data ingestion på tværs af moduler
        if self.json_folder:
            self._ingest_json_data()
            
        self.generate()

    def _extract_dates(self):
        # Udvidet V8 dato-matriks
        dates = ["2023", "2024", "2025", "23", "24", "25", "123", "1234"]
        if len(self.cpr) >= 6:
            ddmm, yy = self.cpr[:4], self.cpr[4:6]
            yyyy = ("19" if int(yy) > 25 else "20") + yy
            dates.extend([ddmm, yy, yyyy, f"{yy}{ddmm}", f"{yyyy}{ddmm}"])
        return list(set(dates))

    def _leetspeak(self, word):
        subs = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        res = word.lower()
        for char, repl in subs.items(): res = res.replace(char, repl)
        return res
        
    def _advanced_leetspeak(self, word):
        """NY V8: Mere aggressiv leetspeak til hardcore brugere"""
        subs = {'a': '@', 'i': '!', 's': '$', 'o': '0', 'e': '3', 'l': '1'}
        res = word.lower()
        for char, repl in subs.items(): res = res.replace(char, repl)
        return res

    def _ingest_json_data(self):
        """NY V8: Central Ingestion Hub - Henter data fra ALLE tidligere moduler!"""
        print(f"{C.YELLOW}[*] Støvsuger loot-mappen for tidligere efterretninger (Cross-Pollination)...{C.RESET}")
        self._ingest_secrets()
        self._ingest_breach_data()
        self._ingest_social_data()

    def _ingest_secrets(self):
        """Henter fundne passwords fra TITAN rapporter til at forbedre wordlisten."""
        for f_path in glob.glob(os.path.join(self.json_folder, "16_TITAN_*.json")):
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    secrets = data.get("Case_Intelligence", {}).get("secrets", [])
                    for s in secrets:
                        if s.get("type") == "Generic_Secret":
                            self.seeds.add(s.get("val"))
                            print(f"{C.GREEN}    [+] Sniper genbruger TITAN secret: {s.get('val')[:5]}...{C.RESET}")
            except Exception: continue

    def _ingest_breach_data(self):
        """NY V8: Henter dekrypterede og lækkede passwords fra Modul 03 og 05!"""
        breach_files = glob.glob(os.path.join(self.json_folder, "03_BREACH_*.json")) + \
                       glob.glob(os.path.join(self.json_folder, "05_OFFLINE_*.json"))
                       
        for f_path in breach_files:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Fra Breach Modul
                    for pwd in data.get("Eksponerede_Passwords", []):
                        self.leaked_passwords.add(pwd)
                        print(f"{C.RED}    🔥 Lækket Password Indsat i Profil: {pwd[:3]}***{C.RESET}")
                        
                    # Fra Offline DB Modul
                    for cred in data.get("Credentials", []):
                        self.leaked_passwords.add(cred.get("Secret"))
                        print(f"{C.RED}    🔥 Offline Password Indsat i Profil: {cred.get('Secret')[:3]}***{C.RESET}")
            except Exception: continue

    def _ingest_social_data(self):
        """NY V8: Henter aliaser fra Modul 04 (Social Stalker)"""
        for f_path in glob.glob(os.path.join(self.json_folder, "04_SOCIAL_*.json")):
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for alias in data.get("Identificerede_Aliaser", []):
                        self.seeds.add(alias)
                    if data.get("Brugernavn"):
                        self.seeds.add(data.get("Brugernavn"))
                        print(f"{C.CYAN}    [+] Socialt Alias Tilføjet: {data.get('Brugernavn')}{C.RESET}")
            except Exception: continue

    def generate(self):
        # V8 Suffix udvidelse
        suffixes = ["!", "123", "!", "#", "_", ".", "?", "!!", "2024!", "2025!"]
        
        print(f"\n{C.YELLOW}[*] Skaber avancerede ord-kombinationer ud fra {len(self.seeds)} seed-ord og {len(self.leaked_passwords)} lækkede passwords...{C.RESET}")
        
        # 1. Permutationer (Sætter to ord sammen)
        for combo in itertools.permutations(list(self.seeds), 2):
            self.wordlist.add(f"{combo[0].capitalize()}{combo[1].lower()}")
            self.wordlist.add(f"{combo[0].lower()}{combo[1].lower()}")
            self.wordlist.add(f"{combo[0].capitalize()}{combo[1].capitalize()}")

        # 2. Dato, Suffix og Leetspeak mangling
        for base in self.seeds:
            if len(base) < 3: continue # Ignorerer for korte fraser for at spare memory
            
            variations = [base.lower(), base.capitalize(), base.upper(), self._leetspeak(base), self._advanced_leetspeak(base)]
            
            for m in variations:
                self.wordlist.add(m)
                for d in self.dates:
                    self.wordlist.add(f"{m}{d}")
                    for s in suffixes:
                        self.wordlist.add(f"{m}{d}{s}")
                        self.wordlist.add(f"{m}{s}{d}")
                        self.wordlist.add(f"{m}{s}")
                        
        # 3. NY V8: Password Profiling (Mennesker genbruger gamle passwords med nye årstal)
        for pwd in self.leaked_passwords:
            if not pwd: continue
            self.wordlist.add(pwd)
            self.wordlist.add(pwd + "!")
            self.wordlist.add(pwd + "123")
            
            # Skræller tal og specialtegn af enden på det gamle password for at finde "kernen"
            core_match = re.match(r'^([A-Za-z]+)', pwd)
            if core_match:
                core = core_match.group(1)
                for d in self.dates:
                    self.wordlist.add(f"{core}{d}")
                    self.wordlist.add(f"{core.capitalize()}{d}!")
                    self.wordlist.add(f"{core}{d}!")

        self._save()

    def _save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        path = os.path.join(session["loot_folder"], f"17_SNIPER_{self.target_name.replace(' ', '_')}.txt")
        
        # Filtrerer alt under 6 tegn for at fjerne junk, og max 32 for at optimere hashcat
        final = [w for w in self.wordlist if 6 <= len(w) <= 32]
        
        # Sorterer: Tildeler højere prioritet til ord der indeholder target name eller gamle passwords
        final = sorted(final, key=lambda x: (not any(c.lower() in x.lower() for c in self.seeds), len(x)))
        
        with open(path, "w", encoding="utf-8") as f:
            for w in final:
                f.write(f"{w}\n")

        # Ingest metadata til datalake
        self.data = {
            "Target": self.target_name,
            "Wordlist_Path": path,
            "Word_Count": len(final),
            "Timestamp": datetime.now().isoformat()
        }
        datalake.ingest(self.name, self.target_name, self.data)
                
        print(f"{C.GREEN}[✓] WORDLIST KLAR: {path} ({len(final)} unikke, målrettede kombinationer){C.RESET}")
        
        # NY V8: Taktisk Hashcat command
        print(f"\n{C.MAGENTA}    🔥 Taktisk Hashcat Kommando (WPA2 Eksempel):{C.RESET}")
        print(f"       hashcat -m 2500 capture.hccapx {path} -r rules/best64.rule")
        print(f"{C.MAGENTA}    🔥 Taktisk JohnTheRipper Kommando (Zip Arkiv):{C.RESET}")
        print(f"       john --wordlist={path} target_zip_hash.txt")

# Beholder originalt klassenavn som fallback alias hvis andre af dine scripts benytter det
GoliathSniperEngine = SniperModule