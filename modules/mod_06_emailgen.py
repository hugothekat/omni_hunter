import os
import json
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search

class EmailPatternGenerator:
    """Generates and validates email address patterns from name"""
    def __init__(self, name):
        parts = name.lower().split()
        self.first = parts[0] if len(parts) > 0 else ""
        self.last = parts[-1] if len(parts) > 1 else ""
        self.name = name
        self.data = {
            "Navn": name,
            "Generated_Emails": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[06] E-mail-mønster Validering\n{'='*60}{C.RESET}")
        print(f"Target: {self.name}\n")
        
        domains = ["gmail.com", "hotmail.com", "live.dk", "mail.dk", "outlook.dk"]
        patterns = [f"{self.first}.{self.last}", f"{self.first}{self.last}", f"{self.first[0]}{self.last}"]
        
        all_emails = [f"{p}@{d}" for p in patterns for d in domains]
        
        # Vi sender alle mønstre afsted i én stor "OR" søgning via Anti-Ban motoren
        batch_query = " OR ".join([f'"{e}"' for e in all_emails])
        links = omni_dork_search(driver, batch_query, max_links=15)
        
        found_emails = set()
        for link in links:
            text = link["text"].lower()
            for email in all_emails:
                if email in text:
                    found_emails.add(email)
                    print(f"{C.GREEN}    ✓ BEKRÆFTET MØNSTER: {email}{C.RESET}")
        
        self.data["Generated_Emails"] = list(found_emails)
        self.save()

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/05_EMAILGEN_{self.first}_{self.last}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n[✓] Report saved: {filename}")