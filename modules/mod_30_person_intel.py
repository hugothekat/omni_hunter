# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V6.0: THE JUGGERNAUT ORCHESTRATOR
MODUL 30: TOTAL IDENTITY RESOLUTION, RECURSIVE PIVOTING & AI FUSION
------------------------------------------------------------------
OPERATIONAL SPECIFICATIONS:
- 8-Phase Autonomous Intelligence Pipeline.
- Historical Data Lake Correlation (Cross-Case Memory).
- Recursive Dorking (Auto-Pivot på opdagede IOCs).
- Threaded Omni-Pivot (Dispatcher under-moduler parallelt).
- Full AI (Titan), Graph (Vis.js) og GEOINT (KML) integration.
"""

import time
import json
import os
import re
import urllib.parse
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, ThreatIntelExtractor, datalake, sanitize_filename
from core.network import omni_dork_search, safe_get_with_retry
from core.browser import get_stealth_driver

try:
    from core.nexus import nexus, EntityType
except ImportError:
    nexus = None

# DYNAMISK IMPORT AF UNDERMODULER TIL FASE 6
from modules.mod_02_business import BusinessIntelligenceAnalyst
from modules.mod_03_breach import BreachIntelligenceAnalyst
from modules.mod_04_social import SocialMediaProfiler
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


class AutonomousOrchestrator(BaseModule):
    
    def __init__(self):
        super().__init__()
        self.name = "GRAND ORCHESTRATOR (Identity Resolution & Omni-Pivot)"
        self.description = "Autonom 8-faset identitets-kortlægning, historisk korrelation og AI-integration."
        self.category = ModuleCategory.PERSON
        self.print_lock = threading.Lock()
        
        self.target_name = ""
        self.max_recursion_depth = 2
        self.seen_targets = set()
        
        self.noise_domains = ["microsoft.com", "outlook.office", "support.google", "login.live", "wikipedia.org", "eniro.dk"]
        
        self.intel_pool = {
            "Mål": "",
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
                "Software": "GOLIATH V6.0 JUGGERNAUT ORCHESTRATOR"
            }
        }

    def _log(self, message, level="INFO", indent=0):
        """Thread-safe standardiseret logning."""
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "ERROR": C.RED, "SUCCESS": C.GREEN, "PIVOT": C.MAGENTA}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "  " * indent
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {prefix}[{color}{level}{C.RESET}] {message}\n")

    def run(self, driver, target: str) -> Dict[str, Any]:
        """Den massive 8-fasede eksekverings-pipeline."""
        self.target_name = target.strip()
        self.intel_pool["Mål"] = self.target_name
        self.seen_targets.add(self.target_name.lower())
        
        print(f"\n{C.BG_RED}{C.WHITE} === THE JUGGERNAUT ORCHESTRATOR ENGAGED === {C.RESET}\n")
        self._log(f"Initiating Identity Resolution Sequence for: {self.target_name}", "INFO")

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

        # FASE 4: Darknet & Leak Recon
        self._log("FASE 4: Querying Darknet Indexers & Paste-Dumps...", "WARN")
        self._phase_4_darknet_recon(driver)

        # FASE 5: Vurdering
        self._phase_5_confidence_scoring()
        self._print_intel_summary()

        # FASE 6: THREADED OMNI-PIVOT
        self._log("FASE 6: INITIATING PARALLEL OMNI-PIVOT ENGINE", "SUCCESS")
        self._phase_6_threaded_omni_pivot()

        # FASE 7: AI & VISUALIZATION
        self._log("FASE 7: Finalizing Intelligence Models (AI, Graph & GEOINT)", "INFO")
        self._phase_7_finalize_models()

        # FASE 8: Archiving
        self._phase_8_archive()
        
        self._log("MISSION COMPLETE. Orchestrator Disengaging.", "SUCCESS")
        return {"status": "success", "target": self.target_name, "pool": self.intel_pool}

    # =========================================================================
    # DE 8 DRIFTSFASER
    # =========================================================================

    def _phase_0_historical_lake(self):
        """Tjekker OmniDataLake for historiske spor."""
        self._log("FASE 0: Cross-referencing Target in OmniDataLake...", "INFO")
        records = datalake.query_cross_reference(self.target_name)
        if records:
            self._log(f"Found {len(records)} previous occurrences in Intelligence Database!", "SUCCESS", indent=1)
            for r in records[:3]:
                self._log(f"Past Entry -> Date: {r['timestamp']} | Source: {r['source_module']}", "WARN", indent=2)

    def _phase_1_generate_permutations(self):
        """Genererer aliaser til brug i Dorking."""
        parts = self.target_name.lower().split()
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            yr = str(datetime.now().year)[-2:] 
            aliases = [f"{f}{l}", f"{f}.{l}", f"{f[0]}{l}", f"{f}{l[0]}", f"{f}_{l}", f"{f}{l}123", f"{f}{l}{yr}"]
            for a in aliases: self.intel_pool["Gættede_Aliaser"].add(a)

    def _phase_2_recursive_dorking(self, driver, target: str, current_depth: int):
        """Udfører Clearnet Dorking og Auto-Pivoterer på nye fund."""
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

        # Parallel dorking
        def run_dork(q):
            try: return omni_dork_search(driver, q, max_links=4)
            except Exception: return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_dork, q) for q in queries]
            for future in concurrent.futures.as_completed(futures):
                hits = future.result()
                for hit in hits:
                    u = hit.get('url', '')
                    if u and not any(d in u for d in self.noise_domains):
                        all_hits.append(hit)
                        collected_text += f" {hit.get('title','')} {hit.get('snippet','')}"

        # Ekstrahering via The Forge (Fase 15 Utils)
        iocs = ThreatIntelExtractor.extract_all(collected_text)
        danish_phones = ThreatIntelExtractor.extract_danish_phones(collected_text)
        
        self._ingest_iocs(iocs, danish_phones, all_hits, target)

        # RECURSIVE TRIGGER: Hvis vi finder nye mails/telefoner
        new_targets = []
        for em in iocs.get("email", []):
            if em.lower() not in self.seen_targets and self.target_name.lower() not in em.lower():
                new_targets.append(em.lower())
                self.seen_targets.add(em.lower())
                
        for ph in list(danish_phones)[:2]:
            if ph not in self.seen_targets:
                new_targets.append(ph)
                self.seen_targets.add(ph)

        # Pivoter på maks 3 nye spor per dybde for at undgå API bans
        for nt in new_targets[:3]:
            self._log(f"Auto-Pivot Triggered on new identifier: {nt}", "SUCCESS", indent=current_depth+1)
            self._phase_2_recursive_dorking(driver, nt, current_depth + 1)

    def _ingest_iocs(self, iocs: Dict, phones: Set[str], hits: List[Dict], source_target: str):
        """Hælder alle fundne IOCs ned i den globale Intel Pool og Nexus Grafen."""
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
                if any(x in url for x in ["github.com", "reddit.com"]): self.intel_pool["GitHub_Reddit_Spor"].add(url)
                if url.lower().endswith(('.pdf', '.docx', '.xls', '.txt')): self.intel_pool["Eksponerede_Dokumenter"].add(url)

            # NEXUS GRAPH INGESTION
            if nexus:
                for e in iocs.get("email", []):
                    nexus.ingest(EntityType.EMAIL, e, source=f"Dorking:{source_target}", confidence=0.8)
                    nexus.link(self.target_name, e, "Tilknyttet Email")
                for p in phones:
                    nexus.ingest(EntityType.PHONE, p, source=f"Dorking:{source_target}", confidence=0.8)
                    nexus.link(self.target_name, p, "Tilknyttet Tlf")

    def _phase_3_virk_pivot(self, driver, url):
        """Scraper virksomhedsdata."""
        if "person" in url and "deltager" not in url: url = url.rstrip('/') + "/deltager"
        if safe_get_with_retry(driver, url):
            try:
                from selenium.webdriver.common.by import By
                rows = driver.find_elements(By.CSS_SELECTOR, "tr, div.address")
                for r in rows:
                    if any(x in r.text for x in ["Bopæl", "Vej", "Adresse", "Postnr"]):
                        clean_addr = r.text.replace("\n", " | ")
                        self.intel_pool["Tidslinje_Bopæl"].append(clean_addr)
            except Exception: pass

    def _phase_4_darknet_recon(self, driver):
        """Tjekker target og e-mails mod pastebins og darkweb indexere."""
        targets = [self.target_name] + list(self.intel_pool["Fundne_Emails"])[:2]
        for t in targets:
            ahmia_url = f"https://ahmia.fi/search/?q={urllib.parse.quote(t)}"
            if safe_get_with_retry(driver, ahmia_url):
                if "No results" not in driver.page_source:
                    self._log(f"Darknet hits verified for indicator: {t}", "WARN", indent=1)
                    
            # Pastebin Dork Pivot
            dork = f'site:pastebin.com OR site:trello.com "{t}"'
            for h in omni_dork_search(driver, dork, max_links=2):
                self.intel_pool["Eksponerede_Dokumenter"].add(h.get('url'))

    def _phase_5_confidence_scoring(self):
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

    def _phase_6_threaded_omni_pivot(self):
        """Eksekverer sekundære moduler parallelt for at berige fundne datapunkter."""
        def run_api_module(module_class, target, kwargs=None):
            try:
                self._log(f"Firing {module_class.__name__} against {target}", "PIVOT", indent=1)
                instance = module_class(target, **(kwargs or {}))
                instance.run(None)
            except Exception as e: self._log(f"{module_class.__name__} failed: {e}", "ERROR", indent=2)

        def run_browser_module(module_class, target, kwargs=None):
            driver = None
            try:
                self._log(f"Spooling Sandbox WebDriver for {module_class.__name__} -> {target}", "PIVOT", indent=1)
                driver = get_stealth_driver()
                instance = module_class(target, **(kwargs or {}))
                instance.run(driver)
            except Exception as e: self._log(f"{module_class.__name__} failed: {e}", "ERROR", indent=2)
            finally:
                if driver: driver.quit()

        api_tasks, browser_tasks = [], []

        # Tildel API Tasks (Lynhurtige)
        for handle in list(self.intel_pool["Fundne_Brugernavne"])[:3]: api_tasks.append((MatrixAnalyzer, handle, {}))
        for ip in list(self.intel_pool["IP_Adresser"])[:2]: api_tasks.append((IPNetworkAnalyzer, ip, {}))
        for wallet in list(self.intel_pool["Kryptovaluta_Wallets"])[:2]:
            api_tasks.append((CryptoLedgerAnalyzer, wallet.split(": ")[1] if ": " in wallet else wallet, {}))
        for mac in list(self.intel_pool["MAC_Adresser"])[:2]: api_tasks.append((BSSIDGeofencer, mac, {}))
        for doc in list(self.intel_pool["Eksponerede_Dokumenter"])[:2]: api_tasks.append((WaybackMachineIntelligence, doc, {}))

        # Tildel Browser Tasks (Tunge)
        browser_tasks.append((BusinessIntelligenceAnalyst, self.target_name, {}))
        for email in list(self.intel_pool["Fundne_Emails"])[:2]: browser_tasks.append((BreachIntelligenceAnalyst, email, {}))
        for handle in list(self.intel_pool["Fundne_Brugernavne"])[:2]: browser_tasks.append((SocialMediaProfiler, handle, {}))
        for phone in list(self.intel_pool["Telefonnumre"])[:2]: browser_tasks.append((ReversePhoneIntelligence, phone, {}))
        for regnr in list(self.intel_pool["Nummerplader"])[:2]: browser_tasks.append((VehicleIntelligence, regnr, {}))

        # Kør API Tasks Parallelt
        if api_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(run_api_module, cls, tgt, kw) for cls, tgt, kw in api_tasks]
                concurrent.futures.wait(futures)

        # Kør Browser Tasks Parallelt
        if browser_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(run_browser_module, cls, tgt, kw) for cls, tgt, kw in browser_tasks]
                concurrent.futures.wait(futures)

    def _phase_7_finalize_models(self):§
        """Kører Wordlist, AI og Graph generation sekventielt."""
        try:
            email_seed = list(self.intel_pool["Fundne_Emails"])[0] if self.intel_pool["Fundne_Emails"] else ""
            cpr_seed = list(self.intel_pool["CPR_Fragments"])[0] if self.intel_pool["CPR_Fragments"] else ""
            clues = ",".join(self.intel_pool["Fundne_Brugernavne"])
            SniperModule(name=self.target_name, email=email_seed, cpr=cpr_seed, clues=clues).run(None)
        except Exception: pass

        try:
            self._log("Processing Context via Local LLM (Titan AI)...", "INFO", indent=1)
            TitanAIEnrichment().analyze_text(json.dumps(list(self.intel_pool.items()), default=str))
        except Exception: pass

        try:
            self._log("Generating Relational Graphs & KML...", "INFO", indent=1)
            GoliathGraphExporter().generate()
            GoogleEarthExporter().generate()
        except Exception: pass

    def _phase_8_archive(self):
        """Gemmer til Secure Data Lake og lokalt JSON."""
        # Data Lake Ingestion
        datalake.ingest(source_module=self.name, target=self.target_name, data=self.intel_pool)
        
        # Flad Fil Eksport
        export_data = self.intel_pool.copy()
        for key in export_data:
            if isinstance(export_data[key], set):
                export_data[key] = list(export_data[key])
                
        ws_folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(ws_folder, exist_ok=True)
        path = Path(ws_folder) / f"30_JUGGERNAUT_{sanitize_filename(self.target_name)}.json"
        
        path.write_text(json.dumps(export_data, indent=4, ensure_ascii=False), encoding="utf-8")
        self._log(f"Master Intelligence Profile archived: {path}", "SUCCESS")