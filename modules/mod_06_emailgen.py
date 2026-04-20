# -*- coding: utf-8 -*-
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search

class EmailPatternGenerator:
    """Generates and validates email address patterns from name"""
    def __init__(self, name):
        parts = name.lower().split()
        self.first = parts[0] if len(parts) > 0 else "unknown"
        self.last = parts[-1] if len(parts) > 1 else self.first
        self.name = name
        self.data = {
            "Navn": name,
            "Generated_Emails": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[06] E-mail-mønster Validering (OSINT Engine)\n{'='*60}{C.RESET}")
        print(f"Target: {self.name}\n")
        
        # Udvidet domæneliste for moderne trusselsbilleder
        domains = ["gmail.com", "hotmail.com", "live.dk", "mail.dk", "outlook.dk", "yahoo.com", "icloud.com", "proton.me"]
        
        # Flere klassiske corporate og private mønstre
        patterns = [
            f"{self.first}.{self.last}", 
            f"{self.first}{self.last}", 
            f"{self.first[0]}{self.last}",
            f"{self.first[0]}.{self.last}",
            f"{self.last}.{self.first}",
            f"{self.first}_{self.last}"
        ]
        
        all_emails = [f"{p}@{d}" for p in patterns for d in domains]
        print(f"{C.YELLOW}[*] Genererede {len(all_emails)} potentielle email-mønstre. Udfører Dorking validering...{C.RESET}")
        
        # Vi sender mønstrene afsted i "OR" søgninger via Anti-Ban motoren (5 ad gangen for ikke at knække url'en)
        found_emails = set()
        chunk_size = 5
        
        for i in range(0, len(all_emails), chunk_size):
            chunk = all_emails[i:i+chunk_size]
            batch_query = " OR ".join([f'"{e}"' for e in chunk])
            
            sys.stdout.write(f"\r{C.CYAN}    [*] Tester mønstre... {i}/{len(all_emails)}{C.RESET}")
            sys.stdout.flush()
            
            links = omni_dork_search(driver, batch_query, max_links=5)
            if links:
                for link in links:
                    text = link["text"].lower()
                    url_text = link["url"].lower()
                    for email in chunk:
                        if email in text or email in url_text:
                            found_emails.add(email)
                            sys.stdout.write("\r" + " " * 80 + "\r")
                            print(f"{C.GREEN}    🔥 BEKRÆFTET MØNSTER: {email}{C.RESET}")
                            print(f"{C.DIM}      -> Kilde: {link['url']}{C.RESET}")

        sys.stdout.write("\r" + " " * 80 + "\r")
        self.data["Generated_Emails"] = list(found_emails)
        if not found_emails:
            print(f"{C.YELLOW}    [-] Ingen email-mønstre kunne bekræftes offentligt.{C.RESET}")
            
        self.save()

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/06_EMAILGEN_{self.first}_{self.last}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")