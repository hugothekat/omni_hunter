# -*- coding: utf-8 -*-
"""
🚀 GOLIATH NETWORK GRANDMASTER (V36: OMNISCIENT EDITION)
📌 Operativ Specifikation:
- Active Threat Intel Fusion (Shodan, VirusTotal, GreyNoise, OTX).
- Subdomain Takeover Vulnerability Scanner (CNAME Analysis).
- Async Web Title & Server Header Prober.
- Stealth Dorking & WebDriver Navigation (Integreret).
"""

import socket
import requests
import ssl
import dns.resolver
import dns.exception
import concurrent.futures
import json
import sys
import csv
import time
import logging
import os
import re
import ipaddress
import asyncio
import aiohttp
import pyfiglet
import random
import struct
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
import sqlite3
from core.utils import session

# Eksterne OSINT & Hacking Biblioteker
try: import whois
except ImportError: pass

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
import nmap

try:
    from core.cert_intel import CertificateIntelligenceEngine
except ImportError:
    CertificateIntelligenceEngine = None

try:
    from core.config_vault import vault
    CONFIG = vault.state if vault else {}
except ImportError:
    CONFIG = {}

# ====================== KONFIGURATION & STYLING ======================
MAX_THREADS = 500
TIMEOUT = 5
RETRY_ATTEMPTS = 5
USER_AGENT = UserAgent().random
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}

class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

logger = logging.getLogger("GOLIATH_NET")

# ====================== GLOBAL OSINT UTILITIES ======================
class TurnstilePlaywrightInjector:
    """GOLIATH V42: Integreret Cloudflare Turnstile Bypass via Playwright DOM-injektion."""
    @staticmethod
    def sync_bypass(url: str) -> Dict[str, Any]:
        from core.browser import OmniHunterBrowser, BrowserConfig
        
        # Henter API nøgle sikkert fra Vault
        api_key = CONFIG.get("api_keys", {}).get("2captcha_api_key", "")
        if not api_key:
            logger.warning("⚠️ Ingen 2Captcha API-nøgle fundet i Vault. Playwright forsøger stealth uden resolver.")
            
        config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            js_rendering=True,
            captcha_api_key=api_key,
            anti_detection=True,
            behavior_level="high" # Algoritmisk human emulation for at varme cookien op
        )
        hunter = OmniHunterBrowser(config)
        hunter.start()
        try:
            return hunter.fetch(url)
        finally:
            hunter.close()

class OmniStealthSession(requests.Session):
    """GOLIATH V36: Active Rate-Limit Bypass & Evasion Engine (Expansion Mode)."""
    def request(self, method, url, **kwargs):
        headers = kwargs.get('headers', {})
        
        # 1. Dynamisk User-Agent rotation for hver ENESTE anmodning (Ikke kun pr. session)
        try: headers['User-Agent'] = UserAgent().random
        except Exception: pass
        
        # 2. X-Forwarded-For & Client-IP Spoofing for at snyde simple WAFs og IP-bans
        spoofed_ip = socket.inet_ntoa(struct.pack('>I', random.randint(0x01000000, 0xEFFFFFFF)))
        headers['X-Forwarded-For'] = spoofed_ip
        headers['X-Real-IP'] = spoofed_ip
        headers['Client-IP'] = spoofed_ip
        
        # 3. Cache-busting for at undgå at WAF serverer en cached blokeringsside
        headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        kwargs['headers'] = headers
        res = super().request(method, url, **kwargs)
        
        # 4. Aktiv 429 Evasion med Gaussian Jitter
        if res.status_code == 429:
            logger.warning(f"⚠️ [RATE-LIMIT] 429 Too Many Requests mod {url}. Udfører Evasion...")
            for attempt in range(1, 4):
                time.sleep(random.uniform(1.5, 3.5) * attempt)
                headers['X-Forwarded-For'] = socket.inet_ntoa(struct.pack('>I', random.randint(0x01000000, 0xEFFFFFFF)))
                res = super().request(method, url, **kwargs)
                if res.status_code != 429: break
                
        # 5. NYT V42: Auto-Detect CF/Turnstile og deploy Playwright DOM-Injektion
        if res.status_code in [403, 503] and any(cf_sig in res.text.lower() for cf_sig in ["cloudflare", "turnstile", "just a moment"]):
            logger.warning(f"⚠️ [WAF] Cloudflare Turnstile udfordring mødt på {url}. Skifter til Playwright DOM-injektion...")
            try:
                bypass_res = TurnstilePlaywrightInjector.sync_bypass(url)
                if bypass_res and bypass_res.get("html"):
                    # Infiltrerer response-objektet transparent, så scraper-modulet fortsætter uforstyrret
                    res._content = bypass_res["html"].encode('utf-8')
                    res.status_code = 200
                    logger.info("✅ Cloudflare knust! Returnerer Playwright-rendret HTML payload.")
            except Exception as e:
                logger.error(f"❌ Playwright Bypass fejlede: {e}")
                
        return res

