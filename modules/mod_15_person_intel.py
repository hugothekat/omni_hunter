# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V39: THE APEX JUGGERNAUT ORCHESTRATOR (PET/FE EDITION)
📌 Formål: Total Identity Resolution, Breach Hunting, Async Enumeration & Pydantic Scoring.
OPERATIONAL SPECIFICATIONS:
- Pydantic Multi-Dimensional Confidence Scoring (Identity, Exposure, Footprint, Physical).
- Phase 1: Asynchronous SMTP MX Email Generation & Validation.
- Phase 2.5: Danish Gov Dorking (Statstidende, Tinglysning).
- Phase 2.6: NATIVE Directory & Property Intel (Krak, DinGeo, BBR).
- Phase 2.8: Async Social Media Enumeration (Sherlock-style integration).
- Phase 4: Integrated Breach API Matrix & Darknet Recon.
- Threaded Omni-Pivot & Historical Data Lake Correlation.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import time
import json
import os
import re
import random
import urllib.parse
import threading
import concurrent.futures
import smtplib
import dns.resolver
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from enum import Enum

from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, ThreatIntelExtractor, datalake, sanitize_filename, extract_danish_phones, validate_danish_address
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

try:
    from modules.mod_06_ip import OmniInfrastructureTracker as IPNetworkAnalyzer
except ImportError:
    IPNetworkAnalyzer = None

# =========================================================================
# ADVANCED PYDANTIC SCORING MODELS (INTELLIGENCE GRADE)
# =========================================================================
class DataType(str, Enum):
    CREDENTIALS = "credentials"
    PII = "PII"
    FINANCIAL = "financial_data"
    MEDICAL = "medical_data"
    SOCIAL = "social_media"
    GEOINT = "geospatial_data"

