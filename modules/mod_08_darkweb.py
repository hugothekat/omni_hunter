# -*- coding: utf-8 -*-
"""
PETFE GOLIATH V31: ABYSS DARKWEB CRAWLER
Operativ Specifikation:
- Deep-Dive Onion Routing: Skraper det faktiske indhold af .onion sider, ikke kun snippets.
- Clearnet Tor2Web Injection: Læser darkweb-sider via proxy-oversættelse, selv når Tor er slukket.
- Next-Gen Threat Identifiers: Regex extraction af PGP Keys, Tox IDs, og Session IDs.
- Asynchronous Execution: Ahmia scraping og Clearnet dorking kører parallelt.
"""

import requests
import json
import os
import re
import urllib.parse
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup 

from core.utils import C, session
from core.network import CONFIG, omni_dork_search

class AbyssDarkwebCrawler: 
    def __init__(self, query):
        self.query = query.strip()
        self.print_lock = threading.Lock()
        self.use_tor = CONFIG.get("use_tor_proxy", False)
        
        self.data = {
            "Søgning": self.query, 
            "Proxy_Type": "TOR Network" if self.use_tor else "Clearnet & Tor2Web Proxies",
            "Onion_Hits": [], 
            "Deep_Dive_Skrapede_Sider": 0,    # NY V31: Tæller faktiske onion sider læst
            "Ekstraherede_Emails": set(), 
            "Ekstraherede_Crypto": set(), 
            "Ekstraherede_Tox_Session": set(),# NY V31: Moderne Darkweb Chat IDs
            "Ekstraherede_PGP_Keys": set(),   # NY V31: PGP Nøgler til de-anonymisering
            "Clearnet_Onion_Spor": [], 
            "Timestamp": datetime.now().isoformat()
        }

    def _log(self, level, message):
        """Trådsikker og klinisk logning."""
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "CRITICAL": C.RED, "SUCCESS": C.GREEN, "DEEP": C.MAGENTA}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} [{color}{level}{C.RESET}] {message}\n")

    def run(self, driver=None):
        print(f"\n{C.WHITE}{'='*80}{C.RESET}")
        print(f"{C.WHITE} MODULE 08: ABYSS DARKWEB CRAWLER & THREAT EXTRACTOR (V31){C.RESET}")
        print(f"{C.WHITE}{'='*80}{C.RESET}")
        self._log("INFO", f"Target Query: {self.query}")
        self._log("INFO", f"Routing Protocol: {self.data['Proxy_Type']}")
        
        # Opretter Asynkron Matrix for at køre Ahmia og Clearnet Dorks samtidigt
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_ahmia = executor.submit(self._crawl_ahmia)
            future_clearnet = executor.submit(self._search_clearnet_proxies, driver)
            
            # Venter på at Ahmia er færdig, før vi starter Deep Dive på de fundne links
            ahmia_links = future_ahmia.result()
            
            if ahmia_links:
                self._log("WARN", f"Initiating Deep-Dive into {len(ahmia_links)} .onion sources...")
                deep_dive_futures = [executor.submit(self._deep_dive_onion, link) for link in ahmia_links]
                concurrent.futures.wait(deep_dive_futures)
            
            concurrent.futures.wait([future_clearnet])

        # Opsamling & konvertering af sets
        self.data["Ekstraherede_Emails"] = list(self.data["Ekstraherede_Emails"])
        self.data["Ekstraherede_Crypto"] = list(self.data["Ekstraherede_Crypto"])
        self.data["Ekstraherede_Tox_Session"] = list(self.data["Ekstraherede_Tox_Session"])
        self.data["Ekstraherede_PGP_Keys"] = list(self.data["Ekstraherede_PGP_Keys"])

        self._print_tactical_dashboard()
        self.save()
        return self.data

    # =========================================================================
    # CORE ROUTING & SEARCH ENGINES
    # =========================================================================
    def _get_session(self):
        """Genererer en requests session konfigureret med eller uden Tor."""
        req_session = requests.Session()
        req_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"})
        if self.use_tor:
            proxy = CONFIG.get("tor_proxy_url", "socks5h://127.0.0.1:9050")
            req_session.proxies = {'http': proxy, 'https': proxy}
        return req_session

    def _crawl_ahmia(self):
        """Søger Ahmia-indekset og returnerer links til Deep-Dive."""
        req_session = self._get_session()
        found_links = []
        
        if self.use_tor:
            url = f"http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={requests.utils.quote(self.query)}"
        else:
            url = f"https://ahmia.fi/search/?q={requests.utils.quote(self.query)}"
            
        try:
            res = req_session.get(url, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            results = soup.find_all('li', class_='searchResultsItem')
            
            if not results:
                self._log("INFO", "Ahmia index returned zero results.")
                return found_links

            for item in results[:10]: # Tager kun top 10 for hastighedens skyld
                link_tag = item.find('cite')
                title_tag = item.find('h4')
                desc_tag = item.find('p')
                
                if link_tag:
                    onion_link = link_tag.text.strip()
                    titel = title_tag.text.strip() if title_tag else "Ukendt Titel"
                    beskrivelse = desc_tag.text.strip() if desc_tag else ""
                    
                    self._log("CRITICAL", f"AHMIA HIT: {titel} ({onion_link})")
                    self._harvest_intel(beskrivelse, onion_link, context="Ahmia Snippet")
                    
                    self.data["Onion_Hits"].append({
                        "Titel": titel,
                        "URL": onion_link,
                        "Kontekst": beskrivelse[:200]
                    })
                    
                    # Sikrer at vi har fuld URL
                    if not onion_link.startswith("http"):
                        onion_link = "http://" + onion_link
                    found_links.append(onion_link)
                    
            return found_links
            
        except requests.exceptions.ProxyError:
            self._log("ERROR", "Tor Proxy Error. Ensure Tor service is running on 127.0.0.1:9050.")
        except Exception as e:
            self._log("ERROR", f"Ahmia crawl failed: {e}")
            
        return found_links

    # =========================================================================
    # ABYSS DEEP-DIVE (Scraper indholdet AF SELVE onion-siden)
    # =========================================================================
    def _deep_dive_onion(self, onion_url):
        """
        Går fysisk ind på onion-linket og læser hele sidens kildekode for secrets.
        Hvis Tor ikke er aktiveret, oversætter den linket til en Tor2Web proxy!
        """
        req_session = self._get_session()
        
        target_url = onion_url
        if not self.use_tor:
            # Tor2Web Translation Trick: Oversæt http://xyz.onion til https://xyz.onion.ly
            target_url = onion_url.replace(".onion", ".onion.ly").replace("http://", "https://")
            
        try:
            res = req_session.get(target_url, timeout=15)
            if res.status_code == 200:
                self.data["Deep_Dive_Skrapede_Sider"] += 1
                self._log("DEEP", f"Successfully breached and dumped source code from: {onion_url}")
                # Kører den fulde HTML igennem regex-kværnen!
                self._harvest_intel(res.text, onion_url, context="Deep Scrape")
        except Exception:
            # Sider på darkweb er ofte nede, det er normalt
            pass

    def _search_clearnet_proxies(self, driver):
        """Dorker clearnet for indekserede lækager via Tor2Web proxies."""
        if not driver: return
        self._log("INFO", "Executing Clearnet Tor2Web Dorking Sequence...")
        
        dork = f'(site:onion.ly OR site:onion.ws OR site:onion.pet OR site:onion.dog) "{self.query}"'
        links = omni_dork_search(driver, dork, max_links=4)
        
        if links:
            for link in links:
                url = link.get('url', '')
                self._log("CRITICAL", f"CLEARNET LEAK HIT: {url[:80]}")
                if url not in self.data["Clearnet_Onion_Spor"]:
                    self.data["Clearnet_Onion_Spor"].append(url)
                    
                snippet = link.get('snippet', '')
                self._harvest_intel(snippet, url, context="Clearnet Dork")
        else:
            self._log("INFO", "No clearnet Tor2Web leaks identified.")

    # =========================================================================
    # NEXT-GEN THREAT EXTRACTION (V31)
    # =========================================================================
    def _harvest_intel(self, text, source_link, context=""):
        """Udvidet regex-motor tilpasset moderne cyberkriminalitet og darknet-standarder."""
        
        # 1. PGP Nøgler (Kritisk for at identificere trusselsaktører)
        pgp_pattern = re.findall(r'-----BEGIN PGP PUBLIC KEY BLOCK-----[A-Za-z0-9\+\/\n\r=]+-----END PGP PUBLIC KEY BLOCK-----', text)
        for pgp in pgp_pattern:
            self.data["Ekstraherede_PGP_Keys"].add("PGP Key Block Found (Se JSON for rå data)")
            self._log("SUCCESS", f"[{context}] Extracted PGP Public Key from {source_link}")

        # 2. Tox IDs (76 hex chars - Standard p2p chat for Ransomware grupper)
        tox_pattern = re.findall(r'\b[A-Fa-f0-9]{76}\b', text)
        for tox in tox_pattern:
            self.data["Ekstraherede_Tox_Session"].add(f"Tox ID: {tox}")
            self._log("CRITICAL", f"[{context}] Tox Messenger ID Identified: {tox[:10]}...")

        # 3. Session IDs (66 chars, starter med 05)
        session_pattern = re.findall(r'\b05[a-zA-Z0-9]{64}\b', text)
        for sess in session_pattern:
            self.data["Ekstraherede_Tox_Session"].add(f"Session ID: {sess}")
            self._log("CRITICAL", f"[{context}] Session Messenger ID Identified: {sess[:10]}...")

        # 4. Crypto Wallets
        btc_pattern = re.findall(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', text)
        for btc in btc_pattern:
            self.data["Ekstraherede_Crypto"].add(f"BTC: {btc}")
            self._log("SUCCESS", f"[{context}] Bitcoin Wallet Identified: {btc}")
            
        xmr_pattern = re.findall(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b', text)
        for xmr in xmr_pattern:
            self.data["Ekstraherede_Crypto"].add(f"XMR: {xmr}")
            self._log("SUCCESS", f"[{context}] Monero Wallet Identified (High OPSEC): {xmr[:15]}...")

        # 5. Emails
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        for em in emails:
            # Undgår false positives fra typiske onion/pgp støj
            if not any(x in em.lower() for x in [".onion", "pgp", "example"]):
                self.data["Ekstraherede_Emails"].add(em.lower())
                self._log("SUCCESS", f"[{context}] Email Identified: {em.lower()}")

    # =========================================================================
    # TACTICAL DASHBOARD & OUTPUT
    # =========================================================================
    def _print_tactical_dashboard(self):
        with self.print_lock:
            print(f"\n{C.BG_RED}{C.WHITE} TACTICAL ABYSS SUMMARY: {self.query.upper()} {C.RESET}\n")
            print(f"Network Protocol: {C.GREEN}{self.data['Proxy_Type']}{C.RESET}")
            print(f"Deep-Dived Sites: {C.GREEN}{self.data['Deep_Dive_Skrapede_Sider']}{C.RESET} (Raw HTML successfully extracted)\n")
            
            if self.data['Ekstraherede_PGP_Keys']:
                print(f"{C.RED}[!] PGP Keys (De-Anonymization Leads):{C.RESET} {len(self.data['Ekstraherede_PGP_Keys'])} Keys Captured")
                
            if self.data['Ekstraherede_Tox_Session']:
                print(f"{C.RED}[!] Underground Comms (Tox/Session IDs):{C.RESET}")
                for cid in self.data['Ekstraherede_Tox_Session']: print(f"    └─ {cid}")

            if self.data['Ekstraherede_Crypto']:
                print(f"{C.MAGENTA}[+] Cryptocurrency Wallets:{C.RESET}")
                for w in self.data['Ekstraherede_Crypto']: print(f"    └─ {w}")

            if self.data['Ekstraherede_Emails']:
                print(f"{C.CYAN}[+] Associated Emails:{C.RESET}")
                for e in self.data['Ekstraherede_Emails']: print(f"    └─ {e}")
                
            print(f"\n{C.DIM}" + "-"*80 + f"{C.RESET}")

    def save(self):
        folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/08_DARKWEB_{self.query.replace(' ', '_')}.json"
        
        if os.path.exists(filename):
            try: os.remove(filename)
            except Exception: pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        self._log("SUCCESS", f"Abyss Intelligence Report archived: {filename}")

# Alias til backwards compatibility i Orchestrator og Main
DarkWebIntelligence = AbyssDarkwebCrawler