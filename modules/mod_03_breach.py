# -*- coding: utf-8 -*-
import requests
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import omni_dork_search

class BreachIntelligenceAnalyst:
    def __init__(self, email):
        self.email = email.strip()
        self.data = {
            "Email": self.email, 
            "Paste_Sites": [], 
            "Data_Leaks": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[03] Breach Analyse (XposedOrNot & Fast Dorks)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        self._update_progress(20, "Forbinder til gratis OSINT API")
        
        self._check_xposedornot()
        
        self._update_progress(60, "Bygger massiv Paste-Dork")
        print(f"\n{C.YELLOW}[*] Udforer High-Speed Dorking mod Paste-sites...{C.RESET}")
        
        sites = ["pastebin.com", "throwbin.io", "ghostbin.co", "rentry.co", "controlc.com", "justpaste.it"]
        sites_query = " OR ".join([f"site:{site}" for site in sites])
        dork = f'({sites_query}) "{self.email}"'
        
        self._update_progress(80, "Soger globalt via Selenium")
        links = omni_dork_search(driver, dork, max_links=5)
        
        sys.stdout.write("\r" + " " * 80 + "\r")
        if links:
            for link in links:
                print(f"{C.GREEN}    🔥 PASTE FUNDET: {link['url'][:80]}{C.RESET}")
                if link["url"] not in self.data["Paste_Sites"]:
                    self.data["Paste_Sites"].append(link["url"])
        else:
            print(f"{C.DIM}    [-] Ingen Paste-laekager fundet via Google.{C.RESET}")

        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"\n{C.GREEN}[✓] Breach-analyse 100% fuldfort.{C.RESET}")
        self.save()

    def _check_xposedornot(self):
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.YELLOW}[*] Slaar op i globale Hacker-databaser (XposedOrNot API)...{C.RESET}")
        
        url = f"https://api.xposedornot.com/v1/check-email/{self.email}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                breaches = data.get("breaches", [])
                if breaches:
                    print(f"{C.RED}    🔥 KRITISK: Emailen findes i {len(breaches)} datalaek!{C.RESET}")
                    for b in breaches[:10]:
                        print(f"{C.YELLOW}      -> Laekket i: {b}{C.RESET}")
                        self.data["Data_Leaks"].append(b)
                    if len(breaches) > 10:
                        print(f"{C.DIM}      -> ... og {len(breaches)-10} mere.{C.RESET}")
            elif res.status_code == 404:
                print(f"{C.GREEN}    ✓ Ingen hits i databasen (Emailen er ikke fundet i kendte laek).{C.RESET}")
            else:
                print(f"{C.DIM}    [-] API gav ukendt statuskode: {res.status_code}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [-] Forbindelsesfejl til XposedOrNot: {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/03_BREACH_{self.email.replace('@', '_at_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")