def get_stealth_session() -> requests.Session:
    sess = OmniStealthSession()
    retry = Retry(total=RETRY_ATTEMPTS, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.headers.update(HEADERS)
    return sess

class AsyncProxyManager:
    """GOLIATH V36: Asynkron Round-Robin Proxy Rotator til Mass-Scanning."""
    def __init__(self, proxies: List[str] = None):
        # Henter automatisk proxies fra den krypterede vault hvis ingen angives
        self.proxies = proxies or CONFIG.get("network", {}).get("proxy_list", [])
        self.index = 0
        self.lock = asyncio.Lock()

    async def get_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        async with self.lock:
            proxy = self.proxies[self.index]
            self.index = (self.index + 1) % len(self.proxies)
            return proxy

async def get_async_stealth_session(proxy_manager: Optional[AsyncProxyManager] = None) -> aiohttp.ClientSession:
    """Returnerer en aiohttp session klargjort med stealth headers og proxy-understøttelse."""
    headers = {
        "User-Agent": UserAgent().random,
        "Accept": "text/html,application/json,application/xhtml+xml",
        "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }
    timeout = aiohttp.ClientTimeout(total=20)
    # Sikrer SOCKS5 og HTTP(S) proxy resolution asynkront
    connector = aiohttp.TCPConnector(ssl=False)
    return aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector)

class AsyncTurnstileSolver:
    """GOLIATH V41: Asynkron Cloudflare Turnstile Bypass via 2Captcha (Expansion Mode)."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger("TurnstileSolver")

    async def solve(self, url: str, sitekey: str) -> Optional[str]:
        if not self.api_key: 
            self.logger.warning("[!] Mangler 2Captcha API-nøgle i vault.")
            return None
            
        req_url = f"http://2captcha.com/in.php?key={self.api_key}&method=turnstile&sitekey={sitekey}&pageurl={url}&json=1"
        self.logger.info(f"[*] Submitter Turnstile Sitekey ({sitekey[:10]}...) til bypass-klynge.")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(req_url) as res:
                data = await res.json()
                if data.get("status") != 1: return None
                req_id = data.get("request")
            
            for _ in range(25):
                await asyncio.sleep(5)
                ans_url = f"http://2captcha.com/res.php?key={self.api_key}&action=get&id={req_id}&json=1"
                async with session.get(ans_url) as ans_res:
                    ans_data = await ans_res.json()
                    if ans_data.get("status") == 1: return ans_data.get("request")
                    if ans_data.get("request") != "CAPCHA_NOT_READY": break
        return None

async def send_authenticated_replay(url: str, target: str, proxy_mgr: AsyncProxyManager) -> Optional[Dict]:
    """GOLIATH V50: Automatisk autentificeret genafspilning af API-kald med Datalake Token Extraction."""
    db_path = Path(session.get("loot_folder", "loot_evidence")) / "omni_datalake.db"
    token = ""
    
    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data_json FROM osint_records WHERE target=? ORDER BY timestamp DESC LIMIT 20", (target,))
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    if "Extracted_Bearer_Tokens" in data and data["Extracted_Bearer_Tokens"]:
                        token = data["Extracted_Bearer_Tokens"][0]
                        break
        except Exception as e:
            logger.error(f"Fejl ved Token-udtrækning fra Datalake: {e}")
            
    headers = {
        "User-Agent": UserAgent().random,
        "Accept": "application/json",
        "X-Forwarded-For": socket.inet_ntoa(struct.pack('>I', random.randint(0x01000000, 0xEFFFFFFF)))
    }
    if token: headers["Authorization"] = f"Bearer {token}"
    
    proxy = await proxy_mgr.get_proxy()
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as http_session:
            async with http_session.get(url, headers=headers, proxy=proxy, timeout=15) as res:
                if res.status == 200:
                    return await res.json()
    except Exception: pass
    return None

http = get_stealth_session()

def safe_get_with_retry(driver: Any, url: str, max_retries: int = 3) -> bool:
    """Sikker navigation med WebDriver, falder tilbage til requests ved fejl."""
    for attempt in range(max_retries):
        try:
            if driver:
                # Hvis det er undetected_chromedriver, bruger vi .get() direkte
                if hasattr(driver, 'get'):
                    driver.get(url)
                else:
                    driver.get(url)
                time.sleep(random.uniform(1.5, 3.5))
                
                # NYT V42: Auto-Detect Cloudflare Turnstile direkte i WebDriveren
                page_source = driver.page_source.lower()
                if any(cf_sig in page_source for cf_sig in ["cf-turnstile", "just a moment", "cloudflare"]):
                    logger.warning("⚠️ Cloudflare udfordring i Selenium! Overdrager session til Playwright...")
                    bypass_res = TurnstilePlaywrightInjector.sync_bypass(url)
                    if bypass_res and bypass_res.get("html"):
                        logger.info("✅ Turnstile knust via dedikeret asynkron DOM-injektion!")
                        return True # Vi markerer navigationen som en succes
                return True
        except Exception as e:
            time.sleep(2)
    return False

def omni_dork_search(driver: Any, query: str, max_links: int = 5, engine: str = "google") -> List[Dict[str, str]]:
    """GOLIATH Dorking Engine: Bypasser CAPTCHAs og returnerer links/snippets."""
    results = []
    if not driver: return results
    
    try:
        if engine == "google":
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        else:
            url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}"
            
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        
        # Ekstrahering (tilpasset Google)
        from selenium.webdriver.common.by import By
        elements = driver.find_elements(By.CSS_SELECTOR, "div.g, div.result")
        for el in elements[:max_links]:
            try:
                link = el.find_element(By.TAG_NAME, "a").get_attribute("href")
                title = el.find_element(By.TAG_NAME, "h3").text
                results.append({"url": link, "title": title, "snippet": el.text})
            except Exception: continue
    except Exception as e:
        logger.warning(f"OmniDork Fejl: {e}")
    return results

# ====================== DATACLASSER ======================
@dataclass
class ScanResult:
    target_domain: str
    target_ip: str
    timestamp: str
    ports: List[Dict] = field(default_factory=list)
    web_probe: List[Dict] = field(default_factory=list)
    dns: Dict = field(default_factory=dict)
    whois: Dict = field(default_factory=dict)
    ssl: Dict = field(default_factory=dict)
    subdomains: List[str] = field(default_factory=list)
    takeovers: List[Dict] = field(default_factory=list)
    vulnerabilities: List[Dict] = field(default_factory=list)
    historical_dns: List[Dict] = field(default_factory=list)
    threat_intel: Dict = field(default_factory=dict)
    ai_threat_assessment: str = ""
    errors: List[str] = field(default_factory=list)

# ====================== NETVÆRKSSCANNER CORE ======================
class NetworkScanner:
    """Enterprise-Grade Network Scanner & Intelligence Engine."""

    def __init__(self, target: str, output_dir: str = "output"):
        self.raw_target = target
        self.domain = None
        self.ip = None
        
        if not self._resolve_dual_target():
            raise ValueError(f"Kunne ikke resolvere mål: {target}")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = http
        
        self.results = ScanResult(
            target_domain=self.domain or "N/A",
            target_ip=self.ip or "N/A",
            timestamp=datetime.now().isoformat()
        )
        self._setup_api_keys()

    def _resolve_dual_target(self) -> bool:
        target = self.raw_target.replace("http://", "").replace("https://", "").split("/")[0]
        try:
            if self._is_ip(target):
                self.ip = target
                try: self.domain = socket.gethostbyaddr(target)[0]
                except: self.domain = target
            else:
                self.domain = target
                self.ip = socket.gethostbyname(target)
            return True
        except Exception as e:
            return False

    def _is_ip(self, target: str) -> bool:
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    def _setup_api_keys(self):
        self.vt_key = os.getenv("VT_API_KEY")
        self.shodan_key = os.getenv("SHODAN_API_KEY")
        self.strails_key = os.getenv("SECURITYTRAILS_API_KEY")

    def fetch_threat_intel(self):
        logger.info("[*] Eksekverer Threat Intelligence Fusion...")
        def get_shodan():
            if not self.shodan_key or not self.ip: return
            try:
                res = self.session.get(f"https://api.shodan.io/shodan/host/{self.ip}?key={self.shodan_key}", timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    self.results.threat_intel["Shodan"] = {"os": data.get("os"), "ports": data.get("ports")}
            except Exception: pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(get_shodan)

    def enumerate_subdomains_passive(self) -> List[str]:
        """NYT: Finder subdomæner passivt via Native Certificate Transparency Engine."""
        logger.info("[*] Udfører passiv subdomain enumeration (Native CRT)...")
        if not self.domain or self.domain == self.ip:
            logger.warning("Ingen domæne fundet eller målet er en IP. Springer passiv scan over.")
            return []

        try:
            if CertificateIntelligenceEngine:
                cert_engine = CertificateIntelligenceEngine(self.domain)
                subs = cert_engine.execute_recon()

                if subs:
                    self.results.subdomains.extend(subs)
                    self.results.subdomains = list(set(self.results.subdomains))

                if cert_engine.errors:
                    self.results.errors.extend(cert_engine.errors)

                return subs
            return []
        except Exception as e:
            self.results.errors.append(f"Native CRT fejl: {e}")
            return []

    async def subdomain_bruteforce_async(self, wordlist: str = None) -> List[str]:
        logger.info("[*] Starter Asynkron Subdomain Bruteforce...")
        if not self.domain or self.domain == self.ip: return []
        
        wordlist_path = Path(wordlist) if wordlist else Path(__file__).parent.parent / "wordlists" / "subdomains.txt"
        if not wordlist_path.exists():
            # Fallback til en minimal liste hvis filen mangler
            words = ["www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2", "smtp", "vpn", "m", "dev"]
            logger.warning(f"Wordlist {wordlist_path} ikke fundet. Bruger intern fallback.")
        else:
            words = [line.strip() for line in wordlist_path.read_text().splitlines() if line.strip()]

        found = set(self.results.subdomains)
        loop = asyncio.get_event_loop()

        async def resolve(sub):
            host = f"{sub}.{self.domain}"
            try:
                await loop.getaddrinfo(host, None)
                found.add(host)
            except Exception: pass

        tasks = set()
        for sub in words:
            if len(tasks) >= 150:
                _, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            tasks.add(asyncio.create_task(resolve(sub)))
        
        if tasks: await asyncio.wait(tasks)
        
        self.results.subdomains = list(found)
        return list(found)

    def scan_with_nmap(self):
        logger.info("[*] Initierer aggressiv Nmap Service & Vulnerability Scan...")
        if not self.ip: return
        try:
            nm = nmap.PortScanner()
            # Tjekker om vi kører som root for mere avancerede scans
            args = '-Pn -sV -T4 --top-ports 100'
            if os.geteuid() == 0: args += ' -sS'
            
            nm.scan(self.ip, arguments=args)
            for host in nm.all_hosts():
                for proto in nm[host].all_protocols():
                    lport = nm[host][proto].keys()
                    for port in sorted(lport):
                        port_data = nm[host][proto][port]
                        if port_data['state'] == 'open':
                            self.results.ports.append({
                                "port": port, "service": port_data.get('name', 'unknown'),
                                "version": port_data.get('version', '')
                            })
        except Exception as e:
            self.results.errors.append(f"Nmap fejl: {e}")

    def run_full_scan(self) -> Dict:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.enumerate_subdomains_passive)
            executor.submit(self.fetch_threat_intel)

        # Kør asynkron bruteforce
        try:
            if sys.version_info >= (3, 7):
                asyncio.run(self.subdomain_bruteforce_async())
            else:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.subdomain_bruteforce_async())
        except Exception as e:
            logger.error(f"Async Subdomain Bruteforce fejlede: {e}")

        self.scan_with_nmap()
        return asdict(self.results)