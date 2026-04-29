# -*- coding: utf-8 -*-
"""
PETFE GOLIATH V14: TACTICAL BREACH & SYNDICATE HUNTER
Operativ Specifikation:
- Asynchronous API Matrix (XposedOrNot, BreachDirectory, LeakCheck)
- HIBP REST API Integration (med Selenium Scrape fallback)
- Advanced Infostealer Log Dorking (RedLine, Raccoon, Vidar)
- Zero-Disk-Footprint: Operatør-styret arkivering
- Thread-Safe Clinical Logging
"""

import json
import os
import sys
import time
import requests
import re
import urllib.parse
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import http, omni_dork_search, CONFIG
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

class BreachIntelligenceAnalyst:
    
    def __init__(self, email):
        self.email = email.strip().lower()
        self.print_lock = threading.Lock()
        self.hibp_key = CONFIG.get("api_keys", {}).get("hibp_api_key", "")
        
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
                "Reddit_Dox_Mentions": [],
                "Infostealer_Logs": [] # NY V14
            },
            "Metadata": {
                "Timestamp": datetime.now().isoformat(),
                "Software": "GOLIATH V14 TACTICAL BREACH ENGINE"
            }
        }

    def _log(self, level, message):
        """Trådsikker og klinisk logning."""
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "CRITICAL": C.RED, "SUCCESS": C.GREEN}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} [{color}{level}{C.RESET}] {message}\n")

    def _update_progress(self, pct, message):
        with self.print_lock:
            sys.stdout.write("\r" + " " * 105 + "\r")
            sys.stdout.write(f"{C.MAGENTA}    [GOLIATH-V14] {message}... {C.BOLD}{pct}%{C.RESET}")
            sys.stdout.flush()

    def run(self, driver=None):
        print(f"\n{C.WHITE}{'='*80}{C.RESET}")
        print(f"{C.WHITE} MODULE 03: GLOBAL LEAK & SYNDICATE HUNTER (V14){C.RESET}")
        print(f"{C.WHITE}{'='*80}{C.RESET}")
        self._log("INFO", f"Initiating Breach Audit for: {self.email}")

        # --- FASE 1: ASYNKRON API MATRIX ---
        self._update_progress(10, "Executing Parallel API Intelligence Sweep")
        self._execute_async_apis()

        # --- FASE 2: HIBP RESOLUTION ---
        self._update_progress(30, "Resolving HaveIBeenPwned Intelligence")
        self._resolve_hibp(driver)

        # --- FASE 3: UNDERGROUND DORKING (Synkron pga. WebDriver krav) ---
        if driver:
            self._update_progress(45, "Sweeping Underground Hacker Forums")
            self._hunt_hacker_forums(driver)

            self._update_progress(55, "Scanning GitHub/GitLab for Hardcoded Secrets")
            self._hunt_github_leaks(driver)

            self._update_progress(65, "Intercepting Telegram Combo-Dumps")
            self._hunt_telegram_dumps(driver)
            
            self._update_progress(75, "Hunting Infostealer Malware Logs (RedLine/Raccoon)")
            self._hunt_stealer_logs(driver)

            self._update_progress(85, "Analyzing Cloud Misconfigurations (Trello/GDocs)")
            self._hunt_cloud_trello(driver)
            
            self._update_progress(90, "Scanning Reddit for Doxxing & Tech Support Exposures")
            self._hunt_reddit_exposures(driver)

            self._update_progress(95, "Mining Pastebin/Ghostbin for Raw Dumps")
            self._dork_pastes(driver)
        else:
            self._log("WARN", "Stealth Driver ikke tilknyttet. Underground Dorking suspenderet.")

        # --- FASE 4: OPSAMLING & KONTROL ---
        self._update_progress(100, "Audit Complete")
        self._summarize_results()
        self._handle_archiving()

        return self.data

    # =========================================================================
    # ASYNC API ENGINE
    # =========================================================================
    def _execute_async_apis(self):
        """Kører alle eksterne (gratis) APIs parallelt for at spare tid."""
        api_tasks = [
            self._check_xposedornot,
            self._check_breach_directory,
            self._check_leakcheck
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(task) for task in api_tasks]
            concurrent.futures.wait(futures)

    def _check_xposedornot(self):
        try:
            res = http.get(f"https://api.xposedornot.com/v1/checkbacklink?email={self.email}", timeout=10)
            if res.status_code == 200:
                breaches = res.json().get("Breaches", [])
                if breaches:
                    self._log("CRITICAL", f"XposedOrNot confirmed {len(breaches)} data breaches.")
                    for b in breaches:
                        name = b[0] if isinstance(b, list) else b
                        self.data["Verified_Databases"]["XposedOrNot"].append(name)
                        if name not in self.data["Breach_Sources"]:
                            self.data["Breach_Sources"].append(name)
        except Exception as e:
            self._log("ERROR", f"XposedOrNot connection failed: {e}")

    def _check_breach_directory(self):
        try:
            res = http.get(f"https://breachdirectory.org/api/search?key=free&term={self.email}", timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("found", 0) > 0:
                    self._log("CRITICAL", f"BreachDirectory flagged {data.get('found')} exposed sources.")
                    for src in data.get("sources", []):
                        name = src.get("name", "Unknown")
                        self.data["Verified_Databases"]["BreachDirectory"].append(name)
                        if name not in self.data["Breach_Sources"]:
                            self.data["Breach_Sources"].append(name)
        except Exception: pass

    def _check_leakcheck(self):
        try:
            res = http.get(f"https://leakcheck.io/api/public?check={self.email}", timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("found", 0) > 0:
                    self._log("CRITICAL", f"LeakCheck.io confirmed {data.get('found')} compromise points.")
                    self.data["Verified_Databases"]["LeakCheck"].append(f"LeakCheck ({data.get('found')} hits)")
                    if "LeakCheck.io (Ukendte kilder)" not in self.data["Breach_Sources"]:
                        self.data["Breach_Sources"].append("LeakCheck.io (Ukendte kilder)")
        except Exception: pass

    # =========================================================================
    # HIBP RESOLUTION (API First, Scraping Second)
    # =========================================================================
    def _resolve_hibp(self, driver):
        if self.hibp_key:
            self._log("INFO", "Valid HIBP API Key detected. Engaging native REST API.")
            self._query_hibp_api()
        elif driver:
            self._log("WARN", "No HIBP API Key. Attempting Stealth DOM Scrape (Cloudflare Risk).")
            self._scrape_hibp_frontend(driver)
        else:
            self._log("WARN", "No HIBP API Key and no WebDriver. HIBP audit bypassed.")

    def _query_hibp_api(self):
        headers = {
            "hibp-api-key": self.hibp_key,
            "user-agent": "PETFE-GOLIATH-OSINT"
        }
        try:
            res = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(self.email)}?truncateResponse=false", headers=headers, timeout=10)
            if res.status_code == 200:
                breaches = res.json()
                self._log("CRITICAL", f"HIBP API verified {len(breaches)} corporate breaches.")
                for b in breaches:
                    b_name = b.get("Name", "Unknown")
                    self.data["Verified_Databases"]["HIBP"].append(b_name)
                    if b_name not in self.data["Breach_Sources"]:
                        self.data["Breach_Sources"].append(b_name)
                    
                    for data_class in b.get("DataClasses", []):
                        self.data["Eksponerede_Data_Typer"].add(data_class)
                        if "password" in data_class.lower():
                            self.data["Lækkede_Passwords_Fundet"] = True
            elif res.status_code == 404:
                self._log("SUCCESS", "HIBP API reports no known corporate breaches.")
            elif res.status_code == 401:
                self._log("ERROR", "HIBP API Key is invalid or expired.")
        except Exception as e:
            self._log("ERROR", f"HIBP API Failure: {e}")

    def _scrape_hibp_frontend(self, driver):
        try:
            driver.get("https://haveibeenpwned.com/")
            time.sleep(3)
            
            try:
                search_box = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "Account")))
                search_box.clear()
                search_box.send_keys(self.email)
                search_box.send_keys(Keys.ENTER)
            except TimeoutException:
                self._log("ERROR", "HIBP Search field not found (Possible Cloudflare Block).")
                return

            time.sleep(5) 
            source = driver.page_source
            
            if "pwnedCompanyTitle" in source or "Oh no — pwned!" in source:
                breaches = driver.find_elements(By.CSS_SELECTOR, ".pwnedCompanyTitle")
                self._log("CRITICAL", f"HIBP Live-Scraper verified {len(breaches)} breaches.")
                for el in breaches:
                    b_name = el.text.strip()
                    if b_name and b_name not in self.data["Breach_Sources"]:
                        self.data["Verified_Databases"]["HIBP"].append(b_name)
                        self.data["Breach_Sources"].append(b_name)
                
                data_points = driver.find_elements(By.CSS_SELECTOR, ".dataClasses")
                for dp in data_points:
                    for tag in dp.text.split(','):
                        clean_tag = tag.strip()
                        self.data["Eksponerede_Data_Typer"].add(clean_tag)
                        if "password" in clean_tag.lower():
                            self.data["Lækkede_Passwords_Fundet"] = True
            elif "Good news" in source:
                self._log("SUCCESS", "HIBP Live-Scraper reports no breaches.")
        except Exception as e:
            self._log("ERROR", f"HIBP Scraper exception: {e}")

    # =========================================================================
    # UNDERGROUND DORKING MATRIX
    # =========================================================================
    def _execute_dork_hunt(self, driver, dork_query, category_name, list_ref):
        """Generisk metode til at udføre en dork og gemme URL'er trådsikkert."""
        hits = omni_dork_search(driver, dork_query, max_links=4)
        if hits:
            self._log("CRITICAL", f"Identified {len(hits)} exposure(s) in: {category_name}")
            for h in hits:
                url = h['url']
                if url not in list_ref:
                    list_ref.append(url)
                    print(f"{C.RED}      -> HIT: {url[:80]}{C.RESET}")

    def _hunt_hacker_forums(self, driver):
        forums = "site:breachforums.st OR site:cracked.io OR site:nulled.to OR site:hackforums.net OR site:exploit.in"
        self._execute_dork_hunt(driver, f'{forums} "{self.email}"', "Hacker Forums", self.data["Underground_Syndicates"]["Hacker_Forums"])

    def _hunt_github_leaks(self, driver):
        dork = f'site:github.com OR site:gitlab.com "{self.email}" (password OR secret OR API_KEY OR token)'
        self._execute_dork_hunt(driver, dork, "GitHub/GitLab (Hardcoded Secrets)", self.data["Underground_Syndicates"]["GitHub_GitLab_Dev"])

    def _hunt_telegram_dumps(self, driver):
        dork = f'site:t.me "{self.email}" (combo OR dump OR leak OR password OR log)'
        self._execute_dork_hunt(driver, dork, "Telegram Combo-Dumps", self.data["Underground_Syndicates"]["Telegram_Channels"])

    def _hunt_stealer_logs(self, driver):
        """NY V14: Specifik jagt på infostealer malware logs."""
        dork = f'"{self.email}" (RedLine OR Raccoon OR Vidar OR Stealer OR "URL: " "USER: " "PASS: ")'
        self._execute_dork_hunt(driver, dork, "Infostealer Malware Logs", self.data["Underground_Syndicates"]["Infostealer_Logs"])

    def _hunt_cloud_trello(self, driver):
        dork = f'site:trello.com OR site:docs.google.com/document/d/ "{self.email}"'
        self._execute_dork_hunt(driver, dork, "Cloud Misconfigurations", self.data["Underground_Syndicates"]["Cloud_Trello_Docs"])

    def _hunt_reddit_exposures(self, driver):
        dork = f'site:reddit.com "{self.email}"'
        self._execute_dork_hunt(driver, dork, "Reddit Mentions", self.data["Underground_Syndicates"]["Reddit_Dox_Mentions"])

    def _dork_pastes(self, driver):
        dork = f'site:pastebin.com OR site:ghostbin.co OR site:paste.ee "{self.email}"'
        self._execute_dork_hunt(driver, dork, "Raw Paste Dumps", self.data["Underground_Syndicates"]["Paste_Dumps"])

    # =========================================================================
    # OPSAMLING & ZERO-DISK ARKIVERING
    # =========================================================================
    def _summarize_results(self):
        unique_sources = list(set(self.data["Breach_Sources"]))
        self.data["Total_Verified_Breaches"] = len(unique_sources)
        self.data["Breach_Sources"] = unique_sources
        self.data["Eksponerede_Data_Typer"] = list(self.data["Eksponerede_Data_Typer"])
        
        total_ug = sum(len(v) for v in self.data["Underground_Syndicates"].values())
        self.data["Total_Underground_Hits"] = total_ug

        print(f"\n{C.WHITE}--- TACTICAL BREACH SUMMARY: {self.email} ---{C.RESET}")
        
        if self.data["Total_Verified_Breaches"] > 0:
            print(f"Verified Breaches: {C.RED}{self.data['Total_Verified_Breaches']} (Critical){C.RESET}")
            print(f"Exposed Vectors:   {C.YELLOW}{', '.join(self.data['Eksponerede_Data_Typer'])}{C.RESET}")
            if self.data["Lækkede_Passwords_Fundet"]:
                print(f"Password Status:   {C.RED}COMPROMISED (Cleartext or Hash exposed){C.RESET}")
        else:
            print(f"Verified Breaches: {C.GREEN}0 (Target appears clean in official records){C.RESET}")

        if total_ug > 0:
            print(f"Underground Hits:  {C.RED}{total_ug} (Forums, Pastes, Stealer Logs){C.RESET}")
            print(f"{C.DIM}* Underground exposures often contain fresh, unhashed credentials.{C.RESET}")
        
        print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")

    def _handle_archiving(self):
        """Operatør-styret zero-disk footprint arkivering."""
        choice = input(f"\n{C.YELLOW}[?] Archive Breach Intelligence report to disk? (y/n): {C.RESET}").strip().lower()
        if choice in ['y', 'j', 'yes', 'ja']:
            self.save()
        else:
            self._log("WARN", "Data purged from RAM. No footprints left.")

    def save(self):
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        safe_email = self.email.replace("@", "_at_").replace(".", "_")
        filename = f"{session.get('loot_folder', 'loot_evidence')}/03_BREACH_{safe_email}.json"
        
        if os.path.exists(filename):
            try: os.remove(filename)
            except Exception: pass
            
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        self._log("SUCCESS", f"Report securely archived: {filename}")

# Alias til bagudkompatibilitet
BreachIntelligenceAnalyst = BreachIntelligenceAnalyst