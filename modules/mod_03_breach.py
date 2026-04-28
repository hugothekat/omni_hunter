# -*- coding: utf-8 -*-
import json
import os
import time
import requests
import re
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import http, omni_dork_search
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BreachIntelligenceAnalyst:
    """PETFE GOLIATH V12 - Syndicated Breach & Credential Leak Hunter"""
    
    def __init__(self, email):
        self.email = email.strip().lower()
        self.data = {
            "Target": self.email,
            "Total_Breaches": 0,
            "Breach_Sources": [],
            "Eksponerede_Data_Typer": set(),
            "Lækkede_Passwords_Fundet": False,
            "Database_Hits": {
                "HIBP": [],
                "XposedOrNot": [],
                "BreachDirectory": []
            },
            "Underground_Hits": {
                "Paste_Leaks": [],
                "GitHub_Dev_Leaks": [],
                "Telegram_Hacker_Dumps": [],
                "Cloud_Trello_Exposures": []
            },
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 85 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.BG_RED}{C.WHITE} {'='*80} {C.RESET}")
        print(f"{C.BG_RED}{C.WHITE} [03] BREACH & LEAK SYNDICATE HUNTER (GOLIATH V12) {'='*29} {C.RESET}")
        print(f"[*] Initierer massiv lækage-analyse for e-mail: {C.WHITE}{self.email}{C.RESET}\n")

        # 1. XposedOrNot API
        self._update_progress(10, "Forespørger globale hacker-databaser (XposedOrNot)")
        self._check_xposedornot()

        # 2. HaveIBeenPwned Live Scrape
        if driver:
            self._update_progress(30, "Infiltrerer HaveIBeenPwned Frontend (Stealth Mode)")
            self._scrape_hibp_frontend(driver)
        else:
            print(f"\n{C.RED}[!] Ingen browser-driver tilgængelig. Springer dyb HIBP-scanning over.{C.RESET}")

        # 3. BreachDirectory API
        self._update_progress(45, "Krydstjekker data mod BreachDirectory API")
        self._check_breach_directory()

        # 4. GitHub & GitLab Leaks
        if driver:
            self._update_progress(60, "Skanner GitHub/GitLab for Hardcodede Passwords")
            self._hunt_github_leaks(driver)

        # 5. Telegram & Dark-Forums
        if driver:
            self._update_progress(75, "Skanner Telegram (t.me) for russiske Combo-Dumps")
            self._hunt_telegram_dumps(driver)

        # 6. Cloud & Trello Boards
        if driver:
            self._update_progress(85, "Skanner åbne Trello-boards og Google Docs")
            self._hunt_cloud_trello(driver)

        # 7. Paste Sites
        if driver:
            self._update_progress(95, "Dorker Pastebin/Ghostbin for rå log-filer")
            self._dork_pastes(driver)

        sys.stdout.write("\r" + " " * 85 + "\r")
        print(f"{C.GREEN}[✓] Breach & Leak Analyse 100% fuldført.{C.RESET}")

        # Sammenfatning og gem
        self._summarize_results()
        self.save()

    def _check_xposedornot(self):
        """Tjekker XposedOrNot API for lynhurtige hits"""
        print(f"\n{C.YELLOW}    [*] XposedOrNot Intelligence:{C.RESET}")
        try:
            url = f"https://api.xposedornot.com/v1/checkbacklink?email={self.email}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                breaches = data.get("Breaches", [])
                for b in breaches:
                    name = b[0] if isinstance(b, list) else b
                    if name not in self.data["Database_Hits"]["XposedOrNot"]:
                        self.data["Database_Hits"]["XposedOrNot"].append(name)
                        self.data["Breach_Sources"].append(name)
                print(f"{C.GREEN}      ✓ XposedOrNot bekræfter {len(breaches)} lækager.{C.RESET}")
            elif res.status_code == 404:
                print(f"{C.DIM}      [-] E-mail ikke fundet i XposedOrNot databasen.{C.RESET}")
            else:
                print(f"{C.DIM}      [-] XposedOrNot returnerede ukendt status: {res.status_code}.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}      [!] Fejl ved kontakt til XposedOrNot: {e}{C.RESET}")

    def _scrape_hibp_frontend(self, driver):
        """V12: Stealth Scraping der fanger de allernyeste leaks som Internet Archive"""
        print(f"\n{C.YELLOW}    [*] HaveIBeenPwned Live Scraper:{C.RESET}")
        try:
            driver.get("https://haveibeenpwned.com/")
            time.sleep(3) # Tillad Cloudflare at validere os
            
            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "Account"))
                )
                search_box.clear()
                search_box.send_keys(self.email)
                search_box.send_keys(Keys.ENTER)
            except TimeoutException:
                print(f"{C.RED}      [!] Kunne ikke finde HIBP søgefelt (Cloudflare blokering mulig).{C.RESET}")
                return

            # Vent på at AJAX requestet henter resultaterne frem
            time.sleep(5) 
            source = driver.page_source
            
            if "pwnedCompanyTitle" in source or "Oh no — pwned!" in source:
                breach_elements = driver.find_elements(By.CSS_SELECTOR, ".pwnedCompanyTitle")
                count = 0
                for el in breach_elements:
                    breach_name = el.text.strip()
                    if breach_name and breach_name not in self.data["Breach_Sources"]:
                        self.data["Database_Hits"]["HIBP"].append(breach_name)
                        self.data["Breach_Sources"].append(breach_name)
                        print(f"{C.RED}      🔥 KRITISK LÆKAGE BEKRÆFTET LOKALT: {breach_name}{C.RESET}")
                        count += 1
                
                # Udtræk kompromitterede datatyper (Passwords, IP, etc)
                data_points = driver.find_elements(By.CSS_SELECTOR, ".dataClasses")
                for dp in data_points:
                    for tag in dp.text.split(','):
                        clean_tag = tag.strip()
                        self.data["Eksponerede_Data_Typer"].add(clean_tag)
                        if "password" in clean_tag.lower():
                            self.data["Lækkede_Passwords_Fundet"] = True
                            
                if count == 0:
                    print(f"{C.DIM}      [-] Fandt 'Pwned' markør, men kunne ikke parse firmanavne.{C.RESET}")
            else:
                print(f"{C.GREEN}      ✓ HaveIBeenPwned melder e-mailen ren for offentlige lækager.{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}      [-] Scraping afbrudt uventet: {e}{C.RESET}")

    def _check_breach_directory(self):
        """V12: Gendannet logik. Sender uofficielt request til deres free-tier."""
        print(f"\n{C.YELLOW}    [*] BreachDirectory Intelligence:{C.RESET}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
            url = f"https://breachdirectory.org/api/search?key=free&term={self.email}"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("found", 0) > 0:
                    sources = data.get("sources", [])
                    print(f"{C.RED}      🔥 BreachDirectory fandt {data.get('found')} kilder!{C.RESET}")
                    for src in sources:
                        name = src.get("name", "Ukendt")
                        if name not in self.data["Breach_Sources"]:
                            self.data["Database_Hits"]["BreachDirectory"].append(name)
                            self.data["Breach_Sources"].append(name)
                            print(f"{C.CYAN}        -> Kilde: {name}{C.RESET}")
                else:
                    print(f"{C.DIM}      [-] Ingen hits hos BreachDirectory.{C.RESET}")
            else:
                print(f"{C.DIM}      [-] BreachDirectory API afviste requestet (HTTP {res.status_code}).{C.RESET}")
        except Exception as e: 
            print(f"{C.DIM}      [-] Kunne ikke forbinde til BreachDirectory: {e}{C.RESET}")

    def _hunt_github_leaks(self, driver):
        """Søger efter e-mailen i kildekode for at finde hardcodede passwords/tokens"""
        print(f"\n{C.YELLOW}    [*] GitHub/GitLab Leak Scanner:{C.RESET}")
        dork = f'site:github.com OR site:gitlab.com "{self.email}" (password OR secret OR API_KEY OR token)'
        hits = omni_dork_search(driver, dork, max_links=4)
        if hits:
            print(f"{C.RED}      [!] ADVARSEL: Målets e-mail optræder i kildekode (Potentielt Hardcoded Credential)!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Hits"]["GitHub_Dev_Leaks"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen åbenlyse kode-leaks fundet.{C.RESET}")

    def _hunt_telegram_dumps(self, driver):
        """Jagt på russiske/underground Telegram combo-lister"""
        print(f"\n{C.YELLOW}    [*] Telegram Combo-Dump Scanner:{C.RESET}")
        dork = f'site:t.me "{self.email}" (combo OR dump OR leak OR password OR log)'
        hits = omni_dork_search(driver, dork, max_links=3)
        if hits:
            print(f"{C.RED}      🔥 KRITISK: E-mailen optræder i offentlige Telegram Hacker-grupper!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Hits"]["Telegram_Hacker_Dumps"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen Telegram hacker-spor fundet via søgemaskiner.{C.RESET}")

    def _hunt_cloud_trello(self, driver):
        """Tjekker fejlkonfigurerede Trello boards og Google Docs"""
        print(f"\n{C.YELLOW}    [*] Cloud Misconfiguration Scanner:{C.RESET}")
        dork = f'site:trello.com OR site:docs.google.com/document/d/ "{self.email}"'
        hits = omni_dork_search(driver, dork, max_links=3)
        if hits:
            print(f"{C.YELLOW}      [!] E-mail eksponeret i åbne Cloud/Trello dokumenter!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Hits"]["Cloud_Trello_Exposures"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen åbne Cloud/Trello eksponeringer fundet.{C.RESET}")

    def _dork_pastes(self, driver):
        """Søger efter e-mailen i rå paste-dumps"""
        print(f"\n{C.YELLOW}    [*] Pastebin/Raw Dump Scanner:{C.RESET}")
        dork = f'site:pastebin.com OR site:ghostbin.co OR site:paste.ee OR site:controlc.com "{self.email}"'
        hits = omni_dork_search(driver, dork, max_links=5)
        if hits:
            print(f"{C.RED}      [!] E-MAIL FUNDET I RÅ PASTE DUMPS (Sandsynlig Combo-liste):{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Hits"]["Paste_Leaks"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen Paste-lækager fundet via Google.{C.RESET}")

    def _summarize_results(self):
        # Rens og fjern dubletter på tværs af de 3 databaser
        unique_sources = set(self.data["Breach_Sources"])
        self.data["Total_Breaches"] = len(unique_sources)
        self.data["Breach_Sources"] = list(unique_sources)
        self.data["Eksponerede_Data_Typer"] = list(self.data["Eksponerede_Data_Typer"])
        
        print(f"\n{C.CYAN}--- [ GOLIATH V12: BREACH SUMMARY FOR {self.email} ] ---{C.RESET}")
        
        if self.data["Total_Breaches"] > 0:
            print(f"{C.BG_RED}{C.WHITE} !!! MÅLET ER EKSPONERET I {self.data['Total_Breaches']} VERIFICEREDE DATALÆKAGER !!! {C.RESET}")
            print(f"{C.MAGENTA}[+] Lækage-kilder: {', '.join(self.data['Breach_Sources'])}{C.RESET}")
            
            if self.data["Eksponerede_Data_Typer"]:
                print(f"{C.MAGENTA}[+] Kompromitterede Typer: {', '.join(self.data['Eksponerede_Data_Typer'])}{C.RESET}")
                
            if self.data["Lækkede_Passwords_Fundet"]:
                print(f"{C.RED}🔥 ALARM: Passwords er bekræftet lækket i et eller flere af disse breaches!{C.RESET}")
                print(f"{C.RED}   -> Kør Modul 17 (Sniper) eller Modul 18 (IMAP Ripper) for at udnytte dette.{C.RESET}")
        else:
            print(f"{C.GREEN}[✓] Ingen verificerede lækager fundet i de store databaser.{C.RESET}")

        # Opsummering af Underground Hits
        total_ug = sum(len(v) for v in self.data["Underground_Hits"].values())
        if total_ug > 0:
            print(f"\n{C.YELLOW}[!] Der blev fundet {total_ug} undergrunds/Cloud eksponeringer!{C.RESET}")
            print(f"{C.DIM}    Se den gemte JSON-rapport for direkte links.{C.RESET}")

    def save(self):
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        safe_email = self.email.replace("@", "_at_").replace(".", "_")
        filename = f"{session.get('loot_folder', 'loot_evidence')}/03_BREACH_{safe_email}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"\n{C.GREEN}[✓] Udvidet Breach-rapport gemt sikkert: {filename}{C.RESET}")