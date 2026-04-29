# -*- coding: utf-8 -*-
"""
PETFE GOLIATH V29: ASYNC ORCHESTRATOR (TERMINAL-FIRST)
MODUL 30: TOTAL IDENTITY RESOLUTION & PARALLEL PIVOTING
------------------------------------------------------------------
OPERATIONAL SPECIFICATIONS:
- Concurrent Execution: ThreadPoolExecutor for asynkron modul-aktivering.
- Ephemeral Sandboxing: Isoleret WebDriver instans per tråd for at undgå State Contamination.
- Thread-Safe Logging: Sikrer klinisk terminal-output via threading.Lock().
- 8-Layer Dorking Matrix: Trækker metadata præ-pivot.
- Zero-Disk Footprint: Prompt-baseret arkivering.
"""

import time
import json
import os
import re
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime

from core.utils import C, session, REGEX_EMAIL, REGEX_CPR, extract_danish_phones
from core.utils import REGEX_BTC, REGEX_ETH, REGEX_XMR, REGEX_IBAN, REGEX_IPV4
from core.network import omni_dork_search, safe_get_with_retry
from core.browser import get_stealth_driver

# DYNAMISK IMPORT AF MODULER
from modules.mod_02_business import BusinessIntelligenceAnalyst
from modules.mod_03_breach import BreachIntelligenceAnalyst
from modules.mod_04_social import SocialMediaProfiler
from modules.mod_06_emailgen import EmailPatternGenerator
from modules.mod_08_darkweb import DarkWebIntelligence
from modules.mod_10_ip import IPNetworkAnalyzer
from modules.mod_12_revphone import ReversePhoneIntelligence
from modules.mod_17_sniper import SniperModule
from modules.mod_19_crypto import CryptoLedgerAnalyzer
from modules.mod_20_vehicle import VehicleIntelligence
from modules.mod_21_bssid import BSSIDGeofencer
from modules.mod_23_matrix import MatrixAnalyzer
from modules.mod_25_wayback import WaybackMachineIntelligence
from modules.mod_27_ai import TitanAIEnrichment
from modules.mod_28_graph import GoliathGraphExporter
from modules.mod_29_kml import GoogleEarthExporter

# Lokale Regex for præcision
REGEX_MAC_INLINE = re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b')
REGEX_REGNR_INLINE = re.compile(r'\b[A-ZÆØÅ]{2}\s?\d{5}\b')

