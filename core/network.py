# -*- coding: utf-8 -*-
"""
GOLIATH NETWORK GRANDMASTER (V35: OMNISCIENT EDITION)
Operativ Specifikation:
- Active Threat Intel Fusion (Shodan, VirusTotal, GreyNoise, OTX).
- Subdomain Takeover Vulnerability Scanner (CNAME Analysis).
- Async Web Title & Server Header Prober.
- Dual-Target Resolution (Bevarer både Domæne og IP).
- Passive Subdomain Discovery via crt.sh (Certificate Transparency).
- Historical DNS via SecurityTrails.
- Asynchronous Banner Grabbing & Port Scanning.
- Nmap Fallback & Vulnerability Enumeration.
- Mistral AI Threat Assessment Generation.
"""

import socket
import requests
import ssl
import dns.resolver
import dns.exception
import concurrent.futures
import json
import csv
import time
import logging
import os
import re
import ipaddress
import asyncio
import aiohttp
import pyfiglet
from urllib.parse import urlparse
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

# Eksterne OSINT & Hacking Biblioteker
import whois
import OpenSSL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
import nmap
import paramiko
from core.cert_intel import CertificateIntelligenceEngine
from securitytrails import SecurityTrails
from shodan import Shodan
from censys.search import CensysSearchClient
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler("omni_hunter_network.log"), logging.StreamHandler()])
logger = logging.getLogger("GOLIATH_NET")

