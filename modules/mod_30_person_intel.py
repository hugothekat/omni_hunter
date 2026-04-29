# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V36: THE APEX JUGGERNAUT ORCHESTRATOR
📌 Formål: Total Identity Resolution, Recursive Pivoting, Breach Hunting & AI Fusion.
OPERATIONAL SPECIFICATIONS:
- 10-Phase Autonomous Intelligence Pipeline.
- Historical Data Lake Correlation.
- Recursive Clearnet Dorking & Footprint Tracking.
- Native Asynchronous Breach API Matrix (HIBP, XposedOrNot, LeakCheck).
- Native Darkweb Proxy Recon (Ahmia scrape).
- Threaded Omni-Pivot.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import time
import json
import os
import re
import urllib.parse
import threading
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List, Set, Optional

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, ThreatIntelExtractor, datalake, sanitize_filename
from core.network import http, omni_dork_search, safe_get_with_retry

try:
    from core.config_vault import vault
    CONFIG = vault.state if vault else {}
except ImportError:
    CONFIG = {}

try:
    from core.nexus import nexus, EntityType
except ImportError:
    nexus = None

class AutonomousOrchestrator(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.name = "APEX ORCHESTRATOR (Identity Resolution, Breach & Omni-Pivot)"
        self.description = "Autonom 10-faset identitets-kortlægning, breach hunting og AI-integration."
        self.category = ModuleCategory.PERSON
        self.print_lock = threading.Lock()
        
        self.target_name: str = ""
        self.max_recursion_depth: int = 2
        self.seen_targets: Set[str] = set()
        self.noise_domains = ["microsoft.com", "outlook.office", "support.google", "login.live", "wikipedia.org", "eniro.dk"]
        
        self.hibp_key = CONFIG.get("api_keys", {}).get("hibp_api_key", "")
        
        self.intel_pool: Dict[str, Any] = {
            "Mål": "",
            "Gættede_Aliaser": set(),
            "Fundne_Emails": set(),
            "Fundne_Brugernavne": set(),
            "Telefonnumre": set(),
            "Nummerplader": set(),
            "MAC_Adresser": set(),
            "Virk_Links": set(),
            "Eksponerede_Dokumenter": set(),
            "Kryptovaluta_Wallets": set(),
            "IP_Adresser": set(),
            "CPR_Fragments": set(),
            "Tidslinje_Bopæl": [],
            "Confidence_Score": 0,
            
            # --- NYT V36: NATIVE BREACH & FOOTPRINT DATA ---
            "Breach_Data": {
                "Total_Verified_Breaches": 0,
                "Lækkede_Passwords_Fundet": False,
                "Breach_Sources": set(),
                "Eksponerede_Data_Typer": set(),
                "Verified_Databases": {
                    "HIBP": [], "XposedOrNot": [], "BreachDirectory": [], "LeakCheck": []
                }
            },
            "Underground_Syndicates": {
                "Hacker_Forums": set(),
                "Paste_Dumps": set(),
                "GitHub_GitLab_Dev": set(),
                "Telegram_Channels": set(),
                "Cloud_Trello_Docs": set(),
                "Reddit_Dox_Mentions": set(),
                "Infostealer_Logs": set()
            },
            "Footprint_Spor": set(),
            "Darkweb_Spor": set(),
            
            "Metadata": {
                "Timestamp": datetime.now().isoformat(),
                "Software": "GOLIATH V36 APEX JUGGERNAUT ORCHESTRATOR"
            }
        }

    def _log(self, message: str, level: str = "INFO", indent: int = 0) -> None:
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "ERROR": C.RED, "SUCCESS": C.GREEN, "PIVOT": C.MAGENTA, "CRITICAL": C.RED}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "  " * indent
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {prefix}[{color}{level}{C.RESET}] {message}\n")

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        self.target_name = target.strip()
        if not self.target_name:
            self._log("Ingen target angivet. Afbryder.", "ERROR")
            return self.data
            
        self.intel_pool["Mål"] = self.target_name
        self.seen_targets.add(self.target_name.lower())
        
        print(f"\n{C.BG_RED}{C.WHITE} === THE APEX JUGGERNAUT ORCHESTRATOR ENGAGED === {C.RESET}\n")
        self._log(f"Initiating Global Identity Resolution Sequence for: {self.target_name}", "INFO")

        # FASE 0: Data Lake Correlation
        self._phase_0_historical_lake()

        # FASE 1: Alias Permutations
        self._phase_1_generate_permutations()

        # FASE 2: Recursive Clearnet Dorking
        self._log("FASE 2: Executing Recursive Clearnet Intelligence Sweep...", "INFO")
        self._phase_2_recursive_dorking(driver, self.target_name, current_depth=0)

        # FASE 3: CVR/Virk Bopæls-historik
        if self.intel_pool["Virk_Links"]:
            self._log("FASE 3: Extracting historical residency data (CVR/Virk)...", "INFO")
            for link in list(self.intel_pool["Virk_Links"])[:3]: 
                self._phase_3_virk_pivot(driver, link)

        # --- NATIVE FASE 4: INTEGRERET BREACH, FOOTPRINT & DARKWEB PIPELINE ---
        if self.intel_pool["Fundne_Emails"]:
            self._log("FASE 4: INITIATING NATIVE BREACH & FOOTPRINT AUDIT", "CRITICAL")
            self._phase_4_breach_and_footprint(driver)
        else:
            self._log("Ingen emails fundet. Bypasser Breach & Footprint Audit.", "WARN")

        # FASE 5: Vurdering
        self._phase_5_confidence_scoring()
        self._print_intel_summary()

        # FASE 6: THREADED OMNI-PIVOT (Eksterne moduler)
        self._log("FASE 6: INITIATING PARALLEL OMNI-PIVOT ENGINE", "SUCCESS")
        self._phase_6_threaded_omni_pivot(driver)

        # FASE 7: AI & VISUALIZATION
        self._log("FASE 7: Finalizing Intelligence Models (AI, Graph & GEOINT)", "INFO")
        self._phase_7_finalize_models()

        # FASE 8: Archiving
        self._phase_8_archive()
        
        self._log("MISSION COMPLETE. Apex Orchestrator Disengaging.", "SUCCESS")
        return self.intel_pool

    # =========================================================================
    # DE DRIFTSFASER
    # =========================================================================

    def _phase_0_historical_lake(self) -> None:
        self._log("FASE 0: Cross-referencing Target in OmniDataLake...", "INFO")
        try:
            if hasattr(datalake, 'query_cross_reference'):
                records = datalake.query_cross_reference(self.target_name)
                if records:
                    self._log(f"Found {len(records)} previous occurrences in Intelligence Database!", "SUCCESS", indent=1)
        except Exception: pass

    def _phase_1_generate_permutations(self) -> None:
        parts = self.target_name.lower().split()
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            yr = str(datetime.now().year)[-2:] 
            aliases = [f"{f}{l}", f"{f}.{l}", f"{f[0]}{l}", f"{f}{l[0]}", f"{f}_{l}", f"{f}{l}123", f"{f}{l}{yr}"]
            for a in aliases: 
                self.intel_pool["Gættede_Aliaser"].add(a)
        self._log(f"FASE 1: Genereret {len(self.intel_pool['Gættede_Aliaser'])} Alias-permutationer.", "SUCCESS", indent=1)

    def _phase_2_recursive_dorking(self, driver: Any, target: str, current_depth: int) -> None:
        if current_depth > self.max_recursion_depth: return
        self._log(f"[DEPTH {current_depth}] Sweeping vectors for: {target}", "PIVOT", indent=current_depth)

        queries = [
            f'"{target}"', 
            f'"{target}" @gmail.com OR @hotmail.com OR @icloud.com',
            f'"{target}" site:instagram.com OR site:tiktok.com OR site:linkedin.com',
            f'"{target}" site:github.com OR site:reddit.com OR site:pastebin.com',
            f'"{target}" site:virk.dk OR site:proff.dk OR site:ownr.dk',
            f'"{target}" ext:pdf OR ext:docx OR ext:xls OR ext:txt'
        ]

        all_hits = []
        collected_text = ""

        def run_dork(q: str) -> List[Dict]:
            try: return omni_dork_search(driver, q, max_links=4)
            except Exception: return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_dork, q) for q in queries]
            for future in concurrent.futures.as_completed(futures):
                hits = future.result()
                for hit in hits:
                    u = hit.get('url', '')
                    if u and not any(d in u for d in self.noise_domains):
                        all_hits.append(hit)
                        collected_text += f" {hit.get('title','')} {hit.get('snippet','')}"

        iocs = ThreatIntelExtractor.extract_all(collected_text)
        danish_phones = ThreatIntelExtractor.extract_danish_phones(collected_text)
        self._ingest_iocs(iocs, danish_phones, all_hits, target)

        new_targets = []
        for em in iocs.get("email", []):
            if em.lower() not in self.seen_targets and self.target_name.lower() not in em.lower():
                new_targets.append(em.lower())
                self.seen_targets.add(em.lower())
                
        for ph in list(danish_phones)[:2]:
            if ph not in self.seen_targets:
                new_targets.append(ph)
                self.seen_targets.add(ph)

        for nt in new_targets[:3]:
            self._log(f"Auto-Pivot Triggered on new identifier: {nt}", "SUCCESS", indent=current_depth+1)
            self._phase_2_recursive_dorking(driver, nt, current_depth + 1)

    def _ingest_iocs(self, iocs: Dict, phones: Set[str], hits: List[Dict], source_target: str) -> None:
        with self.print_lock:
            self.intel_pool["Fundne_Emails"].update(iocs.get("email", []))
            self.intel_pool["IP_Adresser"].update([ip for ip in iocs.get("ipv4", []) if not ip.startswith("1.0")])
            self.intel_pool["MAC_Adresser"].update(iocs.get("mac", []))
            self.intel_pool["Telefonnumre"].update(phones)
            self.intel_pool["CPR_Fragments"].update(iocs.get("danish_cpr", []))
            self.intel_pool["Nummerplader"].update([r.replace(" ","") for r in re.findall(r'\b[A-ZÆØÅ]{2}\s?\d{5}\b', str(hits))])
            
            for k in ["crypto_btc", "crypto_eth", "crypto_xmr", "iban"]:
                self.intel_pool["Kryptovaluta_Wallets"].update([f"{k.upper()}: {x}" for x in iocs.get(k, [])])

            for hit in hits:
                url = hit['url']
                h_match = re.search(r'(?:instagram\.com|tiktok\.com\/@|twitter\.com|github\.com)\/([a-zA-Z0-9._-]+)', url)
                if h_match: self.intel_pool["Fundne_Brugernavne"].add(h_match.group(1))
                if any(x in url for x in ["virk.dk", "ownr.dk", "proff.dk"]): self.intel_pool["Virk_Links"].add(url)
                if url.lower().endswith(('.pdf', '.docx', '.xls', '.txt')): self.intel_pool["Eksponerede_Dokumenter"].add(url)

            if nexus:
                for e in iocs.get("email", []):
                    nexus.ingest(EntityType.EMAIL, e, source=f"Dorking:{source_target}", confidence=0.8)
                    nexus.link(self.target_name, e, "Tilknyttet Email")
                for p in phones:
                    nexus.ingest(EntityType.PHONE, p, source=f"Dorking:{source_target}", confidence=0.8)
                    nexus.link(self.target_name, p, "Tilknyttet Tlf")

    def _phase_3_virk_pivot(self, driver: Any, url: str) -> None:
        if not driver: return
        if "person" in url and "deltager" not in url: url = url.rstrip('/') + "/deltager"
        if safe_get_with_retry(driver, url, max_retries=1):
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "tr, div.address")
                for r in rows:
                    if any(x in r.text for x in ["Bopæl", "Vej", "Adresse", "Postnr"]):
                        clean_addr = r.text.replace("\n", " | ")
                        self.intel_pool["Tidslinje_Bopæl"].append(clean_addr)
                        self._log(f"Bopæl Udtrukket: {clean_addr}", "SUCCESS", indent=2)
            except Exception: pass

    # =========================================================================
    # NATIVE FASE 4: BREACH, FOOTPRINT & DARKWEB (Erstatter Modul 03, 06, 08, 09)
    # =========================================================================
    def _phase_4_breach_and_footprint(self, driver: Any) -> None:
        emails_to_check = list(self.intel_pool["Fundne_Emails"])[:3] # Max 3 for OPSEC / API Limits
        
        for email in emails_to_check:
            self._log(f"Auditing Identity Vector: {email}", "PIVOT", indent=1)
            
            # 4A: Async Breach APIs
            self._execute_async_breach_apis(email)
            
            # 4B: HIBP
            if self.hibp_key: self._query_hibp_api(email)
            elif driver: self._scrape_hibp_frontend(driver, email)
            
            # 4C: Footprint & Underground Dorking
            if driver:
                self._execute_footprint_dorks(driver, email)
                self._darkweb_ahmia_scrape(driver, email)

    def _execute_async_breach_apis(self, email: str):
        def _xon():
            try:
                res = http.get(f"https://api.xposedornot.com/v1/checkbacklink?email={email}", timeout=10)
                if res.status_code == 200:
                    breaches = res.json().get("Breaches", [])
                    if breaches:
                        self._log(f"XposedOrNot confirmed {len(breaches)} breaches for {email}", "CRITICAL", indent=2)
                        with self.print_lock:
                            for b in breaches:
                                name = b[0] if isinstance(b, list) else b
                                self.intel_pool["Breach_Data"]["Verified_Databases"]["XposedOrNot"].append(name)
                                self.intel_pool["Breach_Data"]["Breach_Sources"].add(name)
            except Exception: pass

        def _bd():
            try:
                res = http.get(f"https://breachdirectory.org/api/search?key=free&term={email}", timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("success") and data.get("found", 0) > 0:
                        self._log(f"BreachDirectory flagged {data.get('found')} exposed sources.", "CRITICAL", indent=2)
                        with self.print_lock:
                            for src in data.get("sources", []):
                                name = src.get("name", "Unknown")
                                self.intel_pool["Breach_Data"]["Verified_Databases"]["BreachDirectory"].append(name)
                                self.intel_pool["Breach_Data"]["Breach_Sources"].add(name)
            except Exception: pass

        def _lc():
            try:
                res = http.get(f"https://leakcheck.io/api/public?check={email}", timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("success") and data.get("found", 0) > 0:
                        self._log(f"LeakCheck.io confirmed {data.get('found')} compromise points.", "CRITICAL", indent=2)
                        with self.print_lock:
                            self.intel_pool["Breach_Data"]["Verified_Databases"]["LeakCheck"].append(f"LeakCheck ({data.get('found')} hits)")
                            self.intel_pool["Breach_Data"]["Breach_Sources"].add("LeakCheck.io (Ukendte kilder)")
            except Exception: pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(_xon)
            executor.submit(_bd)
            executor.submit(_lc)

    def _query_hibp_api(self, email: str):
        headers = {"hibp-api-key": self.hibp_key, "user-agent": "PETFE-GOLIATH-OSINT"}
        try:
            res = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}?truncateResponse=false", headers=headers, timeout=10)
            if res.status_code == 200:
                breaches = res.json()
                self._log(f"HIBP API verified {len(breaches)} corporate breaches.", "CRITICAL", indent=2)
                with self.print_lock:
                    for b in breaches:
                        b_name = b.get("Name", "Unknown")
                        self.intel_pool["Breach_Data"]["Verified_Databases"]["HIBP"].append(b_name)
                        self.intel_pool["Breach_Data"]["Breach_Sources"].add(b_name)
                        for dc in b.get("DataClasses", []):
                            self.intel_pool["Breach_Data"]["Eksponerede_Data_Typer"].add(dc)
                            if "password" in dc.lower():
                                self.intel_pool["Breach_Data"]["Lækkede_Passwords_Fundet"] = True
            elif res.status_code == 404:
                self._log("HIBP API reports no known corporate breaches.", "SUCCESS", indent=2)
        except Exception: pass

    def _scrape_hibp_frontend(self, driver: Any, email: str):
        try:
            driver.get("https://haveibeenpwned.com/")
            time.sleep(3)
            try:
                search_box = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "Account")))
                search_box.clear()
                search_box.send_keys(email)
                search_box.send_keys(Keys.ENTER)
            except TimeoutException: return

            time.sleep(4) 
            source = driver.page_source
            if "pwnedCompanyTitle" in source or "Oh no — pwned!" in source:
                breaches = driver.find_elements(By.CSS_SELECTOR, ".pwnedCompanyTitle")
                self._log(f"HIBP Live-Scraper verified {len(breaches)} breaches.", "CRITICAL", indent=2)
                with self.print_lock:
                    for el in breaches:
                        b_name = el.text.strip()
                        if b_name:
                            self.intel_pool["Breach_Data"]["Verified_Databases"]["HIBP"].append(b_name)
                            self.intel_pool["Breach_Data"]["Breach_Sources"].add(b_name)
                    data_points = driver.find_elements(By.CSS_SELECTOR, ".dataClasses")
                    for dp in data_points:
                        for tag in dp.text.split(','):
                            clean_tag = tag.strip()
                            self.intel_pool["Breach_Data"]["Eksponerede_Data_Typer"].add(clean_tag)
                            if "password" in clean_tag.lower():
                                self.intel_pool["Breach_Data"]["Lækkede_Passwords_Fundet"] = True
        except Exception: pass

    def _execute_footprint_dorks(self, driver: Any, email: str):
        dork_matrix = [
            ("Hacker Forums", f'site:breachforums.st OR site:cracked.io OR site:nulled.to OR site:exploit.in "{email}"', "Hacker_Forums"),
            ("GitHub/GitLab Leaks", f'site:github.com OR site:gitlab.com "{email}" (password OR secret OR API_KEY OR token)', "GitHub_GitLab_Dev"),
            ("Telegram Dumps", f'site:t.me "{email}" (combo OR dump OR leak OR password OR log)', "Telegram_Channels"),
            ("Infostealer Logs", f'"{email}" (RedLine OR Raccoon OR Vidar OR Stealer OR "URL: " "USER: " "PASS: ")', "Infostealer_Logs"),
            ("Cloud Misconfigurations", f'site:trello.com OR site:docs.google.com/document/d/ "{email}"', "Cloud_Trello_Docs"),
            ("Raw Pastes", f'site:pastebin.com OR site:ghostbin.co OR site:paste.ee "{email}"', "Paste_Dumps"),
            ("Social Footprints", f'"{email}" (site:facebook.com OR site:instagram.com OR site:linkedin.com OR site:twitter.com)', "Footprint_Spor"),
        ]

        for cat_name, query, target_key in dork_matrix:
            hits = omni_dork_search(driver, query, max_links=3)
            if hits:
                self._log(f"Fandt {len(hits)} spor i: {cat_name}", "CRITICAL" if "Footprint" not in cat_name else "SUCCESS", indent=2)
                with self.print_lock:
                    for h in hits:
                        if target_key == "Footprint_Spor":
                            self.intel_pool["Footprint_Spor"].add(h['url'])
                        else:
                            self.intel_pool["Underground_Syndicates"][target_key].add(h['url'])
            time.sleep(1.5)

    def _darkweb_ahmia_scrape(self, driver: Any, email: str):
        self._log("Querying Tor Gateways (Ahmia) for Darknet references...", "WARN", indent=2)
        ahmia_url = f"https://ahmia.fi/search/?q={urllib.parse.quote(email)}"
        if safe_get_with_retry(driver, ahmia_url, max_retries=1):
            if "No results" not in driver.page_source:
                try:
                    results = driver.find_elements(By.CSS_SELECTOR, "li.result h4 a")
                    for res in results[:3]:
                        onion_link = res.text
                        self.intel_pool["Darkweb_Spor"].add(onion_link)
                        self._log(f"DARKNET HIT: {onion_link}", "CRITICAL", indent=3)
                except Exception: pass

    # =========================================================================
    # VURDERING, OPSAMLING OG EKSTERNE MODULER
    # =========================================================================
    def _phase_5_confidence_scoring(self) -> None:
        score = 0
        if self.intel_pool["Virk_Links"]: score += 15
        if self.intel_pool["Fundne_Brugernavne"]: score += 15
        if self.intel_pool["Fundne_Emails"]: score += 15
        if self.intel_pool["Telefonnumre"]: score += 15
        if self.intel_pool["CPR_Fragments"]: score += 10
        if self.intel_pool["Tidslinje_Bopæl"]: score += 10
        if self.intel_pool["MAC_Adresser"]: score += 10
        
        # Ekstra point for Breach/Darkweb Hits
        if len(self.intel_pool["Breach_Data"]["Breach_Sources"]) > 0: score += 10
        if self.intel_pool["Breach_Data"]["Lækkede_Passwords_Fundet"]: score += 15
        if self.intel_pool["Darkweb_Spor"]: score += 15
        
        self.intel_pool["Confidence_Score"] = min(score, 100)
        self.intel_pool["Breach_Data"]["Total_Verified_Breaches"] = len(self.intel_pool["Breach_Data"]["Breach_Sources"])

    def _print_intel_summary(self) -> None:
        with self.print_lock:
            print(f"\n{C.CYAN}--- TACTICAL INTELLIGENCE SUMMARY: {self.target_name.upper()} ---{C.RESET}")
            print(f"Data Confidence: {C.GREEN if self.intel_pool['Confidence_Score'] > 50 else C.YELLOW}{self.intel_pool['Confidence_Score']}/100{C.RESET}")
            print(f"Usernames:       {C.WHITE}{', '.join(self.intel_pool['Fundne_Brugernavne'])}{C.RESET}")
            print(f"Emails:          {C.WHITE}{', '.join(self.intel_pool['Fundne_Emails'])}{C.RESET}")
            print(f"Phones:          {C.WHITE}{', '.join(self.intel_pool['Telefonnumre'])}{C.RESET}")
            
            # Breach Summary
            b_total = self.intel_pool["Breach_Data"]["Total_Verified_Breaches"]
            if b_total > 0:
                print(f"Verified Breaches: {C.RED}{b_total} (Critical){C.RESET}")
                if self.intel_pool["Breach_Data"]["Lækkede_Passwords_Fundet"]:
                    print(f"Password Status:   {C.RED}COMPROMISED (Cleartext/Hash exposed){C.RESET}")
            
            ug_hits = sum(len(v) for v in self.intel_pool["Underground_Syndicates"].values())
            if ug_hits > 0: print(f"Underground Hits:  {C.RED}{ug_hits} (Forums, Pastes, Stealers){C.RESET}")
            if self.intel_pool["Darkweb_Spor"]: print(f"Darkweb Hits:      {C.RED}{len(self.intel_pool['Darkweb_Spor'])} (Tor Indexed){C.RESET}")
            
            print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")

    def _phase_6_threaded_omni_pivot(self, main_driver: Any) -> None:
        # BEMÆRK: Vi har fjernet kaldet til mod_03 her, fordi det nu er en NATIVE del af Fase 4!
        def _safe_run(module_name: str, class_name: str, target: str, driver=None):
            try:
                import importlib
                mod = importlib.import_module(f"modules.{module_name}")
                cls = getattr(mod, class_name)
                import inspect
                instance = cls(target) if 'name' not in inspect.signature(cls.__init__).parameters else cls()
                self._log(f"Firing {class_name} against {target}", "PIVOT", indent=1)
                instance.run(driver, target)
            except Exception as e:
                self._log(f"{class_name} failed or not found: {e}", "ERROR", indent=2)

        api_tasks = []
        for handle in list(self.intel_pool["Fundne_Brugernavne"])[:2]: api_tasks.append(("mod_23_matrix", "MatrixAnalyzer", handle))
        for ip in list(self.intel_pool["IP_Adresser"])[:2]: api_tasks.append(("mod_10_ip", "IPNetworkAnalyzer", ip))
        for wallet in list(self.intel_pool["Kryptovaluta_Wallets"])[:2]: 
            w_clean = wallet.split(": ")[1] if ": " in wallet else wallet
            api_tasks.append(("mod_19_crypto", "CryptoLedgerAnalyzer", w_clean))

        if api_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                for mod, cls, tgt in api_tasks:
                    executor.submit(_safe_run, mod, cls, tgt, None)

        _safe_run("mod_02_business", "BusinessIntelligenceAnalyst", self.target_name, main_driver)
        for phone in list(self.intel_pool["Telefonnumre"])[:2]: 
            _safe_run("mod_12_revphone", "ReversePhoneIntelligence", phone, main_driver)

    def _phase_7_finalize_models(self) -> None:
        try:
            from modules.mod_27_ai import TitanAIEnrichment
            self._log("Processing Context via Local LLM (Titan AI)...", "INFO", indent=1)
            ai_mod = TitanAIEnrichment(self.target_name)
            
            clean_pool = {k: list(v) if isinstance(v, set) else v for k, v in self.intel_pool.items()}
            # Sikrer at Breach Data også konverteres korrekt
            for k, v in clean_pool["Breach_Data"].items():
                if isinstance(v, set): clean_pool["Breach_Data"][k] = list(v)
            for k, v in clean_pool["Underground_Syndicates"].items():
                if isinstance(v, set): clean_pool["Underground_Syndicates"][k] = list(v)

            res = ai_mod.analyze_text(json.dumps(clean_pool, ensure_ascii=False))
            if res: self.intel_pool["AI_Assessment"] = res
        except Exception as e: 
            self._log(f"AI Enrichment Error: {e}", "WARN", indent=2)

        try:
            from modules.mod_28_graph import GoliathGraphExporter
            from modules.mod_29_kml import GoogleEarthExporter
            self._log("Generating Relational Graphs & KML...", "INFO", indent=1)
            GoliathGraphExporter().generate()
            GoogleEarthExporter().generate()
        except Exception: pass

    def _phase_8_archive(self) -> None:
        # Konverter Set til List for JSON serialisering
        for key in self.intel_pool:
            if isinstance(self.intel_pool[key], set): self.intel_pool[key] = list(self.intel_pool[key])
        
        for key in self.intel_pool["Breach_Data"]:
            if isinstance(self.intel_pool["Breach_Data"][key], set): 
                self.intel_pool["Breach_Data"][key] = list(self.intel_pool["Breach_Data"][key])
                
        for key in self.intel_pool["Underground_Syndicates"]:
            if isinstance(self.intel_pool["Underground_Syndicates"][key], set): 
                self.intel_pool["Underground_Syndicates"][key] = list(self.intel_pool["Underground_Syndicates"][key])

        datalake.ingest(source_module=self.name, target=self.target_name, data=self.intel_pool)
        
        ws_folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(ws_folder, exist_ok=True)
        path = Path(ws_folder) / f"30_ORCHESTRATOR_{sanitize_filename(self.target_name)}.json"
        
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
            
        path.write_text(json.dumps(self.intel_pool, indent=4, ensure_ascii=False), encoding="utf-8")