class PersonIntelligenceOrchestrator:
    
    def __init__(self, target_name):
        self.target_name = target_name.strip()
        self.operator_id = os.getlogin() if hasattr(os, 'getlogin') else "System"
        self.print_lock = threading.Lock()
        
        self.intel_pool = {
            "Mål": self.target_name,
            "Gættede_Aliaser": set(),
            "Fundne_Emails": set(),
            "Fundne_Brugernavne": set(),
            "Telefonnumre": set(),
            "Nummerplader": set(),
            "MAC_Adresser": set(),
            "Virk_Links": set(),
            "GitHub_Reddit_Spor": set(),
            "Eksponerede_Dokumenter": set(),
            "Kryptovaluta_Wallets": set(),
            "IP_Adresser": set(),
            "CPR_Fragments": set(),
            "Tidslinje_Bopæl": [],
            "Confidence_Score": 0,
            "Metadata": {
                "Timestamp": datetime.now().isoformat(),
                "Software": "GOLIATH V29 ASYNC ORCHESTRATOR",
                "Operatør": self.operator_id
            }
        }
        self.noise_domains = ["microsoft.com", "outlook.office", "support.google", "login.live", "wikipedia.org", "eniro.dk"]

    def _log(self, message, level="INFO"):
        """Thread-safe standardiseret logning."""
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "ERROR": C.RED, "SUCCESS": C.GREEN, "PIVOT": C.MAGENTA}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} [{color}{level}{C.RESET}] {message}\n")

    def run(self, driver):
        """Hoved-eksekvering af Fase 1-4 (Synkront) og Fase 5 (Asynkront)."""
        print(f"\n{C.DIM}" + "-"*80 + f"{C.RESET}")
        self._log(f"Initiating Identity Resolution for: {self.target_name}", "INFO")

        # FASE 0: Alias Permutationer
        self._generate_identity_permutations()

        # FASE 1: Deep Clearnet Dorking
        self._log("FASE 1: Executing 8-Layer Clearnet Intelligence Sweep...", "INFO")
        self._run_deep_clearnet_dorking(driver)

        # FASE 2: CVR/Virk Bopæls-historik
        if self.intel_pool["Virk_Links"]:
            self._log("FASE 2: Extracting historical residency data (CVR/Virk)...", "INFO")
            for link in list(self.intel_pool["Virk_Links"])[:3]: 
                self._pivot_virk_history(driver, link)

        # FASE 3: Darknet & Leak Recon
        self._log("FASE 3: Querying Darknet Indexers & Paste-Dumps...", "WARN")
        self._run_darknet_recon(driver)
        for email in list(self.intel_pool["Fundne_Emails"])[:3]:
            self._pastebin_leak_pivot(driver, email)

        # FASE 4: Vurdering
        self._calculate_confidence_score()
        self._print_intel_summary()
        
        # OPERATØR KONTROL
        with self.print_lock:
            valg = input(f"\n{C.YELLOW}[?] Execute PARALLEL OMNI-PIVOT på indsamlede datapunkter? (y/n): {C.RESET}").strip().lower()
            
        if valg in ['n', 'nej', 'no']: 
            self._log("Operation suspended by operator.", "WARN")
            self._handle_archiving()
            return

        # FASE 5: THREADED OMNI-PIVOT
        self._log("FASE 5: INITIATING PARALLEL OMNI-PIVOT ENGINE", "SUCCESS")
        self._execute_threaded_omni_pivot()

        # FASE 6: AI & VISUALIZATION (Køres sekventielt til sidst)
        self._log("FASE 6: Finalizing Intelligence Models (AI & Graph)", "INFO")
        self._finalize_intelligence_models()

        self._handle_archiving()
        self._log("MISSION COMPLETE. System disengaging.", "SUCCESS")

    def _generate_identity_permutations(self):
        parts = self.target_name.lower().split()
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            yr = str(datetime.now().year)[-2:] 
            aliases = [f"{f}{l}", f"{f}.{l}", f"{f[0]}{l}", f"{f}{l[0]}", f"{f}_{l}", f"{f}{l}123", f"{f}{l}{yr}"]
            for a in aliases: self.intel_pool["Gættede_Aliaser"].add(a)

    def _run_deep_clearnet_dorking(self, driver):
        all_hits = []
        name = self.target_name

        queries = [
            f'"{name}"', 
            f'"{name}" @gmail.com OR @hotmail.com OR @icloud.com',
            f'"{name}" site:instagram.com OR site:tiktok.com OR site:facebook.com OR site:linkedin.com',
            f'"{name}" site:github.com OR site:reddit.com OR site:trello.com OR site:pastebin.com',
            f'"{name}" site:virk.dk OR site:proff.dk OR site:ownr.dk OR site:statstidende.dk',
            f'"{name}" ext:pdf OR ext:docx OR ext:xls OR ext:txt',
            f'"{name}" site:afdoede.dk OR site:slaegtogdata.dk OR site:myheritage.dk',
            f'"{name}" site:tinglysning.dk OR site:nummerplade.net OR site:bbr.dk'
        ]

        for q in queries:
            hits = omni_dork_search(driver, q, max_links=6)
            clean_hits = self._clean_hits(hits)
            all_hits.extend(clean_hits)
            self._extract_advanced_intel(clean_hits)

    def _extract_advanced_intel(self, hits):
        for hit in hits:
            snippet = f"{hit.get('title','')} {hit.get('snippet','')}"
            url = hit.get('url','')
            
            for m in REGEX_EMAIL.findall(snippet): self.intel_pool["Fundne_Emails"].add(m.lower())
            for c in REGEX_CPR.findall(snippet): self.intel_pool["CPR_Fragments"].add(c)
            for p in extract_danish_phones(snippet): self.intel_pool["Telefonnumre"].add(p)
            for mac in REGEX_MAC_INLINE.findall(snippet): self.intel_pool["MAC_Adresser"].add(mac)
            for reg in REGEX_REGNR_INLINE.findall(snippet): self.intel_pool["Nummerplader"].add(reg.replace(" ", ""))
            
            for btc in REGEX_BTC.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"BTC: {btc}")
            for eth in REGEX_ETH.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"ETH: {eth}")
            for iban in REGEX_IBAN.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"IBAN: {iban}")
            
            for ip in REGEX_IPV4.findall(snippet): 
                if not ip.startswith("1.0") and not ip.startswith("2.0"): 
                    self.intel_pool["IP_Adresser"].add(ip)

            h_match = re.search(r'(?:instagram\.com|tiktok\.com\/@|twitter\.com|github\.com)\/([a-zA-Z0-9._-]+)', url)
            if h_match: self.intel_pool["Fundne_Brugernavne"].add(h_match.group(1))
            
            if any(x in url for x in ["virk.dk", "ownr.dk", "proff.dk"]): self.intel_pool["Virk_Links"].add(url)
            if any(x in url for x in ["github.com", "reddit.com"]): self.intel_pool["GitHub_Reddit_Spor"].add(url)
            if url.lower().endswith(('.pdf', '.docx', '.xls', '.txt')): self.intel_pool["Eksponerede_Dokumenter"].add(url)

    def _pivot_virk_history(self, driver, url):
        if "person" in url and "deltager" not in url: url = url.rstrip('/') + "/deltager"
        if safe_get_with_retry(driver, url):
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "tr, div.address")
                for r in rows:
                    if any(x in r.text for x in ["Bopæl", "Vej", "Adresse", "Postnr"]):
                        clean_addr = r.text.replace("\n", " | ")
                        self.intel_pool["Tidslinje_Bopæl"].append(clean_addr)
            except Exception: pass

    def _run_darknet_recon(self, driver):
        targets = [self.target_name] + list(self.intel_pool["Fundne_Emails"])[:2]
        for t in targets:
            ahmia_url = f"https://ahmia.fi/search/?q={urllib.parse.quote(t)}"
            if safe_get_with_retry(driver, ahmia_url):
                if "No results" not in driver.page_source:
                    self._log(f"Darknet hits verified for indicator: {t}", "WARN")

    def _pastebin_leak_pivot(self, driver, email):
        dork = f'site:pastebin.com OR site:trello.com "{email}"'
        for h in omni_dork_search(driver, dork, max_links=3):
            self.intel_pool["Eksponerede_Dokumenter"].add(h.get('url'))

    def _clean_hits(self, hits):
        seen = set(); clean = []
        for h in hits:
            u = h.get('url', '')
            if not u or u in seen or any(d in u for d in self.noise_domains): continue
            clean.append(h); seen.add(u)
        return clean

    def _calculate_confidence_score(self):
        score = 0
        if self.intel_pool["Virk_Links"]: score += 15
        if self.intel_pool["Fundne_Brugernavne"]: score += 15
        if self.intel_pool["Fundne_Emails"]: score += 15
        if self.intel_pool["Telefonnumre"]: score += 15
        if self.intel_pool["CPR_Fragments"]: score += 10
        if self.intel_pool["Tidslinje_Bopæl"]: score += 10
        if self.intel_pool["Nummerplader"]: score += 10
        if self.intel_pool["MAC_Adresser"]: score += 10
        self.intel_pool["Confidence_Score"] = min(score, 100)

    def _print_intel_summary(self):
        with self.print_lock:
            print(f"\n{C.CYAN}--- TACTICAL INTELLIGENCE SUMMARY: {self.target_name.upper()} ---{C.RESET}")
            print(f"Data Confidence: {C.GREEN}{self.intel_pool['Confidence_Score']}/100{C.RESET}")
            print(f"Usernames:       {C.WHITE}{', '.join(self.intel_pool['Fundne_Brugernavne'])}{C.RESET}")
            print(f"Emails:          {C.WHITE}{', '.join(self.intel_pool['Fundne_Emails'])}{C.RESET}")
            print(f"Phones:          {C.WHITE}{', '.join(self.intel_pool['Telefonnumre'])}{C.RESET}")
            if self.intel_pool['Nummerplader']: print(f"Vehicles:        {C.RED}{', '.join(self.intel_pool['Nummerplader'])}{C.RESET}")
            if self.intel_pool['Kryptovaluta_Wallets']: print(f"Crypto:          {C.RED}{', '.join(self.intel_pool['Kryptovaluta_Wallets'])}{C.RESET}")
            if self.intel_pool['IP_Adresser']: print(f"IP Addresses:    {C.RED}{', '.join(self.intel_pool['IP_Adresser'])}{C.RESET}")
            print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")

    # =========================================================================
    # THREADED OMNI-PIVOT ENGINE
    # =========================================================================
    def _execute_threaded_omni_pivot(self):
        """Udfører moduler asynkront. Reducerer scanningstid markant."""
        
        def run_api_module(module_class, target, kwargs=None):
            """Wrapper for moduler der IKKE kræver Selenium (Lynhurtige)"""
            try:
                self._log(f"Executing {module_class.__name__} on {target}", "PIVOT")
                kwargs = kwargs or {}
                instance = module_class(target, **kwargs)
                instance.run(None)
            except Exception as e:
                self._log(f"Module {module_class.__name__} failed: {e}", "ERROR")

        def run_browser_module(module_class, target, kwargs=None):
            """Wrapper for moduler der KRÆVER Selenium (Kortlivet sandbox driver)"""
            driver = None
            try:
                self._log(f"Spooling Sandboxed WebDriver for {module_class.__name__} on {target}", "PIVOT")
                driver = get_stealth_driver()
                kwargs = kwargs or {}
                instance = module_class(target, **kwargs)
                instance.run(driver)
            except Exception as e:
                self._log(f"Browser Module {module_class.__name__} failed: {e}", "ERROR")
            finally:
                if driver: driver.quit()

        # Bygger lister over opgaver
        api_tasks = []
        browser_tasks = []

        # 1. Tildel API/Requests Tasks
        for handle in list(self.intel_pool["Fundne_Brugernavne"])[:3]:
            api_tasks.append((MatrixAnalyzer, handle, {}))
            
        for ip in list(self.intel_pool["IP_Adresser"])[:2]:
            api_tasks.append((IPNetworkAnalyzer, ip, {}))
            
        for wallet in list(self.intel_pool["Kryptovaluta_Wallets"])[:2]:
            clean_addr = wallet.split(": ")[1] if ": " in wallet else wallet
            api_tasks.append((CryptoLedgerAnalyzer, clean_addr, {}))
            
        for mac in list(self.intel_pool["MAC_Adresser"])[:2]:
            api_tasks.append((BSSIDGeofencer, mac, {}))
            
        for doc in list(self.intel_pool["Eksponerede_Dokumenter"])[:2]:
            api_tasks.append((WaybackMachineIntelligence, doc, {}))

        # 2. Tildel Browser Tasks
        browser_tasks.append((BusinessIntelligenceAnalyst, self.target_name, {}))
        
        for email in list(self.intel_pool["Fundne_Emails"])[:2]:
            browser_tasks.append((BreachIntelligenceAnalyst, email, {}))
            
        for handle in list(self.intel_pool["Fundne_Brugernavne"])[:2]:
            browser_tasks.append((SocialMediaProfiler, handle, {}))
            
        for phone in list(self.intel_pool["Telefonnumre"])[:2]:
            browser_tasks.append((ReversePhoneIntelligence, phone, {}))
            
        for regnr in list(self.intel_pool["Nummerplader"])[:2]:
            browser_tasks.append((VehicleIntelligence, regnr, {}))

        # KØR API TASKS (Hurtige, Høj Concurrency)
        if api_tasks:
            self._log(f"Dispatching {len(api_tasks)} API Tasks...", "INFO")
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(run_api_module, cls, tgt, kw) for cls, tgt, kw in api_tasks]
                concurrent.futures.wait(futures)

        # KØR BROWSER TASKS (Tunge, Lav Concurrency for at skåne RAM/CPU)
        if browser_tasks:
            self._log(f"Dispatching {len(browser_tasks)} Browser Tasks...", "INFO")
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(run_browser_module, cls, tgt, kw) for cls, tgt, kw in browser_tasks]
                concurrent.futures.wait(futures)

    def _finalize_intelligence_models(self):
        """Kører Wordlist, AI og Graph generation sekventielt til sidst."""
        self._log("Building Targeted Wordlist (Sniper)...", "INFO")
        try:
            email_seed = list(self.intel_pool["Fundne_Emails"])[0] if self.intel_pool["Fundne_Emails"] else ""
            cpr_seed = list(self.intel_pool["CPR_Fragments"])[0] if self.intel_pool["CPR_Fragments"] else ""
            clues = ",".join(self.intel_pool["Fundne_Brugernavne"])
            SniperModule(name=self.target_name, email=email_seed, cpr=cpr_seed, clues=clues).run()
        except Exception as e: self._log(f"Sniper fejlede: {e}", "ERROR")

        self._log("Processing Context via Local LLM (Titan AI)...", "INFO")
        try:
            context = json.dumps(list(self.intel_pool.items()), default=str)
            TitanAIEnrichment().analyze_text(context)
        except Exception: pass

        self._log("Generating Relational Graphs & KML...", "INFO")
        try:
            GoliathGraphExporter().generate()
            GoogleEarthExporter().generate()
        except Exception: pass

    def _handle_archiving(self):
        with self.print_lock:
            save_choice = input(f"\n{C.YELLOW}[?] Archive Master Report to disk? (y/n): {C.RESET}").lower()
            if save_choice == 'y':
                os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
                path = f"{session.get('loot_folder', 'loot_evidence')}/30_MASTER_{self.target_name.replace(' ', '_')}.json"
                
                export_data = self.intel_pool.copy()
                for key in export_data:
                    if isinstance(export_data[key], set):
                        export_data[key] = list(export_data[key])
                        
                Path(path).write_text(json.dumps(export_data, indent=4, ensure_ascii=False), encoding="utf-8")
                self._log(f"Master Intelligence Profile archived: {path}", "SUCCESS")
            else:
                self._log("Data purged from RAM.", "WARN")