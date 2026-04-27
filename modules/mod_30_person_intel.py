# -*- coding: utf-8 -*-
import time
import json
import os
import re
import random
from pathlib import Path
from core.utils import C, session, REGEX_EMAIL, REGEX_CPR

# Imports fra hele din suite (BEHOLDT)
from core.network import omni_dork_search, safe_get_with_retry
from modules.mod_02_business import BusinessIntelligenceAnalyst
from modules.mod_03_breach import BreachIntelligenceAnalyst
from modules.mod_04_social import SocialMediaProfiler
from modules.mod_06_emailgen import EmailPatternGenerator
from modules.mod_08_darkweb import DarkWebIntelligence
from modules.mod_12_revphone import ReversePhoneIntelligence
from modules.mod_17_sniper import GoliathSniperEngine
from modules.mod_19_crypto import CryptoLedgerAnalyzer
from modules.mod_23_matrix import UsernameMatrixAnalyzer
from modules.mod_27_ai import TitanAIEnrichment

class PersonIntelligenceOrchestrator:
    """Modul 30: GOLIATH OMNIPOTENT V7 - Total Recursive Identity Reconstruction"""
    
    def __init__(self, target_name):
        self.target_name = target_name.strip()
        self.intel_pool = {
            "Emails": set(),
            "Brugernavne": set(),
            "Virk_Links": set(),
            "CPR_Fragments": set(),
            "Timeline": []
        }
        self.noise_domains = ["microsoft.com", "outlook.office", "support.google", "login.live"]

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*85}\n[30] GOLIATH OMNIPOTENT V7: TOTAL RECURSIVE RECON\n{'='*85}{C.RESET}")
        
        self._prepare_session(driver)

        # --- 1. MODUL 0: INITIAL DISCOVERY (Massive Search & Snippet Scraping) ---
        # Vi søger på Google, Bing, DuckDuckGo (omni_dork_search logik)
        print(f"{C.YELLOW}[*] Fase 1: Modul 0 - Massive Discovery & Snippet Scraping...{C.RESET}")
        self._run_mod0_discovery(driver)
        # V7 Fallback Logik
        if len(all_hits) < 5:
            print(f"{C.RED}[!] Få resultater fundet. Kører fallback på navne-kombinationer...{C.RESET}")
            parts = self.target_name.split()
            if len(parts) > 2:
                fallback_query = f'"{parts[0]} {parts[-1]}"'
                hits = omni_dork_search(driver, fallback_query, max_links=10)
                if hits: all_hits.extend(hits)

        # --- 2. VIRK/CVR HISTORY PIVOT (Bopæls-tidslinje) ---
        if self.intel_pool["Virk_Links"]:
            print(f"\n{C.YELLOW}[*] Fase 2: Virk/CVR History Pivot (Deltager-historik)...{C.RESET}")
            for link in self.intel_pool["Virk_Links"]:
                self._pivot_virk_history(driver, link)

        # --- 3. DARKNET SEARCH (Ahmia Proxy & Din Onion Link) ---
        # Link: http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/
        print(f"\n{C.RED}[*] Fase 3: Darknet Discovery (Ahmia Engine Onion Proxy)...{C.RESET}")
        self._run_darknet_recon(driver)

        # --- 4. VALIDERING ---
        print(f"\n{C.YELLOW}[!] Identificerede Aliaser: {', '.join(self.intel_pool['Brugernavne'])}{C.RESET}")
        print(f"{C.YELLOW}[!] Fundne Emails: {', '.join(self.intel_pool['Emails'])}{C.RESET}")
        
        valg = input(f"\n{C.CYAN}[?] Er identiteten bekræftet? (fx 0,1,2 eller 'alle'): {C.RESET}").strip()
        if not valg: return

        # --- 5. TOTAL REKURSIV EKSEKVERING ---
        print(f"\n{C.RED}[!] STARTER REKURSIV EKSEKVERING PÅ ALLE MODULER...{C.RESET}")

        # Social Monster (Modul 04)
        for handle in self.intel_pool["Brugernavne"]:
            SocialMediaProfiler(handle).run(driver)

        # Business (Modul 02)
        BusinessIntelligenceAnalyst(self.target_name).run(None)

        # Breach (Modul 03)
        for email in self.intel_pool["Emails"]:
            BreachIntelligenceAnalyst(email).run(driver)
            # Email Leak Pivot (Dorking efter passwords i leaks)
            self._email_leak_pivot(driver, email)

        # AI Context Synthesis (Modul 27)
        try:
            context = f"Navn: {self.target_name}. Email: {str(self.intel_pool['Emails'])}. Tidslinje: {str(self.intel_pool['Timeline'])}"
            TitanAIEnrichment().analyze_text(context)
        except: pass

        print(f"\n{C.GREEN}[✓✓✓] MISSION COMPLETE. GOLIATH V7 har løst puslespillet.{C.RESET}")

    def _run_mod0_discovery(self, driver):
        """Massiv søgning på tværs af motorer"""
        queries = [
            f'"{self.target_name}"',
            f'"{self.target_name}" site:virk.dk OR site:proff.dk OR site:ownr.dk',
            f'"{self.target_name}" site:instagram.com OR site:tiktok.com',
            f'"{self.target_name}" @gmail.com OR @hotmail.com OR @icloud.com'
        ]
        for q in queries:
            hits = omni_dork_search(driver, q, max_links=15)
            for hit in hits:
                snippet = f"{hit.get('title','')} {hit.get('snippet','')}"
                url = hit.get('url','')
                # Udtrækker data før noise-filter (VIGTIGT)
                for m in REGEX_EMAIL.findall(snippet): self.intel_pool["Emails"].add(m.lower())
                for c in REGEX_CPR.findall(snippet): self.intel_pool["CPR_Fragments"].add(c)
                # Handles
                h_match = re.search(r'(?:instagram\.com|tiktok\.com\/@)\/([a-zA-Z0-9._-]+)', url)
                if h_match: self.intel_pool["Brugernavne"].add(h_match.group(1))
                # Virk links
                if any(x in url for x in ["virk.dk", "ownr.dk", "proff.dk"]): self.intel_pool["Virk_Links"].add(url)

    def _pivot_virk_history(self, driver, url):
        """Scraper historisk bopæl og deltager-historik"""
        if "person" in url and "deltager" not in url: url = url.rstrip('/') + "/deltager"
        if safe_get_with_retry(driver, url):
            print(f"{C.DIM}    -> Scraper historik: {url}{C.RESET}")
            rows = driver.find_elements(By.CSS_SELECTOR, "tr")
            for r in rows:
                if any(x in r.text for x in ["Bopæl", "Vej", "Adresse"]):
                    self.intel_pool["Timeline"].append(r.text)
                    print(f"{C.GREEN}       ✓ Spor fundet: {r.text[:60]}...{C.RESET}")

    def _run_darknet_recon(self, driver):
        """NY V7: Ahmia Deep Context via Clearnet Proxy & Onion Reference"""
        # Det rigtige Ahmia søgelink der rammer dit onion target
        onion_target = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/"
        targets = [self.target_name] + list(self.intel_pool["Brugernavne"])
        
        for t in targets:
            print(f"{C.RED}    [*] Scanner Darknet (Ahmia) for: {t}{C.RESET}")
            ahmia_url = f"https://ahmia.fi/search/?q={t.replace(' ', '+')}"
            if safe_get_with_retry(driver, ahmia_url):
                if "No results" not in driver.page_source:
                    print(f"{C.GREEN}    🔥 DARKNET HIT: Resultater fundet for {t}{C.RESET}")
                    print(f"       -> Reference Target: {onion_target}")

    def _email_leak_pivot(self, driver, email):
        """Søger efter passwords i lækkede combolister"""
        dork = f'site:pastebin.com OR site:intelx.io "{email}"'
        hits = omni_dork_search(driver, dork, max_links=5)
        if hits: print(f"{C.RED}    [!] EMAIL LEAK FUNDET PÅ PASTE SITES: {email}{C.RESET}")

    def _calculate_confidence_score(self):
        """NY V7: Tildeler point for datamatch mellem CVR og Socials"""
        score = 0
        print(f"\n{C.CYAN}[*] Beregner Confidence Score for identitet...{C.RESET}")
        
        # Match mellem Virk-links og Navn
        if len(self.intel_pool["Virk_Links"]) > 0: score += 40
        
        # Match på tværs af aliaser
        if len(self.intel_pool["Brugernavne"]) > 1: score += 30
        
        # CPR Fragmenter fundet
        if len(self.intel_pool["CPR_Fragments"]) > 0: score += 30
        
        color = C.GREEN if score >= 70 else C.YELLOW
        print(f"    -> Score: {color}{score}/100{C.RESET}")
        if score >= 70: print(f"    -> {C.GREEN}[Verified Identity]{C.RESET}")

    def _prepare_session(self, driver):
        try:
            driver.get("https://www.google.com")
            time.sleep(1)
            btn = driver.find_elements(By.TAG_NAME, "button")
            for b in btn:
                if any(x in b.text for x in ["Accept", "accept", "Jeg accepterer", "Enig"]):
                    b.click(); break
        except: pass

    def _clean_hits(self, hits):
        seen = set(); clean = []
        for h in hits:
            u = h.get('url', '')
            if not u or u in seen or any(d in u for d in self.noise_domains): continue
            clean.append(h); seen.add(u)
        return clean