class BreachSeverity(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    rationale: List[str]

class IntelligenceScores(BaseModel):
    identity_confidence: float = Field(..., ge=0.0, le=1.0)
    exposure_threat: float = Field(..., ge=0.0, le=1.0)
    digital_footprint: float = Field(..., ge=0.0, le=1.0)
    physical_trace: float = Field(..., ge=0.0, le=1.0)
    overall_threat_index: float = Field(..., ge=0.0, le=1.0)
    intelligence_grade: str

def calculate_breach_severity(breach_data: Dict) -> BreachSeverity:
    """Beregner severity-score for et specifikt datalæk baseret på PET-FE metrikker."""
    severity_weights = {
        DataType.CREDENTIALS: 0.9,
        DataType.PII: 0.7,
        DataType.FINANCIAL: 0.8,
        DataType.MEDICAL: 0.6,
        DataType.SOCIAL: 0.5,
        DataType.GEOINT: 0.75
    }

    base_score = severity_weights.get(DataType(breach_data.get("data_type", "PII")), 0.5)
    breach_count = breach_data.get("breach_count", 1)
    count_multiplier = min(1.0, breach_count * 0.1)

    source = breach_data.get("source", "clearnet")
    source_weights = {"darkweb": 1.2, "underground": 1.3, "clearnet": 1.0}
    source_multiplier = source_weights.get(source, 1.0)

    final_score = min(1.0, base_score * count_multiplier * source_multiplier)
    rationale = [
        f"Base score: {base_score:.2f} (type={breach_data.get('data_type', 'PII')})",
        f"Count multiplier: {count_multiplier:.2f} (count={breach_count})",
        f"Source multiplier: {source_multiplier:.2f} (source={source})",
    ]
    return BreachSeverity(score=final_score, rationale=rationale)

def calculate_intelligence_matrix(intel_data: Dict) -> IntelligenceScores:
    """Beregner den overordnede multi-dimensionelle GOLIATH Intelligence Grade."""
    # 1. Identity Confidence
    id_score = 0.0
    if intel_data.get("Fundne_Emails"): id_score += 0.4
    if intel_data.get("Telefonnumre"): id_score += 0.3
    if intel_data.get("CPR_Fragments"): id_score += 0.3
    if intel_data.get("Nummerplader"): id_score += 0.1
    id_score = min(1.0, id_score)

    # 2. Exposure Threat
    exp_score = 0.0
    breaches = intel_data.get("Scored_Breaches", [])
    if breaches:
        breach_severity = sum(b.get("severity", {}).get("score", 0) for b in breaches) / len(breaches)
        exp_score = min(1.0, breach_severity * 0.8)
    if intel_data.get("Darkweb_Spor"): exp_score = min(1.0, exp_score + 0.3)

    # 3. Digital Footprint (Opgraderet til at inddrage Async Enumeration)
    footprint = 0.0
    if intel_data.get("Footprint_Spor") or intel_data.get("Fundne_Brugernavne"): footprint += 0.4
    if intel_data.get("Verified_Social_Profiles"): footprint += 0.4 # Ekstra point for rigtige profiler
    if intel_data.get("Kryptovaluta_Wallets"): footprint += 0.3
    if intel_data.get("Eksponerede_Dokumenter"): footprint += 0.2
    footprint = min(1.0, footprint)

    # 4. Physical Trace
    physical = 0.0
    if intel_data.get("Virk_Links"): physical += 0.4
    if intel_data.get("Tidslinje_Bopæl"): physical += 0.5
    if intel_data.get("Netværk_Associates"): physical += 0.2
    
    # NYT V39: Point for fysisk ejendoms-bekræftelse og bofæller
    ejendom = intel_data.get("Ejendom", {})
    if ejendom.get("Vej"): physical += 0.3
    if intel_data.get("DinGeo_Intelligence", {}).get("BBR_Stamdata"): physical += 0.2
    if intel_data.get("Bofæller_Netværk"): physical += 0.2
    
    physical = min(1.0, physical)

    # Overall Index
    overall = (id_score * 0.4) + (exp_score * 0.3) + (footprint * 0.15) + (physical * 0.15)
    
    # Intelligence Grade
    grade = "F"
    if overall >= 0.85: grade = "A"
    elif overall >= 0.70: grade = "B"
    elif overall >= 0.50: grade = "C"
    elif overall >= 0.30: grade = "D"

    return IntelligenceScores(
        identity_confidence=id_score,
        exposure_threat=exp_score,
        digital_footprint=footprint,
        physical_trace=physical,
        overall_threat_index=overall,
        intelligence_grade=grade
    )

# =========================================================================
# THE APEX JUGGERNAUT CORE
# =========================================================================
class AutonomousOrchestrator(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.name = "APEX ORCHESTRATOR (Identity Resolution, Async Enum & Omni-Pivot)"
        self.description = "Autonom 10-faset identitets-kortlægning, SMTP validering og Pydantic Matrix."
        self.category = ModuleCategory.PERSON
        self.print_lock = threading.Lock()
        
        self.target_name: str = ""
        self.target_domain: str = ""
        self.max_recursion_depth: int = 2
        self.seen_targets: Set[str] = set()
        self.noise_domains = ["microsoft.com", "outlook.office", "support.google", "login.live", "wikipedia.org", "eniro.dk"]
        
        self.hibp_key = CONFIG.get("api_keys", {}).get("hibp_api_key", "")
        
        self.intel_pool: Dict[str, Any] = {
            "Mål": "",
            "Domæne": "",
            "Genererede_Aliaser": set(),
            "Fundne_Emails": set(),
            "Fundne_Brugernavne": set(),
            "Verified_Social_Profiles": [], # NY V39: Async Enumeration resultater
            "Telefonnumre": set(),
            "Nummerplader": set(),
            "MAC_Adresser": set(),
            "Virk_Links": set(),
            "Eksponerede_Dokumenter": set(),
            "Kryptovaluta_Wallets": set(),
            "IP_Adresser": set(),
            "CPR_Fragments": set(),
            "Tidslinje_Bopæl": set(),
            "Netværk_Associates": set(),
            
            "Ejendom": {
                "Vej": "",
                "Post": "",
                "By": "",
                "Type": "Ukendt",
                "Koordinater": "",
                "Historik": []
            },
            "DinGeo_Intelligence": {
                "BBR_Stamdata": {}, "Vurdering": {}, "Skat": {}, 
                "Infrastruktur": {}, "Historiske_Vurderinger": []
            },
            "Bofæller_Netværk": set(),
            
            "Breach_Data": {
                "Total_Verified_Breaches": 0,
                "Lækkede_Passwords_Fundet": False,
                "Breach_Sources": set(),
                "Eksponerede_Data_Typer": set(),
                "Verified_Databases": {"HIBP": [], "XposedOrNot": [], "BreachDirectory": [], "LeakCheck": []}
            },
            "Scored_Breaches": [],
            
            "Underground_Syndicates": {
                "Hacker_Forums": set(), "Paste_Dumps": set(), "GitHub_GitLab_Dev": set(),
                "Telegram_Channels": set(), "Cloud_Trello_Docs": set(), "Reddit_Dox_Mentions": set(), "Infostealer_Logs": set()
            },
            "Footprint_Spor": set(),
            "Darkweb_Spor": set(),
            
            "Intelligence_Matrix": {}, 
            "Metadata": {
                "Timestamp": datetime.now().isoformat(),
                "Software": "GOLIATH V39 APEX JUGGERNAUT ORCHESTRATOR"
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
        raw_input = target.strip() if target else session.get("name", "")
        if not raw_input:
            self._log("Ingen target angivet. Afbryder.", "ERROR")
            return self.data

        if "," in raw_input:
            parts = raw_input.split(",")
            self.target_name = parts[0].strip()
            self.target_domain = parts[1].strip().replace("@", "")
        else:
            self.target_name = raw_input

        self.intel_pool["Mål"] = self.target_name
        self.intel_pool["Domæne"] = self.target_domain
        self.seen_targets.add(self.target_name.lower())
        
        print(f"\n{C.BG_RED}{C.WHITE} === THE APEX JUGGERNAUT ORCHESTRATOR V39 ENGAGED === {C.RESET}\n")
        self._log(f"Initiating Identity Sequence for: {self.target_name} (Domain: {self.target_domain or 'N/A'})", "INFO")

        self._phase_0_historical_lake()
        self._phase_1_generate_and_smtp_validate()
        self._log("FASE 2: Executing Recursive Clearnet Intelligence Sweep...", "INFO")
        self._phase_2_recursive_dorking(driver, self.target_name, current_depth=0)

        self._log("FASE 2.6: Executing Native Directory & Property Intel (DinGeo/Krak)...", "INFO")
        self._phase_2_6_directory_property_intelligence(driver)

        # FASE 2.8: NATIVE ASYNC SOCIAL ENUMERATION
        self._log("FASE 2.8: Executing Async Username Enumeration (Sherlock-Protocol)...", "INFO")
        self._phase_2_8_async_social_enumeration()

        if self.intel_pool["Virk_Links"]:
            self._log("FASE 3: Extracting historical residency & associate data (CVR/Virk)...", "INFO")
            for link in list(self.intel_pool["Virk_Links"])[:3]: 
                self._phase_3_virk_pivot(driver, link)

        if self.intel_pool["Fundne_Emails"]:
            self._log("FASE 4: INITIATING NATIVE BREACH & FOOTPRINT AUDIT", "CRITICAL")
            self._phase_4_breach_and_footprint(driver)
        else:
            self._log("Ingen emails fundet. Bypasser Breach Audit.", "WARN")

        self._phase_5_pydantic_scoring()
        self._print_intel_summary()

        self._log("FASE 6: INITIATING PARALLEL OMNI-PIVOT ENGINE", "SUCCESS")
        self._phase_6_threaded_omni_pivot(driver)

        self._log("FASE 7: Finalizing Intelligence Models (AI, Graph & GEOINT)", "INFO")
        self._phase_7_finalize_models()
        self._phase_8_archive()
        
        self._log("MISSION COMPLETE. Apex Orchestrator Disengaging.", "SUCCESS")
        return self.intel_pool

    # =========================================================================
    # FASE 1: NATIVE EMAIL GENERATION & SMTP VALIDATION 
    # =========================================================================
    def _phase_0_historical_lake(self) -> None:
        self._log("FASE 0: Cross-referencing Target in OmniDataLake...", "INFO")
        try:
            if hasattr(datalake, 'query_cross_reference'):
                records = datalake.query_cross_reference(self.target_name)
                if records:
                    self._log(f"Found {len(records)} previous occurrences in Intelligence Database!", "SUCCESS", indent=1)
        except Exception: pass

    def _phase_1_generate_and_smtp_validate(self) -> None:
        self._log("FASE 1: Generating Permutations & SMTP Verification...", "INFO")
        
        parts = self.target_name.lower().split()
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            yr = str(datetime.now().year)[-2:] 
            aliases = [f"{f}{l}", f"{f}.{l}", f"{f[0]}{l}", f"{f}{l[0]}", f"{f}_{l}", f"{f}{l}123", f"{f}{l}{yr}", f"{f}{l}88", f"{f}{l}99"]
            for a in aliases: self.intel_pool["Genererede_Aliaser"].add(a)

        if self.target_domain and len(parts) >= 2:
            self._log(f"Resolving MX Records for {self.target_domain}...", "PIVOT", indent=1)
            f, l = parts[0], parts[-1]
            patterns = [
                f"{f}@{self.target_domain}", f"{l}@{self.target_domain}", f"{f}.{l}@{self.target_domain}",
                f"{f[0]}{l}@{self.target_domain}", f"{f}{l[0]}@{self.target_domain}", f"{f[0]}.{l}@{self.target_domain}",
                f"kontakt@{self.target_domain}", f"info@{self.target_domain}"
            ]
            
            try:
                records = dns.resolver.resolve(self.target_domain, 'MX')
                mx_record = str(records[0].exchange)
                
                def _verify_smtp(email: str):
                    try:
                        time.sleep(random.uniform(0.1, 0.5)) 
                        server = smtplib.SMTP(timeout=4)
                        server.connect(mx_record)
                        server.helo(server.local_hostname)
                        server.mail('admin@google.com')
                        code, _ = server.rcpt(email)
                        server.quit()
                        if code == 250:
                            with self.print_lock:
                                self.intel_pool["Fundne_Emails"].add(email)
                                self._log(f"SMTP HIT: {email} exists on server!", "SUCCESS", indent=2)
                    except Exception: pass

                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(_verify_smtp, mail) for mail in patterns]
                    concurrent.futures.wait(futures)
            except Exception as e:
                self._log(f"MX Resolution failed for {self.target_domain}: {e}", "WARN", indent=1)

    # =========================================================================
    # FASE 2 & 2.8: RECURSIVE DORKING & ASYNC SOCIAL ENUMERATION
    # =========================================================================
    def _phase_2_recursive_dorking(self, driver: Any, target: str, current_depth: int) -> None:
        if current_depth > self.max_recursion_depth: return
        self._log(f"[DEPTH {current_depth}] Sweeping vectors for: {target}", "PIVOT", indent=current_depth)

        queries = [
            f'"{target}"', 
            f'"{target}" @gmail.com OR @hotmail.com OR @icloud.com',
            f'"{target}" site:instagram.com OR site:tiktok.com OR site:linkedin.com',
            f'"{target}" site:github.com OR site:reddit.com OR site:pastebin.com',
            f'"{target}" site:virk.dk OR site:proff.dk OR site:ownr.dk',
            f'"{target}" site:tinglysning.dk OR site:statstidende.dk', 
            f'"{target}" ext:pdf OR ext:docx OR ext:xls OR ext:txt'
        ]
        
        if self.target_domain: queries.append(f'"{target}" "{self.target_domain}"')

        all_hits, collected_text = [], ""

        def run_dork(q: str) -> List[Dict]:
            try: return omni_dork_search(driver, q, max_links=4)
            except Exception: return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
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

    # =========================================================================
    # FASE 2.6: NATIVE DIRECTORY & PROPERTY INTELLIGENCE (Modul 01 Fusion)
    # =========================================================================
    def _phase_2_6_directory_property_intelligence(self, driver: Any) -> None:
        """Indsamler adresse og slår op i DinGeo og Krak."""
        if not driver: return
        
        self._log("Striking Krak & DeGuleSider via SERP...", "INFO", indent=1)
        self._google_serp_directory_strike(driver)
        self._bing_directory_dork(driver)
        
        if self.intel_pool["Ejendom"].get("Vej"):
            addr = f"{self.intel_pool['Ejendom']['Vej']}, {self.intel_pool['Ejendom']['Post']} {self.intel_pool['Ejendom']['By']}"
            self._log(f"Address Confirmed: {addr}. Executing Async DinGeo Deep-Audit...", "PIVOT", indent=1)
            
            encoded = urllib.parse.quote(addr)
            self.intel_pool["Ejendom"]["Koordinater"] = f"https://www.google.com/maps/search/?api=1&query={encoded}"
            
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running(): 
                    loop.run_until_complete(self._async_property_audit(driver))
            except Exception as e:
                self._log(f"Async Property Audit Error: {e}", "WARN", indent=2)

    def _google_serp_directory_strike(self, driver):
        query = f'site:krak.dk OR site:degulesider.dk "{self.target_name}" ejendom OR bolig'
        url = f"https://www.google.dk/search?q={urllib.parse.quote(query)}"
        try:
            driver.get(url)
            time.sleep(2)
            elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
            for el in elements:
                text = el.text
                phones = extract_danish_phones(text)
                for p in phones:
                    formatted = f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}"
                    self.intel_pool["Telefonnumre"].add(formatted)

                match = validate_danish_address(text)
                if match and not self.intel_pool["Ejendom"].get("Vej"):
                    with self.print_lock:
                        self.intel_pool["Ejendom"]["Vej"] = match["vej"]
                        self.intel_pool["Ejendom"]["Post"] = match["post"]
                        self.intel_pool["Ejendom"]["By"] = match["by"]
                        self.intel_pool["Ejendom"]["Historik"].append({"source": "Google SERP", "address": match["full"]})
        except Exception: pass

    def _bing_directory_dork(self, driver):
        dork = f'(site:krak.dk OR site:degulesider.dk) "{self.target_name}"'
        hits = omni_dork_search(driver, dork, max_links=4)
        for hit in hits:
            full_text = f"{hit.get('title','')} {hit.get('snippet','')}"
            phones = extract_danish_phones(full_text)
            for p in phones:
                formatted = f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}"
                self.intel_pool["Telefonnumre"].add(formatted)

            match = validate_danish_address(full_text)
            if match and not self.intel_pool["Ejendom"].get("Vej"):
                with self.print_lock:
                    self.intel_pool["Ejendom"]["Vej"] = match["vej"]
                    self.intel_pool["Ejendom"]["Post"] = match["post"]
                    self.intel_pool["Ejendom"]["By"] = match["by"]
                    self.intel_pool["Ejendom"]["Historik"].append({"source": "Bing", "address": match["full"]})

    async def _async_property_audit(self, driver):
        vej_clean = self.intel_pool["Ejendom"]["Vej"].split(',')[0].strip()
        post = self.intel_pool["Ejendom"]["Post"]
        by_clean = self.intel_pool["Ejendom"]["By"].split(' ')[0].strip()

        slug_c = f"{post}-{by_clean}".lower()
        slug_v = re.sub(r'[^a-z0-9æøå\-]', '', vej_clean.replace(" ", "-").replace("æ","ae").replace("ø","oe").replace("å","aa"))
        base = f"https://www.dingeo.dk/adresse/{slug_c}/{slug_v}"

        endpoints = {
            "BBR_Stamdata": {"path": "", "parser": self._parse_bbr_data},
            "Skat": {"path": "/skat/", "parser": self._parse_skat_data},
            "Vurdering": {"path": "/vurdering/", "parser": self._parse_vurdering_data},
            "Infrastruktur": {"path": "/internet-mobil/", "parser": self._parse_infrastructure}
        }

        async with aiohttp.ClientSession() as http_session:
            tasks = []
            for key, config in endpoints.items():
                tasks.append(self._fetch_dingeo_endpoint(http_session, base + config["path"], config["parser"], key))
            await asyncio.gather(*tasks)
            
        # Find bofæller via asynkron trådpool wrapper
        loop = asyncio.get_event_loop()
        query = f'site:krak.dk "{vej_clean}" "{post}"'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            try:
                hits = await loop.run_in_executor(executor, lambda: omni_dork_search(driver, query, max_links=4))
                for hit in hits:
                    name = hit.get('title', '').split('-')[0].strip()
                    if name and self.target_name.lower() not in name.lower() and "Krak" not in name:
                        self.intel_pool["Bofæller_Netværk"].add(name)
            except Exception: pass

    async def _fetch_dingeo_endpoint(self, http_session, url, parser, data_key):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        for _ in range(2):
            try:
                async with http_session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        await parser(html, data_key)
                        break
            except Exception: await asyncio.sleep(1)

    async def _parse_bbr_data(self, html: str, data_key: str):
        soup = BeautifulSoup(html, 'html.parser')
        for row in soup.select('table.bbr-data tr, tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).replace(':', '')
                if key in ["Opførselsesår", "Antal værelser", "Etageareal", "Boligtype", "Varmeinstallation"]:
                    self.intel_pool["DinGeo_Intelligence"][data_key][key] = cells[1].get_text(strip=True)

    async def _parse_skat_data(self, html: str, data_key: str):
        m = re.search(r'Boligskat.*?(?:2024)?[:\s]*([0-9\.]+)\s*kr', BeautifulSoup(html, 'html.parser').get_text())
        if m: self.intel_pool["DinGeo_Intelligence"][data_key]["Boligskat"] = m.group(1)

    async def _parse_vurdering_data(self, html: str, data_key: str):
        text = BeautifulSoup(html, 'html.parser').get_text()
        m = re.search(r'Dingestimat[:\s]*([0-9\.]+)\s*kr', text, re.IGNORECASE)
        m2 = re.search(r'Seneste salgspris[:\s]*([0-9\.]+)\s*kr', text, re.IGNORECASE)
        if m: self.intel_pool["DinGeo_Intelligence"][data_key]["Dingestimat"] = m.group(1)
        if m2: self.intel_pool["DinGeo_Intelligence"][data_key]["Seneste_Salg"] = m2.group(1)

    async def _parse_infrastructure(self, html: str, data_key: str):
        if "fibernet" in html.lower(): self.intel_pool["DinGeo_Intelligence"][data_key]["Fiber"] = "Ja"
        if "5g" in html.lower(): self.intel_pool["DinGeo_Intelligence"][data_key]["5G"] = "Ja"

    def _phase_2_8_async_social_enumeration(self) -> None:
        """Kører et 'Sherlock'-style asynkront tjek på alle aliaser/usernames på tværs af sociale medier."""
        # Saml alle potentielle brugernavne og aliaser
        potential_usernames = list(self.intel_pool["Genererede_Aliaser"].union(self.intel_pool["Fundne_Brugernavne"]))
        if not potential_usernames: return
        
        # Max 10 brugernavne for at holde performance i top
        potential_usernames = potential_usernames[:10]
        
        social_platforms = {
            "GitHub": "https://github.com/{}",
            "Reddit": "https://www.reddit.com/user/{}",
            "Twitter": "https://nitter.net/{}", # Bruger Nitter proxy for at undgå X login-wall
            "Instagram": "https://www.instagram.com/{}/",
            "Pinterest": "https://www.pinterest.com/{}/",
            "Vimeo": "https://open.spotify.com/user/{}", # Spotify wrapper
            "Patreon": "https://www.patreon.com/{}"
        }

        async def check_profile(session: aiohttp.ClientSession, platform: str, url: str, username: str):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            try:
                async with session.get(url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        # Dobbelt-tjek mod false positives (nogle sider returnerer 200 for 404 sider)
                        text = await response.text()
                        if "not found" not in text.lower() and "doesn't exist" not in text.lower():
                            with self.print_lock:
                                profile = {"platform": platform, "url": url, "username": username}
                                self.intel_pool["Verified_Social_Profiles"].append(profile)
                                self._log(f"Active Profile Found: {platform} -> {username}", "SUCCESS", indent=2)
            except Exception: pass

        async def run_async_enum():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for username in potential_usernames:
                    for platform, url_template in social_platforms.items():
                        url = url_template.format(username)
                        tasks.append(check_profile(session, platform, url, username))
                await asyncio.gather(*tasks)

        # Kør asynkron event loop
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running(): loop.run_until_complete(run_async_enum())
        except Exception as e:
            self._log(f"Async Enumeration Error: {e}", "WARN", indent=1)

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
                if any(x in url for x in ["virk.dk", "ownr.dk", "proff.dk", "statstidende.dk", "tinglysning.dk"]): 
                    self.intel_pool["Virk_Links"].add(url)
                if url.lower().endswith(('.pdf', '.docx', '.xls', '.txt')): 
                    self.intel_pool["Eksponerede_Dokumenter"].add(url)

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
                rows = driver.find_elements(By.CSS_SELECTOR, "tr, div.address, a.name")
                for r in rows:
                    txt = r.text.strip()
                    if any(x in txt for x in ["Bopæl", "Vej", "Adresse", "Postnr"]):
                        clean_addr = txt.replace("\n", " | ")
                        self.intel_pool["Tidslinje_Bopæl"].add(clean_addr)
                        self._log(f"Bopæl Udtrukket: {clean_addr}", "SUCCESS", indent=2)
                    elif len(txt) > 5 and not any(char.isdigit() for char in txt) and self.target_name.lower() not in txt.lower():
                        if "A/S" not in txt and "ApS" not in txt: 
                            self.intel_pool["Netværk_Associates"].add(txt)
            except Exception: pass

    # =========================================================================
    # NATIVE FASE 4: BREACH, FOOTPRINT & DARKWEB
    # =========================================================================
    def _phase_4_breach_and_footprint(self, driver: Any) -> None:
        emails_to_check = list(self.intel_pool["Fundne_Emails"])[:3]
        for email in emails_to_check:
            self._log(f"Auditing Identity Vector: {email}", "PIVOT", indent=1)
            self._execute_async_breach_apis(email)
            
            if self.hibp_key: self._query_hibp_api(email)
            elif driver: self._scrape_hibp_frontend(driver, email)
            
            if driver:
                self._execute_footprint_dorks(driver, email)
                self._darkweb_ahmia_scrape(driver, email)

    def _register_breach(self, email: str, name: str, source_type: str = "clearnet", data_type: str = "PII"):
        with self.print_lock:
            self.intel_pool["Breach_Data"]["Breach_Sources"].add(name)
            self.intel_pool["Scored_Breaches"].append({
                "source": source_type, "data_type": data_type, "breach_name": name, "breach_count": 1 
            })

    def _execute_async_breach_apis(self, email: str):
        def _xon():
            try:
                res = http.get(f"https://api.xposedornot.com/v1/checkbacklink?email={email}", timeout=10)
                if res.status_code == 200:
                    breaches = res.json().get("Breaches", [])
                    if breaches:
                        self._log(f"XposedOrNot confirmed {len(breaches)} breaches for {email}", "CRITICAL", indent=2)
                        for b in breaches:
                            name = b[0] if isinstance(b, list) else b
                            self.intel_pool["Breach_Data"]["Verified_Databases"]["XposedOrNot"].append(name)
                            self._register_breach(email, name, "clearnet", "credentials")
            except Exception: pass

        def _bd():
            try:
                res = http.get(f"https://breachdirectory.org/api/search?key=free&term={email}", timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("success") and data.get("found", 0) > 0:
                        self._log(f"BreachDirectory flagged {data.get('found')} exposed sources.", "CRITICAL", indent=2)
                        for src in data.get("sources", []):
                            name = src.get("name", "Unknown")
                            self.intel_pool["Breach_Data"]["Verified_Databases"]["BreachDirectory"].append(name)
                            self._register_breach(email, name, "underground", "credentials")
            except Exception: pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(_xon)
            executor.submit(_bd)

    def _query_hibp_api(self, email: str):
        headers = {"hibp-api-key": self.hibp_key, "user-agent": "PETFE-GOLIATH-OSINT"}
        try:
            res = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}?truncateResponse=false", headers=headers, timeout=10)
            if res.status_code == 200:
                breaches = res.json()
                self._log(f"HIBP API verified {len(breaches)} corporate breaches.", "CRITICAL", indent=2)
                for b in breaches:
                    b_name = b.get("Name", "Unknown")
                    self.intel_pool["Breach_Data"]["Verified_Databases"]["HIBP"].append(b_name)
                    
                    data_type = "PII"
                    for dc in b.get("DataClasses", []):
                        self.intel_pool["Breach_Data"]["Eksponerede_Data_Typer"].add(dc)
                        if "password" in dc.lower():
                            self.intel_pool["Breach_Data"]["Lækkede_Passwords_Fundet"] = True
                            data_type = "credentials"
                        elif any(x in dc.lower() for x in ["bank", "credit", "financial"]):
                            data_type = "financial_data"
                            
                    self._register_breach(email, b_name, "clearnet", data_type)
        except Exception: pass

    def _scrape_hibp_frontend(self, driver: Any, email: str):
        try:
            driver.get("https://haveibeenpwned.com/")
            time.sleep(3)
            search_box = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "Account")))
            search_box.clear()
            search_box.send_keys(email)
            search_box.send_keys(Keys.ENTER)
            time.sleep(4) 
            
            source = driver.page_source
            if "pwnedCompanyTitle" in source or "Oh no — pwned!" in source:
                breaches = driver.find_elements(By.CSS_SELECTOR, ".pwnedCompanyTitle")
                self._log(f"HIBP Live-Scraper verified {len(breaches)} breaches.", "CRITICAL", indent=2)
                for el in breaches:
                    b_name = el.text.strip()
                    if b_name:
                        self.intel_pool["Breach_Data"]["Verified_Databases"]["HIBP"].append(b_name)
                        self._register_breach(email, b_name, "clearnet", "credentials")
                        
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
            sys.stdout.write(f"\r{C.CYAN}    [*] Scannner Matrix: {cat_name}...      {C.RESET}")
            sys.stdout.flush()
            hits = omni_dork_search(driver, query, max_links=3)
            if hits:
                sys.stdout.write("\r" + " " * 80 + "\r")
                self._log(f"Fandt {len(hits)} spor i: {cat_name}", "CRITICAL" if "Footprint" not in cat_name else "SUCCESS", indent=2)
                with self.print_lock:
                    for h in hits:
                        if target_key == "Footprint_Spor":
                            self.intel_pool["Footprint_Spor"].add(h['url'])
                        else:
                            self.intel_pool["Underground_Syndicates"][target_key].add(h['url'])
                            self._register_breach(email, f"Underground Hit: {cat_name}", "underground", "credentials")
            time.sleep(random.uniform(1.0, 2.0))

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
                        self._register_breach(email, "Darkweb Mention", "darkweb", "credentials")
                except Exception: pass

    # =========================================================================
    # FASE 5: PYDANTIC SCORING & SUMMARY
    # =========================================================================
    def _phase_5_pydantic_scoring(self) -> None:
        """Kører den nye Pydantic-baserede Intelligence Grade model."""
        for breach in self.intel_pool["Scored_Breaches"]:
            sev_obj = calculate_breach_severity(breach)
            breach["severity"] = sev_obj.dict()

        conf_obj = calculate_intelligence_matrix(self.intel_pool)
        self.intel_pool["Intelligence_Matrix"] = conf_obj.dict()
        
        self.intel_pool["Confidence_Score"] = int(conf_obj.overall_threat_index * 100)
        self.intel_pool["Breach_Data"]["Total_Verified_Breaches"] = len(self.intel_pool["Breach_Data"]["Breach_Sources"])

    def _print_intel_summary(self) -> None:
        with self.print_lock:
            print(f"\n{C.CYAN}--- TACTICAL INTELLIGENCE SUMMARY: {self.target_name.upper()} ---{C.RESET}")
            
            score_data = self.intel_pool['Intelligence_Matrix']
            grade = score_data.get('intelligence_grade', 'F')
            grade_col = C.GREEN if grade in ["A", "B"] else (C.YELLOW if grade == "C" else C.RED)
            
            print(f"GOLIATH Grade:     {grade_col}GRADE {grade}{C.RESET} (Threat Index: {score_data.get('overall_threat_index', 0)*100:.1f}%)")
            print(f"Metrics (0-1):     ID:{score_data.get('identity_confidence',0):.2f} | EXP:{score_data.get('exposure_threat',0):.2f} | FTP:{score_data.get('digital_footprint',0):.2f} | PHY:{score_data.get('physical_trace',0):.2f}")
            print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")
            
            print(f"Usernames:       {C.WHITE}{', '.join(self.intel_pool['Fundne_Brugernavne'])}{C.RESET}")
            if self.intel_pool['Verified_Social_Profiles']:
                print(f"Social Profiles: {C.GREEN}{len(self.intel_pool['Verified_Social_Profiles'])} Verified Active Profiles{C.RESET}")
            print(f"Emails:          {C.WHITE}{', '.join(self.intel_pool['Fundne_Emails'])}{C.RESET}")
            print(f"Phones:          {C.WHITE}{', '.join(self.intel_pool['Telefonnumre'])}{C.RESET}")
            if self.intel_pool["Netværk_Associates"]:
                print(f"Associates:      {C.WHITE}{', '.join(list(self.intel_pool['Netværk_Associates'])[:5])}{C.RESET}")
            
            ejendom = self.intel_pool.get("Ejendom", {})
            if ejendom.get("Vej"):
                print(f"Address:         {C.WHITE}{ejendom['Vej']}, {ejendom['Post']} {ejendom['By']}{C.RESET}")
            bbr = self.intel_pool.get("DinGeo_Intelligence", {}).get("BBR_Stamdata", {})
            if bbr:
                print(f"BBR Info:        {C.WHITE}Opført {bbr.get('Opførselsesår','N/A')} | {bbr.get('Boligtype','N/A')} | {bbr.get('Etageareal','N/A')}{C.RESET}")
            if self.intel_pool.get("Bofæller_Netværk"):
                print(f"Cohabitants:     {C.WHITE}{', '.join(list(self.intel_pool['Bofæller_Netværk']))}{C.RESET}")

            b_total = self.intel_pool["Breach_Data"]["Total_Verified_Breaches"]
            if b_total > 0:
                print(f"Verified Breaches: {C.RED}{b_total} (Critical){C.RESET}")
                if self.intel_pool["Breach_Data"]["Lækkede_Passwords_Fundet"]:
                    print(f"Password Status:   {C.RED}COMPROMISED (Cleartext/Hash exposed){C.RESET}")
            
            ug_hits = sum(len(v) for v in self.intel_pool["Underground_Syndicates"].values())
            if ug_hits > 0: print(f"Underground Hits:  {C.RED}{ug_hits} (Forums, Pastes, Stealers){C.RESET}")
            if self.intel_pool["Darkweb_Spor"]: print(f"Darkweb Hits:      {C.RED}{len(self.intel_pool['Darkweb_Spor'])} (Tor Indexed){C.RESET}")
            
            print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")

    # =========================================================================
    # FASE 6 - 8: OMNI PIVOT & ARCHIVING
    # =========================================================================
    def _phase_6_threaded_omni_pivot(self, main_driver: Any) -> None:
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
        for handle in list(self.intel_pool["Fundne_Brugernavne"])[:2]: api_tasks.append(("mod_02_social", "SocialMediaProfiler", handle))
        for ip in list(self.intel_pool["IP_Adresser"])[:2]: api_tasks.append(("mod_06_ip", "IPNetworkAnalyzer", ip))
        # Note: mod_06_ip class name is OmniInfrastructureTracker in the provided context
        for ip in list(self.intel_pool["IP_Adresser"])[:1]: api_tasks.append(("mod_06_ip", "OmniInfrastructureTracker", ip))
        for wallet in list(self.intel_pool["Kryptovaluta_Wallets"])[:2]: 
            w_clean = wallet.split(": ")[1] if ": " in wallet else wallet
            api_tasks.append(("mod_19_crypto", "CryptoLedgerAnalyzer", w_clean))

        if api_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                for mod, cls, tgt in api_tasks:
                    if cls == "IPNetworkAnalyzer": cls = "OmniInfrastructureTracker"
                    executor.submit(_safe_run, mod, cls, tgt, None)

    def _phase_7_finalize_models(self) -> None:
        try:
            from modules.mod_12_ai import TitanAIEnrichment
            self._log("Processing Context via Local LLM (Titan AI)...", "INFO", indent=1)
            ai_mod = TitanAIEnrichment(self.target_name)
            
            clean_pool = {k: list(v) if isinstance(v, set) else v for k, v in self.intel_pool.items()}
            for k, v in clean_pool["Breach_Data"].items():
                if isinstance(v, set): clean_pool["Breach_Data"][k] = list(v)
            for k, v in clean_pool["Underground_Syndicates"].items():
                if isinstance(v, set): clean_pool["Underground_Syndicates"][k] = list(v)

            res = ai_mod.analyze_text(json.dumps(clean_pool, ensure_ascii=False))
            if res: self.intel_pool["AI_Assessment"] = res
        except Exception: pass

        try:
            from modules.mod_13_graph import GoliathGraphExporter
            from modules.mod_14_kml import GoogleEarthExporter
            self._log("Generating Relational Graphs & KML...", "INFO", indent=1)
            GoliathGraphExporter().generate()
            GoogleEarthExporter().generate()
        except Exception: pass

    def _phase_8_archive(self) -> None:
        for key in self.intel_pool:
            if isinstance(self.intel_pool[key], set): self.intel_pool[key] = list(self.intel_pool[key])
        for key in self.intel_pool["Breach_Data"]:
            if isinstance(self.intel_pool["Breach_Data"][key], set): self.intel_pool["Breach_Data"][key] = list(self.intel_pool["Breach_Data"][key])
        for key in self.intel_pool["Underground_Syndicates"]:
            if isinstance(self.intel_pool["Underground_Syndicates"][key], set): self.intel_pool["Underground_Syndicates"][key] = list(self.intel_pool["Underground_Syndicates"][key])

        datalake.ingest(source_module=self.name, target=self.target_name, data=self.intel_pool)
        
        ws_folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(ws_folder, exist_ok=True)
        path = Path(ws_folder) / f"30_ORCHESTRATOR_{sanitize_filename(self.target_name)}.json"
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
        path.write_text(json.dumps(self.intel_pool, indent=4, ensure_ascii=False), encoding="utf-8")