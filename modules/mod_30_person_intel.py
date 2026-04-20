# -*- coding: utf-8 -*-
import time
import json
import os
import re
import random
from pathlib import Path
from core.utils import C, session, REGEX_EMAIL

# Imports fra hele din suite
from core.network import omni_dork_search, safe_get_with_retry
from modules.mod_02_business import BusinessIntelligenceAnalyst
from modules.mod_03_breach import BreachIntelligenceAnalyst
from modules.mod_04_social import SocialMediaProfiler
from modules.mod_06_emailgen import EmailPatternGenerator
from modules.mod_08_darkweb import DarkWebIntelligence # MODUL 08 TIL DARKNET
from modules.mod_12_revphone import ReversePhoneIntelligence
from modules.mod_17_sniper import GoliathSniperEngine
from modules.mod_19_crypto import CryptoLedgerAnalyzer
from modules.mod_20_vehicle import VehicleIntelligence
from modules.mod_22_chatapp import ChatAppIntelligence
from modules.mod_23_matrix import UsernameMatrixAnalyzer
from modules.mod_25_wayback import WaybackMachineIntelligence
from modules.mod_27_ai import TitanAIEnrichment

class PersonIntelligenceOrchestrator:
    """Modul 30: GOLIATH OMNIPOTENT V4 - Recursive Identity & Darknet Engine."""
    
    def __init__(self, target_name):
        self.target_name = target_name.strip()
        self.intel_pool = {
            "Emails": set(),
            "Telefonnumre": set(),
            "Brugernavne": set(),
            "Virksomheder": set(),
            "Sociale_Links": set(),
            "Profiler_Bio_Data": [],
            "Darknet_Hits": []
        }
        # Støj-liste: Disse domæner filtreres fra for at holde feedet rent
        self.noise_domains = [
            "microsoft.com", "outlook.office", "support.google", "accounts.google",
            "login.live", "office365.com", "appleid.apple", "support.microsoft"
        ]

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*85}\n[30] GOLIATH OMNIPOTENT V4: GLOBAL IDENTITY & DARKNET RECON\n{'='*85}{C.RESET}")
        
        self._prepare_session(driver)

        # --- TRIN 1: MASSIV DISCOVERY (CLEANED) ---
        print(f"{C.YELLOW}[*] Fase 1: Global Discovery & Darknet Proxy Search...{C.RESET}")
        
        search_queries = [
            f'"{self.target_name}"',
            f'"{self.target_name}" site:tiktok.com OR site:instagram.com OR site:facebook.com',
            f'"{self.target_name}" leak OR breach OR combolist OR database', # Leak search
            f'"{self.target_name}" @gmail.com OR @hotmail.com OR @live.dk OR @icloud.com', # Email focus
            f'"{self.target_name}" site:pastebin.com OR site:ghostbin.com OR site:controlc.com' # Paste sites
        ]
        
        all_hits = []
        for q in search_queries:
            print(f"{C.DIM}    -> Graver i OSINT-rummet: {q}{C.RESET}")
            try:
                hits = omni_dork_search(driver, q, max_links=20)
                if hits: all_hits.extend(hits)
            except Exception: pass
            time.sleep(random.uniform(1, 1.5))

        # --- TRIN 2: DARKNET ANALYSE (Modul 08 Logik) ---
        print(f"{C.RED}[*] Fase 2: Scanner Darknet (Tor Proxy Search via Ahmia)...{C.RESET}")
        try:
            dark_mod = DarkWebIntelligence(self.target_name)
            dark_mod.run(None) # Vi bruger dens interne logik til at slå op
            # Vi indfanger fund her (simuleret integration)
        except Exception: pass

        # --- TRIN 3: INTELLIGENT DATA EXTRACTION & NOISE FILTERING ---
        unique_hits = self._clean_hits(all_hits)
        
        print(f"\n{C.CYAN}--- GOLIATH DISCOVERY FEED (Microsoft-links filtreret) ---{C.RESET}")
        for i, hit in enumerate(unique_hits):
            raw_title = hit.get('title', '').strip()
            url = hit.get('url', 'Ingen URL')
            
            # Smart Title Generation
            if not raw_title or raw_title.lower() == "ingen titel":
                domain = url.split("//")[-1].split("/")[0]
                title = f"Spor fundet på {C.YELLOW}{domain}{C.RESET}"
            else:
                title = raw_title

            snippet = hit.get('snippet', '').strip()
            print(f" [{i}] {C.GREEN}{title}{C.RESET}\n     URL: {url}")
            
            self._extract_data_from_hit(title, url, snippet)

        print(f"\n{C.YELLOW}[!] Identificerede Aliaser: {', '.join(self.intel_pool['Brugernavne']) if self.intel_pool['Brugernavne'] else 'Ingen'}{C.RESET}")
        print(f"{C.YELLOW}[!] Potentielle Emails: {', '.join(self.intel_pool['Emails']) if self.intel_pool['Emails'] else 'Søger...'}{C.RESET}")
        
        valg = input(f"\n{C.CYAN}[?] Bekræft hits (fx 0,1,3) eller 'alle': {C.RESET}").strip()
        if not valg: return

        # --- TRIN 4: DEN STORE REKURSIVE PIVOT ---
        print(f"\n{C.RED}[!] VALIDERING FULDFØRT. STARTER TOTAL PUSLESPILS-LØSNING...{C.RESET}")

        # 1. Social & Bio (Modul 04 + 25)
        if self.intel_pool["Brugernavne"]:
            print(f"{C.YELLOW}[*] Pivot: Modul 04 (Deep Social Scrape)...{C.RESET}")
            for handle in self.intel_pool["Brugernavne"]:
                try:
                    social = SocialMediaProfiler(handle)
                    social.run(driver)
                    if "Deep_Scrape" in social.data:
                        self.intel_pool["Profiler_Bio_Data"].append(social.data["Deep_Scrape"])
                except Exception: pass

        # 2. Breach & Email (Modul 03 + 06)
        if not self.intel_pool["Emails"]:
            print(f"{C.DIM}[*] Ingen emails fundet. Genererer mønstre (Modul 06)...{C.RESET}")
            EmailPatternGenerator(self.target_name).run(driver) # Genererer dem til session
            
        for email in self.intel_pool["Emails"]:
            print(f"{C.RED}[*] Pivot: Modul 03 (Breach Analytics) -> {email}{C.RESET}")
            try: BreachIntelligenceAnalyst(email).run(driver)
            except Exception: pass

        # 3. Erhverv & Økonomi (Modul 02 + 19)
        if self.intel_pool["Virksomheder"]:
            print(f"{C.YELLOW}[*] Pivot: Modul 02 (Business Intelligence)...{C.RESET}")
            try: BusinessIntelligenceAnalyst(self.target_name).run(None)
            except Exception: pass

        # 4. AI & Matrix (Modul 27 + 23)
        print(f"{C.CYAN}[*] Pivot: Modul 27 & 23 (Titan AI Context & Matrix Synthesis)...{C.RESET}")
        try:
            ai = TitanAIEnrichment()
            combined_context = f"Mål: {self.target_name}. Fundne emails: {self.intel_pool['Emails']}. Sociale spor: {self.intel_pool['Profiler_Bio_Data']}"
            ai.analyze_text(combined_context)
            UsernameMatrixAnalyzer(self.target_name).run(None)
        except Exception: pass
        
        print(f"\n{C.GREEN}[✓✓✓] MISSION COMPLETE. GOLIATH V4 har færdiggjort analysen.{C.RESET}")

    def _extract_data_from_hit(self, title, url, snippet):
        # Email extraction (Højt prioriteret)
        for e in REGEX_EMAIL.findall(f"{title} {url} {snippet}"):
            self.intel_pool["Emails"].add(e.lower())
        
        # Social Handles
        handle_match = re.search(r'(?:instagram\.com|tiktok\.com\/@|facebook\.com|linkedin\.com\/in|youtube\.com\/@)\/([a-zA-Z0-9._-]+)', url)
        if handle_match:
            handle = handle_match.group(1).replace('@', '')
            if handle not in ['p', 'reels', 'people', 'explore']:
                self.intel_pool["Brugernavne"].add(handle)

        # Business Detection
        if any(x in url.lower() for x in ["ownr.dk", "virkly.io", "proff.dk", "cvr"]):
            self.intel_pool["Virksomheder"].add(self.target_name)

    def _prepare_session(self, driver):
        try:
            driver.get("https://www.google.com")
            time.sleep(1)
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                if any(x in b.text for x in ["Accept", "accept", "Jeg accepterer", "Enig"]):
                    b.click()
                    break
        except Exception: pass

    def _clean_hits(self, hits):
        seen = set()
        clean = []
        for h in hits:
            url = h.get('url', '')
            if not url or url in seen: continue
            
            # NOISE FILTER: Hvis domænet er i vores sortliste, hopper vi over det
            if any(domain in url.lower() for domain in self.noise_domains):
                continue
                
            clean.append(h)
            seen.add(url)
        return clean