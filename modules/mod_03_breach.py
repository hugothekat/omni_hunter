# -*- coding: utf-8 -*-
import requests
import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from core.utils import C, session
from core.network import omni_dork_search, CONFIG

class BreachIntelligenceAnalyst:
    def __init__(self, email):
        self.email = email.strip()
        self.data = {
            "Email": self.email, 
            "Paste_Sites": [], 
            "Andre_Læk_Kilder": [],          
            "Telegram_Hits": [],             # NY V8 TILFØJELSE: Telegram Leaks
            "Eksponerede_Passwords": [],     
            "Data_Leaks": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[03] Breach Analyse (XposedOrNot & Credential Harvest V8)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        self._update_progress(10, "Forbinder til gratis OSINT API (XposedOrNot)")
        self._check_xposedornot()
        
        # NY V8 TILFØJELSE: Ekstra HIBP tjek via Frontend
        self._update_progress(20, "Bekræfter mod HaveIBeenPwned (Frontend)")
        self._check_hibp_frontend(driver)
        
        # HVIS DER ER LEAKS, GÅ DIREKTE PÅ AHMIA/TOR!
        if self.data["Data_Leaks"]:
            self._search_darkweb_for_leaks(self.data["Data_Leaks"])
            
        self._update_progress(40, "Søger i Cloud Leaks (GitHub, Trello, GDocs)")
        self._check_cloud_leaks(driver)

        # NY V8 TILFØJELSE: Scanner åbne hacker Telegram-grupper
        self._update_progress(50, "Scanner Telegram API for hacker-dumps")
        self._check_telegram_leaks()

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
                    
                snippet = link.get('snippet', '')
                self._extract_credentials_from_text(snippet, "Google Snippet")
        else:
            print(f"{C.DIM}    [-] Ingen Paste-lækager fundet via Google.{C.RESET}")

        if self.data["Paste_Sites"]:
            self._update_progress(90, "Udfører Deep Scrape for at høste Passwords")
            self._deep_scrape_pastes(driver)

        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"\n{C.GREEN}[✓] Breach-analyse 100% fuldført.{C.RESET}")
        
        if self.data["Eksponerede_Passwords"]:
            print(f"\n{C.RED}--- 🚨 KRITISKE CREDENTIALS FUNDET 🚨 ---{C.RESET}")
            for pwd in self.data["Eksponerede_Passwords"]:
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
                        print(f"{C.YELLOW}      -> Lækket i (XposedOrNot): {b}{C.RESET}")
                        if b not in self.data["Data_Leaks"]:
                            self.data["Data_Leaks"].append(b)
                    if len(breaches) > 10:
                        print(f"{C.DIM}      -> ... og {len(breaches)-10} mere.{C.RESET}")
            elif res.status_code == 404:
                print(f"{C.GREEN}    ✓ Ingen hits i XposedOrNot databasen.{C.RESET}")
            else:
                print(f"{C.DIM}    [-] API gav ukendt statuskode: {res.status_code}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [-] Forbindelsesfejl til XposedOrNot: {e}{C.RESET}")

    def _check_hibp_frontend(self, driver):
        """NY V8 TILFØJELSE: Frontend bypass tjek af HaveIBeenPwned (Kræver ingen API nøgle)"""
        print(f"\n{C.YELLOW}[*] Udfører Frontend Bypass-tjek på HaveIBeenPwned...{C.RESET}")
        if not driver: return
        
        # Vi dorker HIBP indirekte, da direkte opslag blockes uden API
        dork = f'site:haveibeenpwned.com "{self.email}"'
        links = omni_dork_search(driver, dork, max_links=2)
        if links:
            print(f"{C.RED}    [!] ADVARSEL: Muligt HIBP Index fundet!{C.RESET}")
            for l in links:
                print(f"{C.DIM}      -> {l['url']}{C.RESET}")
        else:
            print(f"{C.GREEN}    ✓ Ingen åbne HIBP indekseringer fundet på Google.{C.RESET}")

    def _search_darkweb_for_leaks(self, breaches):
        """Søger direkte efter specifikke leaks (f.eks Jefit) + e-mail på Ahmia (Tor)"""
        print(f"\n{C.YELLOW}[*] INITIERER DARKWEB LEAK-JAGT (Søger efter rå dumps for de fundne leaks)...{C.RESET}")
        req_session = requests.Session()
        
        ahmia_onion = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/"
        ahmia_clear = "https://ahmia.fi/search/"
        
        if CONFIG.get("use_tor_proxy"):
            print(f"{C.CYAN}    -> Ruter gennem TOR proxy for maksimal dækning...{C.RESET}")
            req_session.proxies = {
                'http': CONFIG.get("tor_proxy_url", "socks5h://127.0.0.1:9050"), 
                'https': CONFIG.get("tor_proxy_url", "socks5h://127.0.0.1:9050")
            }
            base_url = ahmia_onion
        else:
            base_url = ahmia_clear
            
        for leak in breaches[:3]: 
            query = f'"{leak}" AND "{self.email}" AND (password OR dump OR sql)'
            print(f"{C.DIM}    -> Graver i The Deep Web for: {query}{C.RESET}")
            
            search_url = f"{base_url}?q={requests.utils.quote(query)}"
            try:
                res = req_session.get(search_url, timeout=20)
                if "searchResultsItem" in res.text:
                    print(f"{C.RED}    🔥 DARKWEB HIT: Fandt mulige raw dumps for {leak}!{C.RESET}")
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for item in soup.find_all('li', class_='searchResultsItem')[:2]:
                        link_tag = item.find('cite')
                        if link_tag:
                            onion_link = link_tag.text.strip()
                            print(f"{C.CYAN}      -> Link: {onion_link}{C.RESET}")
                            self.data["Andre_Læk_Kilder"].append(onion_link)
                else:
                    print(f"{C.DIM}      [-] Ingen offentlige .onion dumps fundet for denne combo.{C.RESET}")
            except Exception as e:
                print(f"{C.DIM}      [-] Darkweb/Tor timeout eller fejl: {e}{C.RESET}")

    def _check_cloud_leaks(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking Cloud & Dev miljøer for fejlkonfigurationer...{C.RESET}")
        if not driver: return
        
        dork = f'(site:gist.github.com OR site:trello.com OR site:docs.google.com) "{self.email}"'
        links = omni_dork_search(driver, dork, max_links=3)
        
        if links:
            for link in links:
                print(f"{C.RED}    🔥 LÆK I CLOUD/DEV MILJØ: {link['url'][:80]}{C.RESET}")
                if link["url"] not in self.data["Andre_Læk_Kilder"]:
                    self.data["Andre_Læk_Kilder"].append(link["url"])
                self._extract_credentials_from_text(link.get('snippet', ''), "Cloud Snippet")
        else:
            print(f"{C.DIM}    [-] Ingen hits i Cloud/Dev miljøer.{C.RESET}")

    def _check_telegram_leaks(self):
        """NY V8 TILFØJELSE: Direkte API-kald mod Telegram Web via søgning for at finde dumps"""
        print(f"\n{C.YELLOW}[*] Tjekker Telegram (t.me) for hacker-groups via søgemaskiner...{C.RESET}")
        url = f"https://html.duckduckgo.com/html/?q=site:t.me {requests.utils.quote(self.email)} password"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            links = re.findall(r'href="([^"]+)"', res.text)
            clean_links = [urllib.parse.unquote(l.split('uddg=')[1].split('&')[0]) for l in links if 'uddg=' in l and 't.me' in l]
            
            if clean_links:
                print(f"{C.RED}    🔥 ADVARSEL: E-mail nævnt i åbne Telegram-grupper!{C.RESET}")
                for cl in clean_links[:3]:
                    print(f"{C.DIM}      -> {cl}{C.RESET}")
                    if cl not in self.data["Telegram_Hits"]:
                        self.data["Telegram_Hits"].append(cl)
            else:
                print(f"{C.DIM}    [-] Ingen hits på Telegram.{C.RESET}")
        except Exception:
            pass

    def _deep_scrape_pastes(self, driver):
        print(f"\n{C.YELLOW}[*] Credential Harvest: Scraper Paste-sites for rå passwords...{C.RESET}")
        if not driver: return
        
        for url in self.data["Paste_Sites"][:3]: 
            print(f"{C.DIM}    -> Åbner Paste: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(2)
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
        # NY V8 TILFØJELSE: Regex tager nu både :, ; og | som separator!
        safe_email = re.escape(self.email)
        pattern = re.compile(rf'{safe_email}[:;\|]([^\s<>"\'/]+)')
        matches = pattern.findall(text)
        
        for pwd in matches:
            if pwd.lower() not in ["http", "https"] and len(pwd) > 3:
                if pwd not in self.data["Eksponerede_Passwords"]:
                    self.data["Eksponerede_Passwords"].append(pwd)
                    print(f"{C.MAGENTA}      ✓ Credential udtræk lykkedes fra {source}!{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/03_BREACH_{self.email.replace('@', '_at_')}.json"
        
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")