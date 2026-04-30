# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
import re
import time
import sys
import asyncio
import aiohttp
import threading
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By 

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake
from core.network import omni_dork_search, safe_get_with_retry

class TelecomIntelligenceEngine(BaseModule):
    """THE APEX TELECOM ENGINE (GOLIATH V39) - Fletter Modul 07 og 12"""
    def __init__(self, phone):
        super().__init__()
        self.name = "TELECOM INTELLIGENCE ENGINE"
        self.description = "Asynkron analyse via Krak, TrueCaller, MobilePay, Telegram & Dorking."
        self.category = ModuleCategory.PERSON
        self.print_lock = threading.Lock()
        
        self.raw_phone = str(phone)
        self.phone = self.raw_phone.replace(" ", "").replace("+45", "").replace("-", "")
        
        self.data = {
            "Nummer": f"+45 {self.phone}",
            "Identitet": {
                "Navn": "Ukendt",
                "Adresse": "Ukendt"
            },
            "Web_Spor": [],
            "Social_Spor": [],
            "Direct_App_Links": [],
            "Deep_Scrape_Mål": {
                "Emails": [],
                "CVR": []
            },
            "Timestamp": datetime.now().isoformat()
        }

    def _log(self, message: str, color: str = C.CYAN, indent: int = 0):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "  " * indent
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {prefix}{color}{message}{C.RESET}\n")

    def _generate_app_links(self):
        self._log("Genererer direkte API-links til Messaging OSINT...", C.YELLOW, indent=1)
        wa_link = f"https://wa.me/45{self.phone}"
        tg_link = f"https://t.me/+45{self.phone}"
        vi_link = f"viber://add?number=45{self.phone}"
        sig_link = f"https://signal.me/#p/+45{self.phone}"
        
        self.data["Direct_App_Links"] = [
            {"App": "WhatsApp", "URL": wa_link},
            {"App": "Telegram", "URL": tg_link},
            {"App": "Viber", "URL": vi_link},
            {"App": "Signal", "URL": sig_link}
        ]
        self._log(f"WhatsApp: {wa_link} (Brug til at tjekke profilbillede)", C.CYAN, indent=2)
        
    async def _async_caller_id(self):
        url = f"https://www.krak.dk/search?searchQuery={self.phone}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        name_elem = soup.select_one('.item-title, h2 a, h3 a')
                        if name_elem:
                            self.data["Identitet"]["Navn"] = name_elem.get_text(strip=True)
                            self._log(f"Krak Caller-ID Confirmed: {self.data['Identitet']['Navn']}", C.GREEN, indent=2)
                        
                        addr_elem = soup.select_one('.address')
                        if addr_elem:
                            self.data["Identitet"]["Adresse"] = addr_elem.get_text(strip=True)
                            self._log(f"Krak Residency Confirmed: {self.data['Identitet']['Adresse']}", C.GREEN, indent=2)
            except Exception as e:
                self._log(f"Krak Native API Timeout/Fejl: {e}", C.DIM, indent=2)

    def _execute_dorks(self, driver):
        formats = [
            f'"{self.phone}"',
            f'"{self.phone[:2]} {self.phone[2:4]} {self.phone[4:6]} {self.phone[6:8]}"',
            f'"{self.phone[:2]}-{self.phone[2:4]}-{self.phone[4:6]}-{self.phone[6:8]}"',
            f'"+45 {self.phone}"'
        ]
        combined_dork = " OR ".join(formats)
        
        # Generel Web-Dorking
        links = omni_dork_search(driver, combined_dork, max_links=10)
        if links:
            for link in links:
                href = link["url"]
                if "krak.dk" not in href and "degulesider.dk" not in href and "118.dk" not in href:
                    self._log(f"WEB SPOR: {href[:80]}", C.GREEN, indent=2)
                    if href not in self.data["Web_Spor"]:
                        self.data["Web_Spor"].append(href)
        else:
            self._log("Ingen offentlige web-spor fundet udover standard registre.", C.DIM, indent=2)

        # FUSION FRA MOD_12: MobilePay, TrueCaller & Social Media
        self._log("Cross-Referencing: MobilePay, TrueCaller, Facebook, Instagram...", C.MAGENTA, indent=1)
        soc_dork = f'(site:facebook.com OR site:instagram.com OR site:linkedin.com OR site:truecaller.com OR site:sync.me) "{self.phone}" OR "+45 {self.phone}" OR "MobilePay"'
        soc_links = omni_dork_search(driver, soc_dork, max_links=5)
        
        if soc_links:
            for link in soc_links:
                self._log(f"SYNDICATE HIT: {link['url'][:80]}", C.GREEN, indent=2)
                if link['url'] not in self.data["Social_Spor"]:
                    self.data["Social_Spor"].append(link['url'])
        else:
            self._log("Ingen åbenlyse hits på sociale medier eller MobilePay.", C.DIM, indent=2)

    def _deep_scrape_links(self, driver):
        if not driver or not self.data["Web_Spor"]: return
        for url in self.data["Web_Spor"][:4]:
            self._log(f"Åbner: {url}", C.DIM, indent=2)
            try:
                driver.get(url)
                time.sleep(3)
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["accept", "tillad", "godkend", "ok"]):
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1); break
                except: pass

                page_text = driver.find_element(By.TAG_NAME, "body").text
                cvr_matches = re.findall(r'\b(?:CVR|cvr)[\s:-]*(\d{8})\b', page_text)
                for cvr in set(cvr_matches):
                    if cvr not in self.data["Deep_Scrape_Mål"]["CVR"]:
                        self.data["Deep_Scrape_Mål"]["CVR"].append(cvr)
                        self._log(f"Tilknyttet CVR fundet: {cvr}", C.MAGENTA, indent=3)

                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', page_text)
                for em in set(emails):
                    clean_em = em.lower()
                    if clean_em not in self.data["Deep_Scrape_Mål"]["Emails"] and not any(ext in clean_em for ext in [".png", ".jpg", "sentry"]):
                        self.data["Deep_Scrape_Mål"]["Emails"].append(clean_em)
                        self._log(f"Tilknyttet Email fundet: {clean_em}", C.CYAN, indent=3)
            except Exception:
                self._log(f"Kunne ikke deep-scrape {url}", C.DIM, indent=3)

    def run(self, driver=None, target: str = "") -> dict:
        if target:
            self.raw_phone = target
            self.phone = str(target).replace(" ", "").replace("+45", "").replace("-", "")
            self.data["Nummer"] = f"+45 {self.phone}"

        print(f"\n{C.BG_RED}{C.WHITE} === THE TELECOM INTELLIGENCE ENGINE (GOLIATH V39) === {C.RESET}\n")
        self._log(f"Initiating Global Telecom Matrix for: +45 {self.phone}", C.YELLOW)

        self._log("FASE 1: Executing Async Caller-ID Resolution (Krak/118)...", C.CYAN)
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running(): loop.run_until_complete(self._async_caller_id())
        except Exception as e:
            self._log(f"Async Caller ID failed: {e}", C.RED, indent=1)

        self._generate_app_links()
        
        self._log("FASE 2: Deploying Multi-Format Omni-Dorks & Syndicate Sync...", C.CYAN)
        self._execute_dorks(driver)
        
        self._log("FASE 3: Deep-Scraping identified infrastructure...", C.CYAN)
        self._deep_scrape_links(driver)

        self._log("Telecom-efterretning 100% færdig.", C.GREEN)
        self.save()
        return self.data

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/07_PHONE_{self.phone}.json"
        
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass
            
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        datalake.ingest(self.name, self.phone, self.data)
        self._log(f"Rapport gemt sikkert: {filename}", C.GREEN)

# Aliaser til bagudkompatibilitet (Omni-Pivot)
PhoneIntelligenceHunter = TelecomIntelligenceEngine
PhoneIntelligenceAnalyst = TelecomIntelligenceEngine