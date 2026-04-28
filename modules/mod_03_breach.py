# -*- coding: utf-8 -*-
import requests
import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By

from core.utils import C, session
from core.network import omni_dork_search

class BreachIntelligenceAnalyst:
    def __init__(self, email):
        self.email = email.strip()
        self.data = {
            "Email": self.email, 
            "Paste_Sites": [], 
            "Andre_Læk_Kilder": [],          # NY V7: GitHub, Trello, GDocs
            "Eksponerede_Passwords": [],     # NY V7: Opsamlede passwords
            "Data_Leaks": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[03] Breach Analyse (XposedOrNot & Credential Harvest V7)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        self._update_progress(20, "Forbinder til gratis OSINT API")
        self._check_xposedornot()
        
        self._update_progress(50, "Søger i Cloud Leaks (GitHub, Trello, GDocs)")
        self._check_cloud_leaks(driver)

        self._update_progress(70, "Bygger massiv Paste-Dork")
        print(f"\n{C.YELLOW}[*] Udfører High-Speed Dorking mod Paste-sites...{C.RESET}")
        
        sites = ["pastebin.com", "throwbin.io", "ghostbin.co", "rentry.co", "controlc.com", "justpaste.it"]
        sites_query = " OR ".join([f"site:{site}" for site in sites])
        dork = f'({sites_query}) "{self.email}"'
        
        links = omni_dork_search(driver, dork, max_links=5)
        
        sys.stdout.write("\r" + " " * 80 + "\r")
        if links:
            for link in links:
                print(f"{C.GREEN}    🔥 PASTE FUNDET: {link['url'][:80]}{C.RESET}")
                if link["url"] not in self.data["Paste_Sites"]:
                    self.data["Paste_Sites"].append(link["url"])
                    
                # NY V7: Tjek snippet for direkte lækkede adgangskoder
                snippet = link.get('snippet', '')
                self._extract_credentials_from_text(snippet, "Google Snippet")
        else:
            print(f"{C.DIM}    [-] Ingen Paste-lækager fundet via Google.{C.RESET}")

        # NY V7: Gå ind på paste-sites og stjæl passwords direkte
        if self.data["Paste_Sites"]:
            self._update_progress(90, "Udfører Deep Scrape for at høste Passwords")
            self._deep_scrape_pastes(driver)

        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"\n{C.GREEN}[✓] Breach-analyse 100% fuldført.{C.RESET}")
        
        # --- V7: OPSUMMERING AF PASSWORDS ---
        if self.data["Eksponerede_Passwords"]:
            print(f"\n{C.RED}--- 🚨 KRITISKE CREDENTIALS FUNDET 🚨 ---{C.RESET}")
            for pwd in self.data["Eksponerede_Passwords"]:
                # Vi maskerer passwordet lidt for OPSEC (f.eks. Pas***123)
                masked_pwd = pwd[:3] + "*" * (len(pwd)-5) + pwd[-2:] if len(pwd) > 5 else "***"
                print(f"{C.RED}    [!] Muligt Password Lækket: {masked_pwd}{C.RESET}")
            print(f"{C.YELLOW}    (Fulde passwords er gemt i JSON-rapporten){C.RESET}")

        self.save()

    def _check_xposedornot(self):
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.YELLOW}[*] Slår op i globale Hacker-databaser (XposedOrNot API)...{C.RESET}")
        
        url = f"https://api.xposedornot.com/v1/check-email/{self.email}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                breaches = data.get("breaches", [])
                if breaches:
                    print(f"{C.RED}    🔥 KRITISK: Emailen findes i {len(breaches)} datalæk!{C.RESET}")
                    for b in breaches[:10]:
                        print(f"{C.YELLOW}      -> Lækket i: {b}{C.RESET}")
                        self.data["Data_Leaks"].append(b)
                    if len(breaches) > 10:
                        print(f"{C.DIM}      -> ... og {len(breaches)-10} mere.{C.RESET}")
            elif res.status_code == 404:
                print(f"{C.GREEN}    ✓ Ingen hits i databasen (Emailen er ikke fundet i kendte læk).{C.RESET}")
            else:
                print(f"{C.DIM}    [-] API gav ukendt statuskode: {res.status_code}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [-] Forbindelsesfejl til XposedOrNot: {e}{C.RESET}")

    def _check_cloud_leaks(self, driver):
        """NY V7: Scanner GitHub Gists, Trello og Google Docs for e-mailen"""
        print(f"\n{C.YELLOW}[*] Dorking Cloud & Dev miljøer for fejlkonfigurationer...{C.RESET}")
        if not driver: return
        
        dork = f'(site:gist.github.com OR site:trello.com OR site:docs.google.com) "{self.email}"'
        links = omni_dork_search(driver, dork, max_links=3)
        
        if links:
            for link in links:
                print(f"{C.RED}    🔥 LÆK I CLOUD/DEV MILJØ: {link['url'][:80]}{C.RESET}")
                if link["url"] not in self.data["Andre_Læk_Kilder"]:
                    self.data["Andre_Læk_Kilder"].append(link["url"])
                # Træk evt. kodeord fra snippet
                self._extract_credentials_from_text(link.get('snippet', ''), "Cloud Snippet")
        else:
            print(f"{C.DIM}    [-] Ingen hits i Cloud/Dev miljøer.{C.RESET}")

    def _deep_scrape_pastes(self, driver):
        """NY V7: Besøger paste-sites fysisk for at regex-trække passwords ud"""
        print(f"\n{C.YELLOW}[*] Credential Harvest: Scraper Paste-sites for rå passwords...{C.RESET}")
        if not driver: return
        
        for url in self.data["Paste_Sites"][:3]: # Vi tager kun de top 3 for hastighed
            print(f"{C.DIM}    -> Åbner Paste: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(2)
                
                # Cookie Clicker for Paste sites
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["agree", "accept", "got it", "tillad"]):
                            btn.click(); time.sleep(1); break
                except: pass
                
                page_text = driver.find_element(By.TAG_NAME, "body").text
                self._extract_credentials_from_text(page_text, url)
                
            except Exception as e:
                print(f"{C.DIM}    [-] Fejl ved deep-scrape af {url}: {e}{C.RESET}")

    def _extract_credentials_from_text(self, text, source):
        """NY V7: Regex for at finde email:password format i en given tekst"""
        # Beskytter punktummer osv. i emailen
        safe_email = re.escape(self.email)
        # Leder efter formatet target@email.com:Password123 eller target@email.com;Password123
        pattern = re.compile(rf'{safe_email}[:;]([^\s<>"\'/]+)')
        matches = pattern.findall(text)
        
        for pwd in matches:
            # Fjern evt standard falske negativer som 'http'
            if pwd.lower() not in ["http", "https"] and len(pwd) > 3:
                if pwd not in self.data["Eksponerede_Passwords"]:
                    self.data["Eksponerede_Passwords"].append(pwd)
                    print(f"{C.MAGENTA}      ✓ Credential udtræk lykkedes fra {source}!{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/03_BREACH_{self.email.replace('@', '_at_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")