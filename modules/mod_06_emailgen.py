# -*- coding: utf-8 -*-
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from core.utils import C, session
from core.network import omni_dork_search

class EmailPatternGenerator:
    def __init__(self, name):
        parts = name.strip().split()
        self.first = parts[0].lower() if len(parts) > 0 else "unknown"
        self.last = parts[-1].lower() if len(parts) > 1 else self.first
        self.middle = parts[1].lower() if len(parts) > 2 else ""
        self.name = name
        self.data = {
            "Navn": name,
            "Generated_Emails": [],
            "Verified_Emails": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[06] E-mail-mønster Validering (GOLIATH V7)\n{'='*60}{C.RESET}")
        print(f"Target: {self.name}\n")
        
        # Udvidet domæneliste for moderne trusselsbilleder og danske brugere
        domains = [
            "gmail.com", "hotmail.com", "live.dk", "mail.com", 
            "yahoo.dk", "yahoo.com", "icloud.com", "me.com", 
            "mac.com", "outlook.dk", "outlook.com", "protonmail.com"
        ]
        
        print(f"{C.YELLOW}[*] Genererer permutations-matrix for e-mails...{C.RESET}")
        
        # Standard Mønstre
        patterns = [
            f"{self.first}{self.last}", f"{self.first}.{self.last}",
            f"{self.first}_{self.last}", f"{self.first[0]}{self.last}",
            f"{self.first}{self.last[0]}", f"{self.last}{self.first}"
        ]
        
        # V7: Udvidede danske mønstre (inkl. mellemnavn og fødselsår)
        if self.middle:
            patterns.extend([
                f"{self.first}{self.middle[0]}{self.last}",
                f"{self.first}.{self.middle[0]}.{self.last}"
            ])
            
        # V7: Tilføjer typiske danske tal-endelser
        extended_patterns = list(patterns)
        for p in patterns:
            extended_patterns.extend([f"{p}88", f"{p}123", f"{p}1"])
            
        for domain in domains:
            for pat in set(extended_patterns):
                email = f"{pat}@{domain}"
                self.data["Generated_Emails"].append(email)

        print(f"{C.GREEN}[+] Genererede {len(self.data['Generated_Emails'])} potentielle e-mails.{C.RESET}")
        
        # --- V7 INTELLIGENS: LIVE DORK VALIDERING ---
        print(f"\n{C.YELLOW}[*] Udfører Live Dork-Validering af de mest sandsynlige e-mails...{C.RESET}")
        if driver:
            # Vi tager kun de mest 'normale' for ikke at spamme Google
            top_targets = [f"{self.first}{self.last}@{d}" for d in ["gmail.com", "hotmail.com"]] + \
                          [f"{self.first}.{self.last}@{d}" for d in ["gmail.com", "hotmail.com"]]
            
            for target_email in top_targets:
                dork = f'"{target_email}"'
                hits = omni_dork_search(driver, dork, max_links=2)
                if hits:
                    print(f"{C.RED}    🔥 BEKRÆFTET E-MAIL FUNDET PÅ NETTET: {target_email}{C.RESET}")
                    for h in hits:
                        print(f"      -> {C.DIM}{h['url']}{C.RESET}")
                    if target_email not in self.data["Verified_Emails"]:
                        self.data["Verified_Emails"].append(target_email)
        else:
            print(f"{C.DIM}[-] Ingen stealth-driver givet. Skipper Live Dork-Validering.{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/06_EMAILGEN_{self.name.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] E-mail rapport gemt: {filename}{C.RESET}")