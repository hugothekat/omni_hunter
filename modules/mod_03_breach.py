# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import requests
import re
import urllib.parse
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
    """PETFE GOLIATH V13 - Global Leak & Syndicate Hunter (No-Nerf Edition)"""
    
    def __init__(self, email):
        self.email = email.strip().lower()
        self.data = {
            "Target": self.email,
            "Total_Verified_Breaches": 0,
            "Total_Underground_Hits": 0,
            "Breach_Sources": [],
            "Eksponerede_Data_Typer": set(),
            "Lækkede_Passwords_Fundet": False,
            "Verified_Databases": {
                "HIBP": [],
                "XposedOrNot": [],
                "BreachDirectory": [],
                "LeakCheck": []
            },
            "Underground_Syndicates": {
                "Hacker_Forums": [],
                "Paste_Dumps": [],
                "GitHub_GitLab_Dev": [],
                "Telegram_Channels": [],
                "Cloud_Trello_Docs": [],
                "Reddit_Dox_Mentions": []
            },
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        """Klippestabil progress bar der rydder linjen"""
        sys.stdout.write("\r" + " " * 95 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.BG_RED}{C.WHITE} {'='*85} {C.RESET}")
        print(f"{C.BG_RED}{C.WHITE} [03] GLOBAL LEAK & SYNDICATE HUNTER (GOLIATH V13) {'='*32} {C.RESET}")
        print(f"[*] Initierer dybdegående lækage-analyse for: {C.WHITE}{self.email}{C.RESET}\n")

        # --- FASE 1: OFFICIELLE DATABASER ---
        self._update_progress(5, "Forespørger XposedOrNot (Globale Databaser)")
        self._check_xposedornot()

        self._update_progress(15, "Forespørger BreachDirectory (Gratis API)")
        self._check_breach_directory()

        self._update_progress(25, "Scanner LeakCheck.io (Russiske/Alternative Leaks)")
        self._check_leakcheck()

        if driver:
            self._update_progress(35, "Infiltrerer HaveIBeenPwned Frontend (Stealth Omgåelse)")
            self._scrape_hibp_frontend(driver)
        else:
            print(f"\n{C.RED}[!] Ingen browser-driver. Springer HIBP Live-Scrape over.{C.RESET}")

        # --- FASE 2: UNDERGROUND & DEEP WEB DORKING ---
        if driver:
            self._update_progress(50, "Scanner lukkede Hacker-Fora (BreachForums, Nulled, etc)")
            self._hunt_hacker_forums(driver)

            self._update_progress(60, "Scanner GitHub/GitLab for Hardcodede Passwords")
            self._hunt_github_leaks(driver)

            self._update_progress(70, "Scanner Telegram (t.me) for russiske Combo-Dumps")
            self._hunt_telegram_dumps(driver)

            self._update_progress(80, "Scanner åbne Trello-boards og Google Docs")
            self._hunt_cloud_trello(driver)
            
            self._update_progress(85, "Scanner Reddit for Doxxing eller Hacking Requests")
            self._hunt_reddit_exposures(driver)

            self._update_progress(95, "Dorker Pastebin/Ghostbin for rå log-filer")
            self._dork_pastes(driver)

        sys.stdout.write("\r" + " " * 95 + "\r")
        print(f"{C.GREEN}[✓] Breach & Leak Analyse 100% fuldført.{C.RESET}")

        self._summarize_results()
        self.save()

    def _check_xposedornot(self):
        print(f"\n{C.YELLOW}    [*] XposedOrNot Intelligence:{C.RESET}")
        try:
            url = f"https://api.xposedornot.com/v1/checkbacklink?email={self.email}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                breaches = data.get("Breaches", [])
                for b in breaches:
                    name = b[0] if isinstance(b, list) else b
                    if name not in self.data["Verified_Databases"]["XposedOrNot"]:
                        self.data["Verified_Databases"]["XposedOrNot"].append(name)
                        self.data["Breach_Sources"].append(name)
                print(f"{C.GREEN}      ✓ XposedOrNot bekræfter {len(breaches)} lækager.{C.RESET}")
            else:
                print(f"{C.DIM}      [-] E-mail ikke fundet i XposedOrNot databasen.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}      [!] Fejl ved kontakt til XposedOrNot: {e}{C.RESET}")

    def _check_breach_directory(self):
        print(f"\n{C.YELLOW}    [*] BreachDirectory Intelligence:{C.RESET}")
        try:
            headers = {"User-Agent": "PETFE GOLIATH OSINT Engine"}
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
                            self.data["Verified_Databases"]["BreachDirectory"].append(name)
                            self.data["Breach_Sources"].append(name)
                            print(f"{C.CYAN}        -> Kilde: {name}{C.RESET}")
                else:
                    print(f"{C.DIM}      [-] Ingen hits hos BreachDirectory.{C.RESET}")
            else:
                print(f"{C.DIM}      [-] BreachDirectory API afviste requestet (HTTP {res.status_code}).{C.RESET}")
        except Exception as e: 
            print(f"{C.DIM}      [-] Kunne ikke forbinde til BreachDirectory: {e}{C.RESET}")

    def _check_leakcheck(self):
        """Uofficielt tjek op mod LeakCheck's offentlige systemer (Ofte gode til russiske leaks)"""
        print(f"\n{C.YELLOW}    [*] LeakCheck.io Intelligence:{C.RESET}")
        try:
            # Sender et simpelt request til deres public API for at se om der er et match
            url = f"https://leakcheck.io/api/public?check={self.email}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("found", 0) > 0:
                    print(f"{C.RED}      🔥 LeakCheck bekræfter {data.get('found')} kompromitteringer!{C.RESET}")
                    self.data["Verified_Databases"]["LeakCheck"].append(f"LeakCheck ({data.get('found')} hits)")
                    self.data["Breach_Sources"].append("LeakCheck.io (Ukendte kilder)")
                else:
                    print(f"{C.DIM}      [-] Ingen offentlige hits hos LeakCheck.{C.RESET}")
            else:
                print(f"{C.DIM}      [-] LeakCheck API ikke tilgængelig pt.{C.RESET}")
        except:
            print(f"{C.DIM}      [-] Kunne ikke forbinde til LeakCheck.{C.RESET}")

    def _scrape_hibp_frontend(self, driver):
        print(f"\n{C.YELLOW}    [*] HaveIBeenPwned Live Scraper:{C.RESET}")
        try:
            driver.get("https://haveibeenpwned.com/")
            time.sleep(3)
            
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

            time.sleep(5) 
            source = driver.page_source
            
            if "pwnedCompanyTitle" in source or "Oh no — pwned!" in source:
                breach_elements = driver.find_elements(By.CSS_SELECTOR, ".pwnedCompanyTitle")
                count = 0
                for el in breach_elements:
                    breach_name = el.text.strip()
                    if breach_name and breach_name not in self.data["Breach_Sources"]:
                        self.data["Verified_Databases"]["HIBP"].append(breach_name)
                        self.data["Breach_Sources"].append(breach_name)
                        print(f"{C.RED}      🔥 KRITISK LÆKAGE BEKRÆFTET LOKALT: {breach_name}{C.RESET}")
                        count += 1
                
                data_points = driver.find_elements(By.CSS_SELECTOR, ".dataClasses")
                for dp in data_points:
                    for tag in dp.text.split(','):
                        clean_tag = tag.strip()
                        self.data["Eksponerede_Data_Typer"].add(clean_tag)
                        if "password" in clean_tag.lower():
                            self.data["Lækkede_Passwords_Fundet"] = True
            else:
                print(f"{C.GREEN}      ✓ HaveIBeenPwned melder e-mailen ren for offentlige lækager.{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}      [-] Scraping afbrudt uventet: {e}{C.RESET}")

    def _hunt_hacker_forums(self, driver):
        """Ny V13: Specifik jagt på de største undergrundsfora"""
        print(f"\n{C.YELLOW}    [*] Hacker Forums & Black Hat Sites:{C.RESET}")
        forums = "site:breachforums.st OR site:cracked.io OR site:nulled.to OR site:hackforums.net OR site:exploit.in"
        dork = f'{forums} "{self.email}"'
        hits = omni_dork_search(driver, dork, max_links=4)
        if hits:
            print(f"{C.RED}      🔥 FATALT: Målet er nævnt direkte på Black Hat / Hacker Fora!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Syndicates"]["Hacker_Forums"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen åbenlyse hits på undergrundsfora.{C.RESET}")

    def _hunt_github_leaks(self, driver):
        print(f"\n{C.YELLOW}    [*] GitHub/GitLab Leak Scanner:{C.RESET}")
        dork = f'site:github.com OR site:gitlab.com OR site:bitbucket.org "{self.email}" (password OR secret OR API_KEY OR token)'
        hits = omni_dork_search(driver, dork, max_links=4)
        if hits:
            print(f"{C.RED}      [!] ADVARSEL: Målets e-mail optræder i kildekode (Potentielt Hardcoded Credential)!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Syndicates"]["GitHub_GitLab_Dev"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen åbenlyse kode-leaks fundet.{C.RESET}")

    def _hunt_telegram_dumps(self, driver):
        print(f"\n{C.YELLOW}    [*] Telegram Combo-Dump Scanner:{C.RESET}")
        dork = f'site:t.me "{self.email}" (combo OR dump OR leak OR password OR log OR stealer)'
        hits = omni_dork_search(driver, dork, max_links=4)
        if hits:
            print(f"{C.RED}      🔥 KRITISK: E-mailen optræder i offentlige Telegram Hacker-grupper/Stealer Logs!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Syndicates"]["Telegram_Channels"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen Telegram hacker-spor fundet via søgemaskiner.{C.RESET}")

    def _hunt_cloud_trello(self, driver):
        print(f"\n{C.YELLOW}    [*] Cloud Misconfiguration Scanner:{C.RESET}")
        dork = f'site:trello.com OR site:docs.google.com/document/d/ "{self.email}"'
        hits = omni_dork_search(driver, dork, max_links=3)
        if hits:
            print(f"{C.YELLOW}      [!] E-mail eksponeret i åbne Cloud/Trello dokumenter!{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Syndicates"]["Cloud_Trello_Docs"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen åbne Cloud/Trello eksponeringer fundet.{C.RESET}")

    def _hunt_reddit_exposures(self, driver):
        """Ny V13: Finder ud af om brugeren er doxet, eller selv har postet dumme ting"""
        print(f"\n{C.YELLOW}    [*] Reddit Exposure & Doxxing Scanner:{C.RESET}")
        dork = f'site:reddit.com "{self.email}"'
        hits = omni_dork_search(driver, dork, max_links=3)
        if hits:
            print(f"{C.YELLOW}      [!] Målet er nævnt på Reddit (Tjek for Doxxing eller Tech-support posts){C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Syndicates"]["Reddit_Dox_Mentions"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen Reddit mentions fundet.{C.RESET}")

    def _dork_pastes(self, driver):
        print(f"\n{C.YELLOW}    [*] Pastebin/Raw Dump Scanner:{C.RESET}")
        dork = f'site:pastebin.com OR site:ghostbin.co OR site:paste.ee OR site:controlc.com "{self.email}"'
        hits = omni_dork_search(driver, dork, max_links=5)
        if hits:
            print(f"{C.RED}      [!] E-MAIL FUNDET I RÅ PASTE DUMPS (Sandsynlig Combo-liste):{C.RESET}")
            for h in hits:
                print(f"        -> {h['url']}")
                self.data["Underground_Syndicates"]["Paste_Dumps"].append(h['url'])
        else:
            print(f"{C.DIM}      [-] Ingen Paste-lækager fundet via Google.{C.RESET}")

    def _summarize_results(self):
        unique_sources = set(self.data["Breach_Sources"])
        self.data["Total_Verified_Breaches"] = len(unique_sources)
        self.data["Breach_Sources"] = list(unique_sources)
        self.data["Eksponerede_Data_Typer"] = list(self.data["Eksponerede_Data_Typer"])
        
        # Tæl alle undergrunds hits sammen
        total_ug = sum(len(v) for v in self.data["Underground_Syndicates"].values())
        self.data["Total_Underground_Hits"] = total_ug

        print(f"\n{C.CYAN}--- [ GOLIATH V13: INTELLIGENCE SUMMARY FOR {self.email} ] ---{C.RESET}")
        
        if self.data["Total_Verified_Breaches"] > 0:
            print(f"{C.BG_RED}{C.WHITE} !!! MÅLET ER EKSPONERET I {self.data['Total_Verified_Breaches']} VERIFICEREDE DATALÆKAGER !!! {C.RESET}")
            print(f"{C.MAGENTA}[+] Lækage-kilder: {', '.join(self.data['Breach_Sources'])}{C.RESET}")
            
            if self.data["Eksponerede_Data_Typer"]:
                print(f"{C.MAGENTA}[+] Kompromitterede Typer: {', '.join(self.data['Eksponerede_Data_Typer'])}{C.RESET}")
                
            if self.data["Lækkede_Passwords_Fundet"]:
                print(f"{C.RED}🔥 ALARM: Passwords er bekræftet lækket i et eller flere af disse breaches!{C.RESET}")
                print(f"{C.RED}   -> Kør Modul 17 (Sniper) eller Modul 18 (IMAP Ripper) for at udnytte dette.{C.RESET}")
        else:
            print(f"{C.GREEN}[✓] Ingen verificerede lækager fundet i de officielle databaser.{C.RESET}")

        if total_ug > 0:
            print(f"\n{C.YELLOW}[!] Der blev fundet {total_ug} undergrunds/Cloud eksponeringer! (Hacker fora, Pastebins, GitHub){C.RESET}")
            print(f"{C.DIM}    Dette er ofte mere kritisk end gamle HIBP leaks. Tjek den gemte JSON-rapport for direkte links.{C.RESET}")

    def save(self):
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        safe_email = self.email.replace("@", "_at_").replace(".", "_")
        filename = f"{session.get('loot_folder', 'loot_evidence')}/03_BREACH_{safe_email}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"\n{C.GREEN}[✓] V13 Breach-rapport gemt sikkert: {filename}{C.RESET}")