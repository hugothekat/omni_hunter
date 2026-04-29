# -*- coding: utf-8 -*-
import sys
import time
import json
import os
import re
import urllib.parse
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, extract_danish_phones, validate_danish_address, datalake
from core.network import safe_get_with_retry, omni_dork_search

class EnhancedDirectoryIntelligenceHunter(BaseModule):
    """Advanced Danish property and person intelligence gathering with:
    - Parallel processing
    - Comprehensive error handling
    - Multiple data sources
    - Async I/O
    - Caching
    - Enhanced output formats
    """

    MAX_WORKERS = 5
    REQUEST_TIMEOUT = 30
    RATE_LIMIT_DELAY = 1.5

    def __init__(self, name: str, city: str = "") -> None:
        super().__init__()
        self.name_module = "NATIONAL DIRECTORY MATRIX" # Bruger name_module for at undgå at overskrive den personlige self.name
        self.description = "Dybdegående asynkron opslag i Krak, DinGeo, 118 og CVR for fuld personprofilering."
        self.category = ModuleCategory.PERSON
        
        self.name = name.strip()
        self.city = city.strip()
        self.start_time = datetime.now()
        self.rate_limited = False

        self.data = {
            "Identitet": self.name,
            "Lokation": self.city,
            "Telefonnumre": set(),
            "Ejendom": {
                "Vej": "",
                "Post": "",
                "By": "",
                "Type": "Ukendt",
                "Koordinater": "",
                "Historik": [],
                "Arealdata": {}
            },
            "DinGeo_Intelligence": {
                "BBR_Stamdata": {},
                "Vurdering": {},
                "Skat": {},
                "Dokumenter": {},
                "Infrastruktur": {},
                "Miljø_Risici": {},
                "Nabolag_Profil": {},
                "Historiske_Vurderinger": []
            },
            "Bofæller_Netværk": [],
            "Social_Media_Links": [],
            "Metadata": {
                "Timestamp": self.start_time.isoformat(),
                "Software": "GOLIATH V36 Enhanced",
                "Bypass_Method": "Native Google SERP + Async Multi-Source Extraction",
                "Sources": [],
                "Confidence_Scores": {}
            }
        }

    def _log(self, message: str, color: str = C.CYAN) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {color}{message}{C.RESET}\n")

    def _update_progress(self, pct: int, message: str) -> None:
        sys.stdout.write("\r" + " " * 100 + "\r")
        status = f"{C.MAGENTA}[*] {message}... {pct}%{C.RESET}"
        if self.rate_limited:
            status += f" {C.RED}[RATE LIMITED]{C.RESET}"
        sys.stdout.write(status)
        sys.stdout.flush()

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        """Synchronous wrapper around async logic for the Orchestrator."""
        if target:
            self.name = target.strip()
            self.data["Identitet"] = self.name
            
        print(f"\n{C.WHITE}{'='*80}{C.RESET}")
        print(f"{C.WHITE} MODULE 01: ENHANCED DIRECTORY & PROPERTY INTELLIGENCE (V36){C.RESET}")
        print(f"{C.WHITE}{'='*80}{C.RESET}")
        self._log(f"Target: {self.name} | Location: {self.city}", C.YELLOW)

        try:
            if driver: driver.set_window_position(-2000, 0)
        except Exception:
            pass

        # Kør den asynkrone event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an event loop (e.g. jupyter), create task
            loop.create_task(self._async_run(driver))
        else:
            loop.run_until_complete(self._async_run(driver))
            
        return self.data

    async def _async_run(self, driver) -> None:
        # Phase 1: Parallel data collection (SERP & Dorking)
        self._update_progress(10, "Initiating Parallel Matrix Collection")
        if driver:
            await self._execute_parallel_collection(driver)
        else:
            self._log("Ingen WebDriver. Springer over SERP-baseret opslag.", C.RED)

        # Phase 2: Enhanced Analysis (DinGeo)
        if self.data["Ejendom"].get("Vej"):
            self._update_progress(40, f"Udfører Deep-Audit på {self.data['Ejendom']['Vej']}")
            await self._enhanced_dingeo_analysis(driver)
            
            self._update_progress(70, "Kortlægger husstand og bofæller")
            await self._find_cohabitants_async(driver)
            
            self._update_progress(85, "Cross-referencing Social Media & Real Estate")
            await self._social_media_cross_reference()
            await self._geospatial_validation()

        # Phase 3: Data consolidation
        self._update_progress(100, "Enhanced intelligence gathering complete")
        self.data["Telefonnumre"] = sorted(list(self.data["Telefonnumre"]))
        
        # Udskrivning og Gem
        self._print_enhanced_dashboard()
        
        choice = input(f"\n{C.YELLOW}[?] Archive intelligence report to disk? (y/n): {C.RESET}").lower()
        if choice in ['y', 'j', 'yes', 'ja']:
            self.save_json()
            
        datalake.ingest(self.name_module, self.name, self.data)

    async def _execute_parallel_collection(self, driver):
        """Parallel data collection from multiple sources."""
        sources = [
            ("Google SERP", self._google_serp_strike),
            ("Bing Dorking", self._bing_dorking)
        ]

        # Use ThreadPool to run synchronous selenium stuff in background
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            tasks = [
                loop.run_in_executor(executor, func, driver)
                for name, func in sources
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

    def _google_serp_strike(self, driver):
        """Enhanced Google SERP implementation with better parsing."""
        query = f'site:krak.dk OR site:degulesider.dk "{self.name}" "{self.city}" ejendom OR bolig'
        url = f"https://www.google.dk/search?q={urllib.parse.quote(query)}"

        try:
            driver.get(url)
            time.sleep(2)
            try:
                consent = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='L2AGLb'] | //button[.//div[text()='Accepter alle']]"))
                )
                driver.execute_script("arguments[0].click();", consent)
                time.sleep(1)
            except Exception: pass

            elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
            for el in elements:
                text = el.text
                phones = extract_danish_phones(text)
                for phone in phones:
                    formatted = f"{phone[:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]}"
                    self.data["Telefonnumre"].add(formatted)
                    self.data["Metadata"]["Sources"].append("Google SERP Phone")

                match = validate_danish_address(text)
                if match and not self.data["Ejendom"].get("Vej"):
                    self.data["Ejendom"]["Vej"] = match["vej"]
                    self.data["Ejendom"]["Post"] = match["post"]
                    self.data["Ejendom"]["By"] = match["by"]
                    self.data["Ejendom"]["Historik"].append({
                        "source": "Google SERP",
                        "timestamp": datetime.now().isoformat(),
                        "address": match["full"]
                    })
                    self._log(f"Google Address Confirmed: {match['full']}", C.GREEN)

        except Exception as e:
            self.rate_limited = True

    def _bing_dorking(self, driver):
        """Bing-specific dorking implementation."""
        dork = f'(site:krak.dk OR site:degulesider.dk) "{self.name}" "{self.city}"'
        hits = omni_dork_search(driver, dork, max_links=5)

        for hit in hits:
            full_text = f"{hit.get('title','')} {hit.get('snippet','')}"
            phones = extract_danish_phones(full_text)
            for phone in phones:
                formatted = f"{phone[:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]}"
                self.data["Telefonnumre"].add(formatted)
                self.data["Metadata"]["Sources"].append("Bing Dork")

            match = validate_danish_address(full_text)
            if match and not self.data["Ejendom"].get("Vej"):
                self.data["Ejendom"]["Vej"] = match["vej"]
                self.data["Ejendom"]["Post"] = match["post"]
                self.data["Ejendom"]["By"] = match["by"]
                self.data["Ejendom"]["Historik"].append({
                    "source": "Bing Dork",
                    "timestamp": datetime.now().isoformat(),
                    "address": match["full"]
                })

    async def _enhanced_dingeo_analysis(self, driver):
        """Completely revamped DinGeo analysis with async capabilities."""
        vej_clean = self.data["Ejendom"]["Vej"].split(',')[0].strip()
        post = self.data["Ejendom"]["Post"]
        by_clean = self.data["Ejendom"]["By"].split(' ')[0].strip()

        slug_c = f"{post}-{by_clean}".lower()
        slug_v = re.sub(r'[^a-z0-9æøå\-]', '', vej_clean.replace(" ", "-").replace("æ","ae").replace("ø","oe").replace("å","aa"))
        base = f"https://www.dingeo.dk/adresse/{slug_c}/{slug_v}"

        endpoints = {
            "BBR_Stamdata": {"path": "", "parser": self._parse_bbr_data, "source": "DinGeo BBR"},
            "Skat": {"path": "/skat/", "parser": self._parse_skat_data, "source": "DinGeo Skat"},
            "Vurdering": {"path": "/vurdering/", "parser": self._parse_vurdering_data, "source": "DinGeo Vurdering"},
            "Infrastruktur": {"path": "/internet-mobil/", "parser": self._parse_infrastructure, "source": "DinGeo Infrastruktur"}
        }

        async with aiohttp.ClientSession() as http_session:
            tasks = []
            for key, config in endpoints.items():
                url = base + config["path"]
                tasks.append(self._fetch_dingeo_endpoint(http_session, url, config["parser"], key))
            await asyncio.gather(*tasks)

    async def _fetch_dingeo_endpoint(self, http_session, url, parser, data_key):
        """Async endpoint fetcher with retry logic."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                async with http_session.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        await parser(html, data_key)
                        self.data["Metadata"]["Sources"].append(f"DinGeo {data_key}")
                        break
                    elif response.status == 429:
                        self.rate_limited = True
                        await asyncio.sleep(self.RATE_LIMIT_DELAY * (attempt + 1))
                    else:
                        break
            except Exception:
                await asyncio.sleep(1)

    async def _parse_bbr_data(self, html: str, data_key: str):
        soup = BeautifulSoup(html, 'html.parser')
        bbr_data = {}
        for row in soup.select('table.bbr-data tr, tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).replace(':', '')
                value = cells[1].get_text(strip=True)
                if key in ["Opførselsesår", "Antal værelser", "Etageareal", "Boligtype", "Varmeinstallation"]:
                    bbr_data[key] = value

        if bbr_data:
            self.data["DinGeo_Intelligence"][data_key].update(bbr_data)

    async def _parse_skat_data(self, html: str, data_key: str):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        if "Boligskat" in text:
            m = re.search(r'Boligskat.*?(?:2024)?[:\s]*([0-9\.]+)\s*kr', text)
            if m: self.data["DinGeo_Intelligence"][data_key]["Boligskat"] = m.group(1)

    async def _parse_vurdering_data(self, html: str, data_key: str):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        m = re.search(r'Dingestimat[:\s]*([0-9\.]+)\s*kr', text, re.IGNORECASE)
        if m: self.data["DinGeo_Intelligence"][data_key]["Dingestimat"] = m.group(1)
        m2 = re.search(r'Seneste salgspris[:\s]*([0-9\.]+)\s*kr', text, re.IGNORECASE)
        if m2: self.data["DinGeo_Intelligence"][data_key]["Seneste_Salg"] = m2.group(1)

    async def _parse_infrastructure(self, html: str, data_key: str):
        text = html.lower()
        if "fibernet" in text: self.data["DinGeo_Intelligence"][data_key]["Fiber"] = "Ja"
        if "5g" in text: self.data["DinGeo_Intelligence"][data_key]["5G"] = "Ja"

    async def _find_cohabitants_async(self, driver):
        if not self.data["Ejendom"].get("Vej") or not driver:
            return

        addr = self.data["Ejendom"]["Vej"].split(',')[0].strip()
        queries = [
            f'site:krak.dk "{addr}" "{self.data["Ejendom"]["Post"]}"'
        ]

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            for query in queries:
                try:
                    hits = await loop.run_in_executor(executor, lambda: omni_dork_search(driver, query, max_links=3))
                    for hit in hits:
                        name = hit.get('title', '').split('-')[0].strip()
                        if (name and self.name.lower() not in name.lower() and "Krak" not in name and name not in self.data["Bofæller_Netværk"]):
                            self.data["Bofæller_Netværk"].append(name)
                            self._log(f"Bofælle Detekteret: {name}", C.MAGENTA)
                except Exception: pass

    async def _social_media_cross_reference(self):
        """Cross-reference with social media platforms using async requests."""
        platforms = [
            ("Facebook", f"site:facebook.com \"{self.name}\" \"{self.city}\""),
            ("LinkedIn", f"site:linkedin.com \"{self.name}\" \"{self.city}\"")
        ]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async def fetch_social(session, plat, q):
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        links = re.findall(r'href="(https?://(?:www\.)?(?:facebook\.com|linkedin\.com)[^"]+)"', html)
                        for l in links:
                            if l not in self.data["Social_Media_Links"]:
                                self.data["Social_Media_Links"].append(l)
                                self._log(f"Social Media Profil Fundet: {l[:50]}...", C.GREEN)
            except Exception: pass

        async with aiohttp.ClientSession() as http_session:
            tasks = [fetch_social(http_session, p, q) for p, q in platforms]
            await asyncio.gather(*tasks)

    async def _geospatial_validation(self):
        """Build maps links."""
        if not self.data["Ejendom"].get("Vej"): return
        addr_str = f"{self.data['Ejendom']['Vej']}, {self.data['Ejendom']['Post']} {self.data['Ejendom']['By']}"
        encoded = urllib.parse.quote(addr_str)
        self.data["Ejendom"]["Koordinater"] = f"https://www.google.com/maps/search/?api=1&query={encoded}"

    def _print_enhanced_dashboard(self):
        print(f"\n{C.BG_RED}{C.WHITE} TACTICAL DIRECTORY SUMMARY: {self.name.upper()} {C.RESET}\n")
        
        t_list = ", ".join(self.data["Telefonnumre"]) if self.data["Telefonnumre"] else "INGEN FUNDET"
        print(f"[{C.GREEN}+{C.RESET}] Telefoner: {C.GREEN}{t_list}{C.RESET}")
        
        addr = f"{self.data['Ejendom'].get('Vej', '')}, {self.data['Ejendom'].get('Post', '')} {self.data['Ejendom'].get('By', '')}".strip(" ,")
        print(f"[{C.GREEN}+{C.RESET}] Adresse:   {C.GREEN}{addr if addr else 'INGEN FUNDET'}{C.RESET}")
        
        bbr = self.data["DinGeo_Intelligence"]["BBR_Stamdata"]
        if bbr:
            print(f"[{C.CYAN}*{C.RESET}] BBR Data:  {C.CYAN}Opført {bbr.get('Opførselsesår', 'N/A')} | {bbr.get('Boligtype', 'N/A')} | {bbr.get('Etageareal', 'N/A')}{C.RESET}")
            
        if self.data["Bofæller_Netværk"]:
            print(f"[{C.MAGENTA}*{C.RESET}] Netværk:   {C.MAGENTA}{', '.join(self.data['Bofæller_Netværk'])}{C.RESET}")

        if self.data["Social_Media_Links"]:
            print(f"[{C.MAGENTA}*{C.RESET}] Social:    {C.MAGENTA}{len(self.data['Social_Media_Links'])} Profiler Fundet{C.RESET}")

        print(f"{C.DIM}" + "-"*80 + f"{C.RESET}")

    def save_json(self):
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        safe_name = "".join([c for c in self.name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        path = f"{session.get('loot_folder', 'loot_evidence')}/01_DIRECTORY_{safe_name.replace(' ', '_')}.json"
        
        try:
            if os.path.exists(path): os.remove(path)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
            self._log(f"Rapport gemt sikkert: {path}", C.GREEN)
        except Exception as e:
            self._log(f"Fejl ved arkivering: {e}", C.RED)

# Backwards compatibility alias for Orchestrator
DirectoryIntelligenceHunter = EnhancedDirectoryIntelligenceHunter
KrakIntelligenceAnalyst = EnhancedDirectoryIntelligenceHunter