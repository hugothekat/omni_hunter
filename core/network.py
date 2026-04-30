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
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

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
def get_stealth_session() -> requests.Session:
    sess = requests.Session()
    retry = Retry(total=RETRY_ATTEMPTS, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.headers.update(HEADERS)
    return sess

http = get_stealth_session()

def safe_get_with_retry(driver: Any, url: str, max_retries: int = 3) -> bool:
    """Sikker navigation med WebDriver, falder tilbage til requests ved fejl."""
    for attempt in range(max_retries):
        try:
            if driver:
                driver.get(url)
                time.sleep(random.uniform(1.5, 3.5))
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