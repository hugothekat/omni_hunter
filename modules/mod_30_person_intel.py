# -*- coding: utf-8 -*-
import time
import json
import os
import re
from pathlib import Path
from datetime import datetime

from core.utils import C, session, REGEX_EMAIL, REGEX_CPR, extract_danish_phones
from core.utils import REGEX_BTC, REGEX_ETH, REGEX_XMR, REGEX_IBAN, REGEX_IPV4

from core.network import omni_dork_search, safe_get_with_retry

# --- DYNAMISK IMPORT AF ALLE MODULER TIL AUTO-PIVOT ---
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

# Inline V10 Regex udvidelser (Sikrer funktionalitet selvom core/utils ikke er opdateret)
REGEX_MAC_INLINE = re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b')
REGEX_REGNR_INLINE = re.compile(r'\b[A-ZÆØÅ]{2}\s?\d{5}\b')

class PersonIntelligenceOrchestrator:
    """PETFE GOLIATH V10 - The Grand Orchestrator (Total Identity Resolution)"""
    
    def __init__(self, target_name):
        self.target_name = target_name.strip()
        self.intel_pool = {
            "Mål": self.target_name,
            "Gættede_Aliaser": set(),
            "Fundne_Emails": set(),
            "Fundne_Brugernavne": set(),
            "Telefonnumre": set(),
            "Nummerplader": set(),           # NY V10
            "MAC_Adresser": set(),           # NY V10
            "Virk_Links": set(),
            "GitHub_Reddit_Spor": set(),
            "Eksponerede_Dokumenter": set(),
            "Kryptovaluta_Wallets": set(),
            "IP_Adresser": set(),
            "CPR_Fragments": set(),
            "Tidslinje_Bopæl": [],
            "Confidence_Score": 0,
            "Timestamp": datetime.now().isoformat()
        }
        self.noise_domains = ["microsoft.com", "outlook.office", "support.google", "login.live", "wikipedia.org", "eniro.dk"]

    def run(self, driver):
        print(f"\n{C.BG_RED}{C.WHITE} {'='*85} {C.RESET}")
        print(f"{C.BG_RED}{C.WHITE} [30] THE GRAND ORCHESTRATOR: GOLIATH V10 AUTONOMOUS ENGINE {'='*24} {C.RESET}")
        print(f"{C.DIM}[*] Operatør har beordret fuld rekursiv udslettelse og rekonkurrence på: {self.target_name}{C.RESET}\n")
        
        self._prepare_session(driver)
        
        # FASE 0: Generer logiske permutationer
        self._generate_identity_permutations()

        # FASE 1: Deep Clearnet Dorking (8-Lags Søgning)
        print(f"{C.YELLOW}[*] FASE 1: Deep Clearnet Dorking (Udtræk af metadata, hardware og skjulte filer)...{C.RESET}")
        self._run_deep_clearnet_dorking(driver)

        # FASE 2: Virksomhed & Bopæls-Pivot
        if self.intel_pool["Virk_Links"]:
            print(f"\n{C.YELLOW}[*] FASE 2: Virk/CVR Scraping (Bopælshistorik & Netværk)...{C.RESET}")
            for link in list(self.intel_pool["Virk_Links"])[:4]: 
                self._pivot_virk_history(driver, link)

        # FASE 3: Darknet & Leak Databaser
        print(f"\n{C.RED}[*] FASE 3: Darknet & Pastebin Dorking (Jagt på lækkede data)...{C.RESET}")
        self._run_darknet_recon(driver)
        for email in list(self.intel_pool["Fundne_Emails"])[:3]:
            self._pastebin_leak_pivot(driver, email)

        # FASE 4: Score & Validering
        self._calculate_confidence_score()
        self._print_intel_summary()
        
        # Operatør Godkendelse
        valg = input(f"\n{C.CYAN}[?] OVERRIDE KODE GODKENDT. Tryk ENTER for at affyre samtlige PETFE-moduler mod disse data (eller 'n' for stop): {C.RESET}").strip().lower()
        if valg in ['n', 'nej', 'no']: 
            print(f"{C.DIM}[*] Efterforskning sat på pause. Data gemt i sagsmappen.{C.RESET}")
            self.save()
            return

        self.save() # Gem Master Report før vi angriber

        # FASE 5: THE GRAND OMNI-PIVOT
        print(f"\n{C.BG_RED}{C.WHITE} 🔥 STARTER THE GRAND OMNI-PIVOT: AUTONOM EKSEKVERING PÅ TVÆRS AF ALLE MODULER 🔥 {C.RESET}\n")
        self._execute_omni_pivot(driver)

        print(f"\n{C.GREEN}[✓✓✓] GOLIATH V10 HAR FULDENDT DEN AUTONOME EFTERFORSKNING.{C.RESET}")
        print(f"{C.CYAN}      -> Kør Modul 14 (HTML Dashboard) for at se det fulde, tværgående resultat.{C.RESET}")

    def _generate_identity_permutations(self):
        """V10.1: Rettet fejl hvor årstal ikke kunne subscriptes"""
        print(f"{C.DIM}    -> Genererer identitets-permutationer...{C.RESET}")
        parts = self.target_name.lower().split()
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            # Konverter årstal til streng først for at undgå 'int' object is not subscriptable
            current_year_suffix = str(datetime.now().year)[-2:] 
            
            aliases = [
                f"{f}{l}", f"{f}.{l}", f"{f[0]}{l}", f"{f}{l[0]}", 
                f"{f}_{l}", f"{f}{l}123", f"{f}{l}{current_year_suffix}"
            ]
            for a in aliases: self.intel_pool["Gættede_Aliaser"].add(a)

    def _run_deep_clearnet_dorking(self, driver):
        """V10: 8-Lags Dorking Motor (Suger ALT)"""
        all_hits = []
        name = self.target_name

        layer_1 = [f'"{name}"', f'"{name}" @gmail.com OR @hotmail.com OR @icloud.com OR @proton.me']
        layer_2 = [f'"{name}" site:instagram.com OR site:tiktok.com OR site:facebook.com OR site:linkedin.com']
        layer_3 = [f'"{name}" site:github.com OR site:reddit.com OR site:trello.com OR site:pastebin.com']
        layer_4 = [f'"{name}" site:virk.dk OR site:proff.dk OR site:ownr.dk OR site:statstidende.dk']
        layer_5 = [f'"{name}" ext:pdf OR ext:docx OR ext:xls OR ext:txt']
        layer_6 = [f'intitle:"index of" "{name}"']
        
        # NY V10 Lags:
        layer_7 = [f'"{name}" site:afdoede.dk OR site:slaegtogdata.dk OR site:myheritage.dk'] # Slægt/Familie
        layer_8 = [f'"{name}" site:tinglysning.dk OR site:nummerplade.net OR site:bbr.dk'] # Aktiver/Køretøjer

        all_queries = layer_1 + layer_2 + layer_3 + layer_4 + layer_5 + layer_6 + layer_7 + layer_8

        for q in all_queries:
            hits = omni_dork_search(driver, q, max_links=8)
            clean_hits = self._clean_hits(hits)
            all_hits.extend(clean_hits)
            self._extract_advanced_intel(clean_hits)

    def _extract_advanced_intel(self, hits):
        """V10: Regex-steroider til at flå data, hardware og køretøjer ud af Snippets"""
        for hit in hits:
            snippet = f"{hit.get('title','')} {hit.get('snippet','')}"
            url = hit.get('url','')
            
            # Personlige Data
            for m in REGEX_EMAIL.findall(snippet): self.intel_pool["Fundne_Emails"].add(m.lower())
            for c in REGEX_CPR.findall(snippet): self.intel_pool["CPR_Fragments"].add(c)
            for p in extract_danish_phones(snippet): self.intel_pool["Telefonnumre"].add(p)
            
            # Hardware & Aktiver (NY V10)
            for mac in REGEX_MAC_INLINE.findall(snippet): self.intel_pool["MAC_Adresser"].add(mac)
            for reg in REGEX_REGNR_INLINE.findall(snippet): self.intel_pool["Nummerplader"].add(reg.replace(" ", ""))
            
            # Finans & Krypto
            for btc in REGEX_BTC.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"BTC: {btc}")
            for eth in REGEX_ETH.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"ETH: {eth}")
            for xmr in REGEX_XMR.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"XMR: {xmr}")
            for iban in REGEX_IBAN.findall(snippet): self.intel_pool["Kryptovaluta_Wallets"].add(f"IBAN: {iban}")
            
            # Netværk
            for ip in REGEX_IPV4.findall(snippet): 
                if not ip.startswith("1.0") and not ip.startswith("2.0"): 
                    self.intel_pool["IP_Adresser"].add(ip)

            # URL Kategorisering
            h_match = re.search(r'(?:instagram\.com|tiktok\.com\/@|twitter\.com|github\.com)\/([a-zA-Z0-9._-]+)', url)
            if h_match: self.intel_pool["Fundne_Brugernavne"].add(h_match.group(1))
            
            if any(x in url for x in ["virk.dk", "ownr.dk", "proff.dk"]): self.intel_pool["Virk_Links"].add(url)
            if any(x in url for x in ["github.com", "reddit.com", "stackoverflow.com"]): self.intel_pool["GitHub_Reddit_Spor"].add(url)
            if url.lower().endswith(('.pdf', '.docx', '.xls', '.txt')): self.intel_pool["Eksponerede_Dokumenter"].add(url)

    def _pivot_virk_history(self, driver, url):
        """Scraper historisk bopæl fra virksomhedsregistre"""
        if "person" in url and "deltager" not in url: url = url.rstrip('/') + "/deltager"
        if safe_get_with_retry(driver, url):
            print(f"{C.DIM}    -> Scraper CVR-historik: {url}{C.RESET}")
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "tr, div.address")
                for r in rows:
                    if any(x in r.text for x in ["Bopæl", "Vej", "Adresse", "Postnr"]):
                        clean_addr = r.text.replace("\n", " | ")
                        self.intel_pool["Tidslinje_Bopæl"].append(clean_addr)
                        print(f"{C.GREEN}       ✓ Bopælsspor: {clean_addr[:60]}...{C.RESET}")
            except Exception: pass

    def _run_darknet_recon(self, driver):
        targets = [self.target_name] + list(self.intel_pool["Fundne_Emails"])[:3]
        for t in targets:
            print(f"{C.DIM}    [*] Scanner Darknet (Ahmia) for: {t}{C.RESET}")
            ahmia_url = f"https://ahmia.fi/search/?q={t.replace(' ', '+')}"
            if safe_get_with_retry(driver, ahmia_url):
                if "No results" not in driver.page_source:
                    print(f"{C.RED}    🔥 DARKNET HIT: Resultater fundet for {t}{C.RESET}")

    def _pastebin_leak_pivot(self, driver, email):
        dork = f'site:pastebin.com OR site:intelx.io OR site:trello.com "{email}"'
        hits = omni_dork_search(driver, dork, max_links=3)
        for h in hits:
            print(f"{C.RED}    [!] DATA LÆKAGE FUNDET PÅ PASTE-SITE: {h.get('url')}{C.RESET}")
            self.intel_pool["Eksponerede_Dokumenter"].add(h.get('url'))

    def _calculate_confidence_score(self):
        score = 0
        if len(self.intel_pool["Virk_Links"]) > 0: score += 15
        if len(self.intel_pool["Fundne_Brugernavne"]) > 0: score += 15
        if len(self.intel_pool["Fundne_Emails"]) > 0: score += 15
        if len(self.intel_pool["Telefonnumre"]) > 0: score += 15
        if len(self.intel_pool["CPR_Fragments"]) > 0: score += 10
        if len(self.intel_pool["Tidslinje_Bopæl"]) > 0: score += 10
        if len(self.intel_pool["Nummerplader"]) > 0: score += 10
        if len(self.intel_pool["MAC_Adresser"]) > 0: score += 10
        
        self.intel_pool["Confidence_Score"] = min(score, 100)

    def _print_intel_summary(self):
        score = self.intel_pool["Confidence_Score"]
        color = C.GREEN if score >= 70 else C.YELLOW
        
        print(f"\n{C.CYAN}--- [ GOLIATH V10 INTELLIGENCE OVERBLIK ] ---{C.RESET}")
        print(f"Datamatch Score: {color}{score}/100{C.RESET}")
        print(f"Brugernavne:   {C.WHITE}{', '.join(self.intel_pool['Fundne_Brugernavne'])}{C.RESET}")
        print(f"Emails:        {C.WHITE}{', '.join(self.intel_pool['Fundne_Emails'])}{C.RESET}")
        print(f"Telefoner:     {C.WHITE}{', '.join(self.intel_pool['Telefonnumre'])}{C.RESET}")
        
        if self.intel_pool['Nummerplader']: print(f"Køretøjer:     {C.RED}{', '.join(self.intel_pool['Nummerplader'])}{C.RESET}")
        if self.intel_pool['MAC_Adresser']: print(f"MAC/BSSID:     {C.RED}{', '.join(self.intel_pool['MAC_Adresser'])}{C.RESET}")
        if self.intel_pool['Kryptovaluta_Wallets']: print(f"Krypto/Finans: {C.RED}{', '.join(self.intel_pool['Kryptovaluta_Wallets'])}{C.RESET}")
        if self.intel_pool['IP_Adresser']: print(f"IP Adresser:   {C.RED}{', '.join(self.intel_pool['IP_Adresser'])}{C.RESET}")
        if self.intel_pool['Eksponerede_Dokumenter']: print(f"Dokumenter:    {C.YELLOW}{len(self.intel_pool['Eksponerede_Dokumenter'])} fundet{C.RESET}")

    def _execute_omni_pivot(self, driver):
        """V10 THE GRAND PIVOT: Kaster data ind i ALT."""
        
        # 0. E-mail Generation (Modul 06)
        print(f"\n{C.CYAN}[PIVOT] Kører Modul 06 (Email Gen) på navnet...{C.RESET}")
        try: EmailPatternGenerator(self.target_name).run(driver)
        except Exception: pass

        # 1. Social & Matrix (Modul 04 & 23)
        for handle in self.intel_pool["Fundne_Brugernavne"]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 04 & 23 (Profil-søgning) på: {handle}{C.RESET}")
            try:
                SocialMediaProfiler(handle).run(driver)
                MatrixAnalyzer(handle).run(None) 
            except Exception: pass

        # 2. Telefonnumre (Modul 12)
        for phone in self.intel_pool["Telefonnumre"]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 12 (Telefonopslag) på: {phone}{C.RESET}")
            try: ReversePhoneIntelligence(phone).run(driver)
            except Exception: pass

        # 3. Breach & IP Track (Modul 03)
        for email in self.intel_pool["Fundne_Emails"]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 03 (Password Breach) på: {email}{C.RESET}")
            try: BreachIntelligenceAnalyst(email).run(driver)
            except Exception: pass

        # 4. Krypto Sporing (Modul 19)
        for wallet in self.intel_pool["Kryptovaluta_Wallets"]:
            clean_addr = wallet.split(": ")[1] if ": " in wallet else wallet
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 19 (Blockchain Trace) på: {clean_addr}{C.RESET}")
            try: CryptoLedgerAnalyzer(clean_addr).run(None)
            except Exception: pass

        # 5. IP Analyse (Modul 10)
        for ip in self.intel_pool["IP_Adresser"]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 10 (Netværksscan) på: {ip}{C.RESET}")
            try: IPNetworkAnalyzer(ip).run(None)
            except Exception: pass

        # 6. Køretøjer (Modul 20) NY V10
        for regnr in self.intel_pool["Nummerplader"]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 20 (Køretøjs-OSINT) på: {regnr}{C.RESET}")
            try: VehicleIntelligence(regnr).run(driver)
            except Exception: pass

        # 7. Geofencing (Modul 21) NY V10
        for mac in self.intel_pool["MAC_Adresser"]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 21 (BSSID Geofencing) på: {mac}{C.RESET}")
            try: BSSIDGeofencer(mac).run(None)
            except Exception: pass

        # 8. Dokument Arkivering (Modul 25)
        for doc_url in list(self.intel_pool["Eksponerede_Dokumenter"])[:3]:
            print(f"\n{C.CYAN}[PIVOT] Kører Modul 25 (Bevissikring) på dokument: {doc_url}{C.RESET}")
            try: WaybackMachineIntelligence(doc_url).run(None)
            except Exception: pass

        # 9. Erhverv (Modul 02)
        print(f"\n{C.CYAN}[PIVOT] Kører Modul 02 (Erhvervs-OSINT) på: {self.target_name}{C.RESET}")
        try: BusinessIntelligenceAnalyst(self.target_name).run(driver)
        except Exception: pass

        # 10. Taktisk Wordlist (Modul 17)
        print(f"\n{C.YELLOW}[*] Bygger Ultimativ Wordlist via Modul 17 (Sniper)...{C.RESET}")
        try:
            email_seed = list(self.intel_pool["Fundne_Emails"])[0] if self.intel_pool["Fundne_Emails"] else ""
            cpr_seed = list(self.intel_pool["CPR_Fragments"])[0] if self.intel_pool["CPR_Fragments"] else ""
            clues = ",".join(self.intel_pool["Fundne_Brugernavne"])
            SniperModule(name=self.target_name, email=email_seed, cpr=cpr_seed, clues=clues).run()
        except Exception: pass

        # 11. LLM Profilering (Modul 27)
        print(f"\n{C.YELLOW}[*] Kører Forensic AI Profilering (Modul 27)...{C.RESET}")
        try:
            context = json.dumps(self.intel_pool, default=list)
            TitanAIEnrichment().analyze_text(context)
        except Exception: pass

        # 12. AUTO-COMPILE VISUALS (Modul 28 & 29) NY V10
        print(f"\n{C.BG_RED}{C.WHITE} [*] KOMPILERER VISUELLE KORT (MALTEGO & GOOGLE EARTH) {C.RESET}")
        try:
            GoliathGraphExporter().generate()
            GoogleEarthExporter().generate()
        except Exception as e: print(f"{C.DIM}[-] Fejl ved graf-generering: {e}{C.RESET}")

    def _prepare_session(self, driver):
        try:
            driver.get("https://www.google.com")
            time.sleep(1)
            btn = driver.find_elements(By.TAG_NAME, "button")
            for b in btn:
                if any(x in b.text for x in ["Accept", "accept", "Jeg accepterer", "Enig"]):
                    driver.execute_script("arguments[0].click();", b); break
        except: pass

    def _clean_hits(self, hits):
        seen = set(); clean = []
        for h in hits:
            u = h.get('url', '')
            if not u or u in seen or any(d in u for d in self.noise_domains): continue
            clean.append(h); seen.add(u)
        return clean

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/30_MASTER_ORCHESTRATOR_{self.target_name.replace(' ', '_')}.json"
        
        export_data = self.intel_pool.copy()
        for key in export_data:
            if isinstance(export_data[key], set):
                export_data[key] = list(export_data[key])
            
        Path(filename).write_text(json.dumps(export_data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"{C.GREEN}    [✓] V10 Master Intelligence Profil gemt lokalt.{C.RESET}")