# ====================== DATACLASSER ======================
@dataclass
class ScanResult:
    target_domain: str
    target_ip: str
    timestamp: str
    ports: List[Dict] = field(default_factory=list)
    web_probe: List[Dict] = field(default_factory=list)      # NYT: Web Title og Headers
    dns: Dict = field(default_factory=dict)
    whois: Dict = field(default_factory=dict)
    ssl: Dict = field(default_factory=dict)
    subdomains: List[str] = field(default_factory=list)
    takeovers: List[Dict] = field(default_factory=list)      # NYT: Subdomain Takeovers
    vulnerabilities: List[Dict] = field(default_factory=list)
    historical_dns: List[Dict] = field(default_factory=list)
    threat_intel: Dict = field(default_factory=dict)         # NYT: VT, Shodan, GreyNoise data
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
        self.session = self._create_session()
        self.proxy = None
        
        self.results = ScanResult(
            target_domain=self.domain or "N/A",
            target_ip=self.ip or "N/A",
            timestamp=datetime.now().isoformat()
        )
        self._setup_api_keys()

    def _print_banner(self):
        banner = pyfiglet.figlet_format("GOLIATH NET", font="slant")
        print(f"{C.CYAN}{banner}{C.RESET}")
        print(f"{C.YELLOW}[*] Target Domain: {self.domain} | Target IP: {self.ip}{C.RESET}\n")

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
            logger.error(f"Target resolution fejl: {e}")
            return False

    def _is_ip(self, target: str) -> bool:
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    def _create_session(self) -> requests.Session:
        sess = requests.Session()
        retry = Retry(total=RETRY_ATTEMPTS, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
        sess.headers.update(HEADERS)
        return sess

    def _setup_api_keys(self):
        """Henter API nøgler sikkert til de direkte requests."""
        def load_key(env_var, config_key):
            return os.getenv(env_var)
            
        self.vt_key = load_key("VT_API_KEY", "virus_total")
        self.shodan_key = load_key("SHODAN_API_KEY", "shodan")
        self.greynoise_key = load_key("GREYNOISE_API_KEY", "greynoise")
        self.strails_key = load_key("SECURITYTRAILS_API_KEY", "securitytrails")
        self.ai_client = MistralClient(api_key=load_key("MISTRAL_API_KEY", "mistral")) if load_key("MISTRAL_API_KEY", "mistral") else None

    # ====================== THREAT INTELLIGENCE FUSION (NYT I V35) ======================
    def fetch_threat_intel(self):
        """Henter data fra Shodan, VirusTotal og GreyNoise parallelt ved hjælp af requests (sikrer at det rutes gennem vores session/proxy)."""
        logger.info("[*] Eksekverer Threat Intelligence Fusion (Shodan/VT/GreyNoise)...")
        
        def get_shodan():
            if not self.shodan_key or not self.ip: return
            try:
                res = self.session.get(f"https://api.shodan.io/shodan/host/{self.ip}?key={self.shodan_key}", timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    self.results.threat_intel["Shodan"] = {
                        "os": data.get("os"), "isp": data.get("isp"), "ports": data.get("ports"), "vulns": data.get("vulns", [])
                    }
                    if data.get("vulns"): logger.warning(f"{C.RED}[!] Shodan fandt CVE'er: {len(data['vulns'])}{C.RESET}")
            except Exception: pass

        def get_virustotal():
            if not self.vt_key: return
            try:
                headers = {"x-apikey": self.vt_key}
                target = self.domain if self.domain and self.domain != self.ip else self.ip
                type_endpoint = "domains" if not self._is_ip(target) else "ip_addresses"
                res = self.session.get(f"https://www.virustotal.com/api/v3/{type_endpoint}/{target}", headers=headers, timeout=10)
                if res.status_code == 200:
                    stats = res.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    self.results.threat_intel["VirusTotal"] = stats
                    if stats.get("malicious", 0) > 0: logger.warning(f"{C.RED}[!] VirusTotal Flag: {stats['malicious']} motorer detekterede trusler.{C.RESET}")
            except Exception: pass

        def get_greynoise():
            if not self.greynoise_key or not self.ip: return
            try:
                headers = {"key": self.greynoise_key}
                res = self.session.get(f"https://api.greynoise.io/v3/community/{self.ip}", headers=headers, timeout=10)
                if res.status_code == 200:
                    gn_data = res.json()
                    self.results.threat_intel["GreyNoise"] = {
                        "classification": gn_data.get("classification"),
                        "name": gn_data.get("name"),
                        "riot": gn_data.get("riot")
                    }
                    if gn_data.get("classification") == "malicious":
                        logger.warning(f"{C.RED}[!] GreyNoise kategoriserer IP som ondsindet scanner!{C.RESET}")
            except Exception: pass

        # Kør API opslag parallelt
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(get_shodan)
            executor.submit(get_virustotal)
            executor.submit(get_greynoise)

    # ====================== OSINT & PASSIVE RECON ======================
    def fetch_historical_dns(self):
        logger.info("[*] Henter historisk DNS via SecurityTrails...")
        if not self.strails_key or not self.domain or self.domain == self.ip: return
            
        url = f"https://api.securitytrails.com/v1/history/{self.domain}/dns/a"
        headers = {"APIKEY": self.strails_key, "Accept": "application/json"}
        try:
            res = self.session.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                records = res.json().get('records', [])
                self.results.historical_dns = [{"ip": r['values'][0]['ip'], "first_seen": r['first_seen'], "last_seen": r['last_seen']} for r in records]
                logger.info(f"{C.GREEN}[+] Fandt {len(records)} historiske DNS records!{C.RESET}")
        except Exception as e:
            self.results.errors.append(f"SecurityTrails Fejl: {e}")

    def enumerate_subdomains_passive(self) -> List[str]:
    """NYT: Finder subdomæner passivt via Native Certificate Transparency Engine."""
    logger.info("[*] Udfører passiv subdomain enumeration (Native CRT)...")
    if not self.domain or self.domain == self.ip: return []

    try:
        # Initialiserer vores nye Native Engine
        cert_engine = CertificateIntelligenceEngine(self.domain)
        subs = cert_engine.execute_recon()

        if subs:
            self.results.subdomains.extend(subs)
            # Fjern potentielle dubletter
            self.results.subdomains = list(set(self.results.subdomains))

        if cert_engine.errors:
            self.results.errors.extend(cert_engine.errors)

        return subs
    except Exception as e:
        self.results.errors.append(f"Native CRT fejl: {e}")
        return []

    async def subdomain_bruteforce_async(self, wordlist: str = None) -> List[str]:
        logger.info("[*] Starter Asynkron Subdomain Bruteforce...")
        if not self.domain or self.domain == self.ip: return []
        
        wordlist_path = wordlist or str(Path(__file__).parent / "wordlists" / "subdomains.txt")
        if not Path(wordlist_path).exists(): return []

        with open(wordlist_path, "r") as f:
            words = [line.strip() for line in f if line.strip()]

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
        logger.info(f"{C.GREEN}[+] Bruteforce komplet. Totalt unikke subdomæner: {len(found)}{C.RESET}")
        return list(found)

    # ====================== SUBDOMAIN TAKEOVER & WEB PROBER (NYT I V35) ======================
    def check_subdomain_takeovers(self):
        """NYT: Tjekker CNAME records for at finde dangling DNS der peger på uregistrerede cloud services."""
        logger.info("[*] Scanner subdomæner for Subdomain Takeover sårbarheder...")
        takeover_signatures = {
            "github.io": "There isn't a GitHub Pages site here",
            "herokuapp.com": "No such app",
            "s3.amazonaws.com": "NoSuchBucket",
            "myshopify.com": "Sorry, this shop is currently unavailable",
            "zendesk.com": "Help Center Closed"
        }
        
        for sub in self.results.subdomains:
            try:
                answers = dns.resolver.resolve(sub, 'CNAME')
                for rdata in answers:
                    cname = str(rdata.target).strip('.')
                    for provider, error_sig in takeover_signatures.items():
                        if provider in cname:
                            # Verify if the target actually returns the error signature
                            try:
                                res = self.session.get(f"http://{sub}", timeout=5)
                                if error_sig in res.text:
                                    logger.warning(f"{C.RED}[!] KRITISK: Mulig Subdomain Takeover på {sub} (Peger på {cname}){C.RESET}")
                                    self.results.takeovers.append({"subdomain": sub, "cname": cname, "provider": provider})
                            except: pass
            except Exception: pass

    async def probe_web_titles(self):
        """NYT: Asynkron web-prober for at hente <title> og Server headers på åbne webporte."""
        logger.info("[*] Prober HTTP/HTTPS porte for Web Teknologi og Titler...")
        
        async def fetch(url):
            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as sess:
                    async with sess.get(url, timeout=5) as resp:
                        text = await resp.text()
                        title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE)
                        title = title_match.group(1).strip() if title_match else "Ingen Titel"
                        server = resp.headers.get('Server', 'Ukendt')
                        
                        logger.info(f"{C.CYAN}  -> [Web] {url} | Server: {server} | Titel: {title}{C.RESET}")
                        self.results.web_probe.append({"url": url, "status": resp.status, "title": title, "server": server})
            except Exception: pass

        tasks = []
        # Tjekker primært domæne/IP
        for port in [80, 443, 8080, 8443]:
            protocol = "https" if port in [443, 8443] else "http"
            tasks.append(fetch(f"{protocol}://{self.domain or self.ip}:{port}"))
            
        # Hvis vi har mange subdomæner, tag en stikprøve af de 20 første
        for sub in self.results.subdomains[:20]:
            tasks.append(fetch(f"https://{sub}"))
            
        await asyncio.gather(*tasks)

    # ====================== ACTIVE SCANNING ======================
    def scan_with_nmap(self):
        logger.info("[*] Initierer aggressiv Nmap Service & Vulnerability Scan...")
        if not self.ip: return
        try:
            nm = nmap.PortScanner()
            nm.scan(self.ip, arguments='-Pn -sV -A --script vuln -p 21,22,80,443,445,3306,3389,8080')
            
            for host in nm.all_hosts():
                for proto in nm[host].all_protocols():
                    lport = nm[host][proto].keys()
                    for port in sorted(lport):
                        port_data = nm[host][proto][port]
                        if port_data['state'] == 'open':
                            vulns = [{k: v} for k, v in port_data.get('script', {}).items()]
                            self.results.ports.append({
                                "port": port, "service": port_data.get('name', 'unknown'),
                                "version": port_data.get('version', ''), "product": port_data.get('product', '')
                            })
                            if vulns:
                                self.results.vulnerabilities.extend([{"port": port, "vulns": vulns}])
                                logger.warning(f"{C.RED}[!] Sårbarhed fundet på port {port}!{C.RESET}")
        except Exception as e:
            self.results.errors.append(f"Nmap fejl: {e}")

    def scan_dns(self) -> Dict:
        logger.info("[*] Eksekverer DNS Enumering...")
        record_types = ["A", "AAAA", "MX", "TXT", "NS", "SOA"]
        dns_records = {}
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(self.domain or self.target, record_type)
                dns_records[record_type] = [str(r) for r in answers]
            except Exception: pass
        self.results.dns = dns_records
        return dns_records

    def whois_lookup(self) -> Dict:
        logger.info("[*] Eksekverer WHOIS Opslag...")
        try:
            info = whois.whois(self.domain or self.ip)
            self.results.whois = dict(info)
            return dict(info)
        except Exception as e:
            self.results.errors.append(f"WHOIS Fejl: {e}")
            return {}

    def ssl_certificate_analysis(self) -> Dict:
        logger.info("[*] Eksekverer SSL/TLS Certifikat Analyse...")
        if not self.domain: return {}
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=TIMEOUT) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
            
            cert_clean = {
                "issuer": str(cert.get("issuer")), "subject": str(cert.get("subject")),
                "notBefore": cert.get("notBefore"), "notAfter": cert.get("notAfter"), "version": cert.get("version")
            }
            
            not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            if (not_after - datetime.now()).days < 30:
                self.results.vulnerabilities.append({"type": "SSL", "desc": "Certifikat udløber om under 30 dage!"})
                
            self.results.ssl = cert_clean
            return cert_clean
        except Exception as e:
            self.results.errors.append(f"SSL Fejl: {e}")
            return {}

    # ====================== AI TRUSSELSVURDERING ======================
    def generate_ai_assessment(self):
        if not self.ai_client:
            logger.info("Skipper AI Analyse (Mangler Mistral API Nøgle).")
            return

        logger.info(f"{C.MAGENTA}[*] Fodrer netværksdata til Mistral AI for Cyber Threat Assessment...{C.RESET}")
        
        prompt_data = {
            "Target": self.domain or self.ip,
            "Open Ports": self.results.ports,
            "Vulnerabilities": self.results.vulnerabilities,
            "Subdomain Takeovers": self.results.takeovers,
            "Threat Intel (VT/Shodan/GreyNoise)": self.results.threat_intel
        }

        prompt = f"""
        Du er en Senior Penetration Tester og OSINT Analyst for PET.
        Gennemgå følgende omfattende netværksdata og skriv et professionelt Executive Summary (på dansk) 
        med fokus på kritiske fund, CNAME takeovers, port-sårbarheder og Threat Intelligence advarsler.
        Vær præcis og kynisk i din vurdering.
        Data: {json.dumps(prompt_data)}
        """

        try:
            messages = [ChatMessage(role="user", content=prompt)]
            response = self.ai_client.chat(model="mistral-large-latest", messages=messages)
            self.results.ai_threat_assessment = response.choices[0].message.content
            logger.info(f"{C.GREEN}[+] AI Threat Assessment Genereret!{C.RESET}")
        except Exception as e:
            self.results.errors.append(f"AI Analyse fejlede: {e}")

    # ====================== EKSPORT ======================
    def save_results(self, fmt: str = "json") -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.domain or self.ip}_{timestamp}"

        if fmt == "json":
            filepath = self.output_dir / f"{filename}.json"
            with open(filepath, "w") as f: json.dump(asdict(self.results), f, indent=4)
                
        elif fmt == "html":
            filepath = self.output_dir / f"{filename}.html"
            
            # HTML er opgraderet til at vise Takeovers, Web Probes og Threat Intel
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2f; color: #cfd2d9; margin: 40px; }}
                    h1 {{ color: #00e5ff; border-bottom: 2px solid #3b3b54; padding-bottom: 10px; }}
                    h2 {{ color: #ff007f; margin-top: 0; }}
                    .box {{ background: #27293d; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; border-left: 4px solid #00e5ff; }}
                    .box-critical {{ border-left: 4px solid #ff007f; }}
                    .badge {{ background: #3b3b54; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 10px; color: #00e5ff; }}
                    .badge-red {{ background: #ff007f; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 10px; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ background: #1e1e2f; margin: 5px 0; padding: 10px; border-radius: 4px; border: 1px solid #3b3b54; }}
                </style>
            </head>
            <body>
                <h1>🌐 GOLIATH NETWORK GRANDMASTER: {self.domain or self.ip}</h1>
                
                <div class="box box-critical">
                    <h2>🧠 AI Cyber Threat Assessment</h2>
                    <p>{self.results.ai_threat_assessment.replace(chr(10), '<br>') if self.results.ai_threat_assessment else 'Ingen AI analyse kørt.'}</p>
                </div>
                
                <div class="box">
                    <h2>🚨 Threat Intelligence (Shodan/VT/GreyNoise)</h2>
                    <pre style="color: #cfd2d9;">{json.dumps(self.results.threat_intel, indent=4)}</pre>
                </div>
                
                <div class="box box-critical">
                    <h2>⚠️ Subdomain Takeovers ({len(self.results.takeovers)})</h2>
                    <ul>{''.join([f"<li><span class='badge-red'>KRITISK</span> <strong>{t['subdomain']}</strong> peger på forladt {t['provider']} ({t['cname']})</li>" for t in self.results.takeovers]) if self.results.takeovers else '<li>Ingen takeovers fundet.</li>'}</ul>
                </div>
                
                <div class="box">
                    <h2>💻 Web Probes (Title & Server Headers)</h2>
                    <ul>{''.join([f"<li><span class='badge'>HTTP {p['status']}</span> <strong>{p['url']}</strong> | Server: {p['server']} | Title: {p['title']}</li>" for p in self.results.web_probe]) if self.results.web_probe else '<li>Ingen web probes udført.</li>'}</ul>
                </div>

                <div class="box">
                    <h2>🎯 Åbne Porte & Services (Nmap)</h2>
                    <ul>{''.join([f"<li><span class='badge'>Port {p['port']}</span> {p.get('service', 'Ukendt')} - {p.get('product', '')} {p.get('version', '')}</li>" for p in self.results.ports]) if self.results.ports else '<li>Ingen åbne porte fundet.</li>'}</ul>
                </div>
                
                <div class="box">
                    <h2>🛡️ Subdomæner ({len(self.results.subdomains)})</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                        {''.join([f"<div style='background: #1e1e2f; padding: 5px; border: 1px solid #3b3b54;'>{s}</div>" for s in self.results.subdomains[:90]])}
                    </div>
                </div>
            </body>
            </html>
            """
            with open(filepath, "w", encoding="utf-8") as f: f.write(html)
        
        logger.info(f"{C.GREEN}Resultater gemt til: {filepath}{C.RESET}")

    def run_full_scan(self) -> Dict:
        self._print_banner()
        
        # 1. Parallelt I/O arbejde (Hurtige ting og Threat Intel API'er)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.scan_dns)
            executor.submit(self.whois_lookup)
            executor.submit(self.ssl_certificate_analysis)
            executor.submit(self.fetch_historical_dns)
            executor.submit(self.enumerate_subdomains_passive)
            executor.submit(self.fetch_threat_intel) # NYT

        # 2. Asynkront Subdomain Bruteforce & Web Probing
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.subdomain_bruteforce_async())
            
            # Kør synkron takeover test og asynkron web prober
            self.check_subdomain_takeovers() # NYT
            loop.run_until_complete(self.probe_web_titles()) # NYT
        except Exception as e:
            logger.error(f"Async operations fejlede: {e}")

        # 3. Tungt netværksarbejde (Nmap Port/Vuln Scan)
        self.scan_with_nmap()

        # 4. AI Vurdering (Med al den nye kontekst)
        self.generate_ai_assessment()

        # 5. Eksport
        self.save_results("json")
        self.save_results("html")
        return asdict(self.results)