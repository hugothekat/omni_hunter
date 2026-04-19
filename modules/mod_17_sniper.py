import os
import json
import glob
import itertools
from core.utils import C, session

class GoliathSniperEngine:
    """Universal og interaktiv wordlist generator med avanceret mangling."""
    def __init__(self, name, city, cpr, clues, json_folder=None):
        self.target_name = name.strip()
        self.city = city.strip()
        self.cpr = cpr.replace("-", "").strip()
        self.clues = [c.strip() for c in clues.split(",") if c.strip()]
        self.json_folder = json_folder
        self.wordlist = set()
        
        self.name_parts = self.target_name.split()
        self.dates = self._extract_dates()
        self.seeds = set(self.name_parts + [self.city] + self.clues)
        
        if self.json_folder:
            self._ingest_json_data()

    def _extract_dates(self):
        if len(self.cpr) < 6: return ["2024", "2025", "24"]
        ddmm, yy = self.cpr[:4], self.cpr[4:6]
        yyyy = ("19" if int(yy) > 25 else "20") + yy
        return [ddmm, yy, yyyy, "2024", "24"]

    def _leetspeak(self, word):
        subs = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        res = word.lower()
        for char, repl in subs.items(): res = res.replace(char, repl)
        return res

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
                            print(f"{C.GREEN}    [+] Sniper genbruger fundet secret: {s.get('val')[:5]}...{C.RESET}")
            except Exception: continue

    def generate(self):
        print(f"\n{C.CYAN}[17] STARTER SNIPER-ENGINE FOR: {self.target_name.upper()}{C.RESET}")
        suffixes = ["!", "123", "!", "#", "_", ".", "2024"]
        
        print("[*] Skaber avancerede ord-kombinationer...")
        for combo in itertools.permutations(list(self.seeds), 2):
            self.wordlist.add(f"{combo[0].capitalize()}{combo[1].lower()}")
            self.wordlist.add(f"{combo[0].lower()}{combo[1].lower()}")

        for base in self.seeds:
            for d in self.dates:
                for s in suffixes:
                    for m in [base.lower(), base.capitalize(), self._leetspeak(base)]:
                        self.wordlist.add(f"{m}{d}")
                        self.wordlist.add(f"{m}{d}{s}")
                        self.wordlist.add(f"{m}{s}{d}")
        self._save()

    def _save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        path = os.path.join(session["loot_folder"], f"17_SNIPER_{self.target_name.replace(' ', '_')}.txt")
        final = sorted(list(self.wordlist), key=lambda x: (not any(c in x for c in self.clues), len(x)))
        with open(path, "w", encoding="utf-8") as f:
            for w in final:
                if 6 <= len(w) <= 20: f.write(f"{w}\n")
        print(f"{C.GREEN}[✓] WORDLIST KLAR: {path} ({len(final)} ord){C.RESET}")