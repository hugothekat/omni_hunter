# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search

class PhoneIntelligenceHunter:
    """Deep web search for phone number occurrences"""
    def __init__(self, phone):
        self.phone = phone.replace(" ", "").replace("+45", "").replace("-", "")
        self.data = {
            "Nummer": f"+45 {self.phone}",
            "Web_Spor": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        """Execute phone search"""
        print(f"\n{C.CYAN}{'='*60}\n[07] Telefon-efterretning (Dorking Matrix)\n{'='*60}{C.RESET}")
        print(f"Target: +45 {self.phone}\n")

        # Bygger alle tænkelige måder et dansk nummer kan skrives på
        formats = [
            f'"{self.phone}"',
            f'"{self.phone[:2]} {self.phone[2:4]} {self.phone[4:6]} {self.phone[6:8]}"',
            f'"{self.phone[:4]} {self.phone[4:]}"',
            f'"{self.phone[:2]}-{self.phone[2:4]}-{self.phone[4:6]}-{self.phone[6:8]}"',
            f'"+45{self.phone}"',
            f'"+45 {self.phone}"'
        ]
        
        print(f"{C.YELLOW}[*] Udruller massiv søgning på {len(formats)} tal-formater...{C.RESET}")
        
        # Samler alt i ét stort DORK call for stealth og speed
        combined_dork = " OR ".join(formats)
        
        # Bruger nu din centrale omni_dork_search for anti-bot beskyttelse og bing-fallback
        links = omni_dork_search(driver, combined_dork, max_links=10)
        
        if links:
            for link in links:
                href = link["url"]
                # Vi ignorerer krak/dgs da vi allerede har et dedikeret modul (12) til det
                if "krak.dk" not in href and "degulesider.dk" not in href:
                    print(f"{C.GREEN}    🔥 SPOR: {href[:80]}{C.RESET}")
                    if href not in self.data["Web_Spor"]:
                        self.data["Web_Spor"].append(href)
        else:
            print(f"{C.DIM}    [-] Ingen offentlige spor fundet udover standard registre.{C.RESET}")
        
        self.save()

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/07_PHONE_{self.phone}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")