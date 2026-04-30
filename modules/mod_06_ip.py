# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import time
import json
import os
import re
import email
import email.policy
import socket
import asyncio
import aiohttp
import threading
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake, sanitize_filename
from core.utils import C, session, datalake
from core.network import omni_dork_search

try:
    from core.config_vault import vault
    CONFIG = vault.state if vault else {}
    import nmap
except ImportError:
    CONFIG = {}
    nmap = None

# =========================================================================
# ADVANCED PYDANTIC INFRASTRUCTURE MODELS
# =========================================================================
class LocationData(BaseModel):
    country: str = "Unknown"
    city: str = "Unknown"
    latitude: float = 0.0
    longitude: float = 0.0
    isp: str = "Unknown"
    precision_level: str = "Network" # 'Network' (IP) eller 'Street' (BSSID)
try:
    import whois
except ImportError:
    whois = None

class ThreatRecord(BaseModel):
    source: str
    malicious_votes: int = 0
    total_votes: int = 0
    tags: List[str] = Field(default_factory=list)
    last_analysis_date: Optional[str] = None
try:
    import dns.resolver
except ImportError:
    dns = None

class HistoricalEndpoint(BaseModel):
    url: str
    status_code: str
    timestamp: str
    mime_type: str

class InfraIntelNode(BaseModel):
    target: str
    target_type: str # 'IP', 'DOMAIN', or 'BSSID'
    resolves_to: List[str] = Field(default_factory=list) # IPs for domæner, Domæner for IPs
    location: LocationData = Field(default_factory=LocationData)
    threat_intel: ThreatRecord = Field(default_factory=lambda: ThreatRecord(source="None"))
    historical_endpoints: List[HistoricalEndpoint] = Field(default_factory=list)
    ssl_certificates: List[str] = Field(default_factory=list)
    open_ports: List[int] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# =========================================================================
# THE APEX INFRASTRUCTURE CORE
# =========================================================================
class OmniInfrastructureTracker(BaseModule):
    """
    GOLIATH V36: THE OMNI INFRASTRUCTURE TRACKER [MODUL 06]
    Universel udtrækning af IP-adresser fra PCAP, EML, Emails, Domæner og Navne.
    """
    def __init__(self):
        super().__init__()
        self.name = "OMNI-NETWORK & INFRASTRUCTURE ENGINE"
        self.description = "Dyb asynkron analyse af IP, Domæner, BSSID (Wigle), Wayback og VirusTotal."
        self.category = ModuleCategory.NETWORK
        self.print_lock = threading.Lock()
        self.data = {
            "Target": "",
            "Target_Type": "",
            "Fundne_IPer": [],
            "IP_Detaljer": {},
            "WHOIS_Data": {},
            "Tracking_Pixels": [],
            "Timestamp": datetime.now().isoformat()
        }
        self.target_ips = set()

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[06] OMNI INFRASTRUCTURE TRACKER V36\n{'='*60}{C.RESET}")
        self.target = target.strip()
        self.data["Target"] = self.target
        
    def _log(self, message: str, level: str = "INFO", indent: int = 0) -> None:
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "ERROR": C.RED, "SUCCESS": C.GREEN, "PIVOT": C.MAGENTA, "CRITICAL": C.RED}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "  " * indent
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {prefix}[{color}{level}{C.RESET}] {message}\n")

    def _determine_target_type(self, target: str) -> str:
        target = target.strip()
        if os.path.isfile(target) and target.lower().endswith(('.pcap', '.pcapng')):
            return "PCAP_FILE"
        if os.path.isfile(target) and target.lower().endswith('.eml'):
            return "EML_FILE"
        # BSSID (MAC Address)
        if re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", target):
            return "BSSID"
        # IPv4
        elif re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", target):
            return "IP"
        # Domain (Simplificeret check)
        elif re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
            return "DOMAIN"
        return "UNKNOWN"

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        """BaseModule Compliance Run-funktion."""
        self.raw_target = target.strip() if target else session.get("name", "")
        if not self.raw_target:
            self._log("Ingen target (IP/Domain/BSSID) angivet. Afbryder.", "ERROR")
            return {}

        self.target_type = self._determine_target_type(self.raw_target)
        if self.target_type == "UNKNOWN":
            self._log(f"Kunne ikke klassificere target format: {self.raw_target}", "ERROR")
            return {}

        self.vt_api_key = CONFIG.get("api_keys", {}).get("virustotal_api_key", "")
        self.wigle_api_key = CONFIG.get("api_keys", {}).get("wigle_api_key", "")

        self.node = InfraIntelNode(target=self.raw_target, target_type=self.target_type)

        print(f"\n{C.BG_RED}{C.WHITE} === THE OMNI-NETWORK JUGGERNAUT V39 ENGAGED === {C.RESET}\n")
        self._log(f"Initiating Global Infrastructure Sequence for: {self.raw_target} [TYPE: {self.target_type}]", "INFO")

        # FASE 1: Lokal Resolution
        if self.target_type == "PCAP_FILE":
            self._parse_pcap_file(self.raw_target)
        elif self.target_type == "EML_FILE":
            self._parse_eml_file(self.raw_target)
        elif self.target_type == "DOMAIN":
            self._phase_1_local_resolution()
            self._resolve_domain(self.raw_target)
            self._run_whois(self.raw_target)
        else:
            self._phase_1_local_resolution()

        # FASE 2: Asynkron API Matrix (VT, Wayback, GeoIP, Certs)
        self._log("FASE 2: Executing Parallel API Matrix (Geo, Threat, Historical)...", "INFO")
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(self._phase_2_async_execution())
        except Exception as e:
            self._log(f"Async Loop failed: {e}", "ERROR", indent=1)

        if not self.target_ips and self.target_type != "BSSID":
             self._log("Ingen IP-adresser kunne udtrækkes fra inputtet.", "WARN", indent=1)
             self.data["Fundne_IPer"] = []

        # FASE 3: Output & Arkivering
        self._phase_3_finalize()
        return self.node.dict()

    # =========================================================================
    # FASE 1: SYNCHRONOUS PRE-CHECKS (DNS)
    # =========================================================================
    def _phase_1_local_resolution(self):
        if self.target_type == "DOMAIN":
            try:
                ip = socket.gethostbyname(self.raw_target)
                self.node.resolves_to.append(ip)
                self._log(f"Domain Resolves to IPv4: {ip}", "SUCCESS", indent=1)
                self.target_ips.add(ip)
            except Exception:
                self._log("Domain DNS resolution failed.", "WARN", indent=1)
        elif self.target_type == "IP":
            try:
                host = socket.gethostbyaddr(self.raw_target)
                self.node.resolves_to.append(host[0])
                self._log(f"IPv4 Resolves to Host: {host[0]}", "SUCCESS", indent=1)
                self.target_ips.add(self.raw_target)
            except Exception:
                self._log("Reverse DNS resolution failed.", "WARN", indent=1)

    def _parse_pcap_file(self, filepath: str):
        self._log(f"Parser PCAP netværksdump for eksterne IP-adresser: {filepath}", "INFO", indent=1)
        try:
            from scapy.all import PcapReader, IP
            found_ips = set()
            with PcapReader(filepath) as pcap:
                for pkt in pcap:
                    if IP in pkt:
                        for ip in (pkt[IP].src, pkt[IP].dst):
                            if not ip.startswith(("10.", "192.168.", "127.", "172.16.", "255.255.", "0.")):
                                found_ips.add(ip)
            for ip in found_ips:
                self.target_ips.add(ip)
                if ip not in self.node.resolves_to:
                    self.node.resolves_to.append(ip)
            self._log(f"Udtræk fuldført! Fandt {len(found_ips)} unikke offentlige IP-adresser i PCAP.", "SUCCESS", indent=2)
        except ImportError:
            self._log("Mangler 'scapy'. System Auto-Healer vil prøve at installere, ellers kør: pip install scapy", "ERROR", indent=1)
        except Exception as e:
            self._log(f"PCAP Parse Fejl (Filen kan være korrupt): {e}", "ERROR", indent=1)

    def _parse_eml_file(self, filepath: str):
        print(f"{C.YELLOW}[*] Parser lokal EML-fil for Headers og Tracking Pixels: {filepath}{C.RESET}")
        try:
            with open(filepath, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=email.policy.default)
                
                for header in msg.get_all('Received', []):
                    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', header)
                    for ip in ips:
                        if not ip.startswith("10.") and not ip.startswith("192.168.") and not ip.startswith("127."):
                            self.target_ips.add(ip)
                            print(f"{C.GREEN}    ✓ IP fundet i Received-header: {ip}{C.RESET}")
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/html':
                            html = part.get_content()
                            soup = BeautifulSoup(html, 'html.parser')
                            for img in soup.find_all('img'):
                                src = img.get('src', '')
                                if src and ('width="1"' in str(img) or 'height="1"' in str(img) or 'display:none' in str(img)):
                                    self.data["Tracking_Pixels"].append(src)
                                    print(f"{C.MAGENTA}    🔥 Mulig Tracking Pixel detekteret: {src[:60]}...{C.RESET}")
                                    try:
                                        pixel_dom = src.split('/')[2]
                                        self._resolve_domain(pixel_dom)
                                    except: pass
        except Exception as e:
            print(f"{C.RED}[!] EML Parse Fejl: {e}{C.RESET}")

    def _resolve_domain(self, domain: str):
        print(f"{C.YELLOW}[*] Opløser DNS for domæne: {domain}{C.RESET}")
        if not dns: return
        for record_type in ['A', 'AAAA', 'MX']:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                for rdata in answers:
                    if record_type == 'MX':
                        mx_host = str(rdata.exchange).rstrip('.')
                        mx_ips = dns.resolver.resolve(mx_host, 'A')
                        for mx_ip in mx_ips:
                            self.target_ips.add(str(mx_ip))
                            print(f"{C.GREEN}    ✓ MX IP Fundet: {mx_ip} ({mx_host}){C.RESET}")
                    else:
                        self.target_ips.add(str(rdata))
                        print(f"{C.GREEN}    ✓ {record_type} Record Fundet: {rdata}{C.RESET}")
            except Exception: pass

    def _run_whois(self, domain: str):
        if not whois: return
        try:
            w = whois.whois(domain)
            self.data["WHOIS_Data"][domain] = {
                "Registrar": w.registrar,
                "Creation_Date": str(w.creation_date),
                "Emails": w.emails
            }
            print(f"{C.CYAN}    ✓ WHOIS Registrar: {w.registrar}{C.RESET}")
        except Exception: pass

    # =========================================================================
    # FASE 2: ASYNCHRONOUS ENGINE & GREYNOISE FILTER
    # =========================================================================
    async def _filter_ips_via_greynoise(self, session: aiohttp.ClientSession):
        """GOLIATH V36: Frasorterer internetscannere og baggrundsstøj via GreyNoise."""
        if not self.target_ips: return
        self._log(f"Krydstjekker {len(self.target_ips)} IP'er mod GreyNoise for at fjerne støj/scannere...", "INFO")
        
        valid_ips = set()
        noise_ips = set()
        headers = {"Accept": "application/json"}
        gn_key = CONFIG.get("api_keys", {}).get("greynoise_api_key", "")
        if gn_key: headers["key"] = gn_key

        async def check_gn(ip: str):
            if ip.startswith(("10.", "192.168.", "127.", "172.16.", "255.255.", "0.")):
                return
            try:
                async with session.get(f"https://api.greynoise.io/v3/community/{ip}", headers=headers, timeout=5) as res:
                    if res.status == 200:
                        data = await res.json()
                        if data.get("noise") or data.get("riot"):
                            noise_ips.add(ip)
                        else:
                            valid_ips.add(ip)
                    else:
                        valid_ips.add(ip) # Fail-open (tillad IP hvis server fejl/rate-limit)
            except Exception:
                valid_ips.add(ip)

        await asyncio.gather(*(check_gn(ip) for ip in self.target_ips))
        
        if noise_ips:
            self._log(f"GreyNoise frasorterede {len(noise_ips)} baggrundsscannere/benign IP'er.", "SUCCESS", indent=1)
            self.target_ips = valid_ips

    async def _phase_2_async_execution(self):
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 1. Kør GreyNoise Filtrering før Deep Scan
            if self.target_type in ["PCAP_FILE", "IP", "DOMAIN", "EML_FILE"]:
                await self._filter_ips_via_greynoise(session)

            self._log(f"Initierer Asynkron Deep-Scan af {len(self.target_ips)} validerede mål...", "INFO")
            tasks = []

            if self.target_ips:
                tasks.append(self._async_ip_scan(session))

            if self.target_type in ["IP", "DOMAIN", "PCAP_FILE"]:
                query_target = self.node.resolves_to[0] if self.target_type == "DOMAIN" and self.node.resolves_to else self.raw_target
                if self.target_ips: query_target = list(self.target_ips)[0]
                tasks.append(self._async_geoip(session, query_target))
                tasks.append(self._async_crt_sh(session, self.raw_target if self.target_type == "DOMAIN" else query_target))
            
            if self.target_type == "BSSID" and self.wigle_api_key:
                tasks.append(self._async_wigle_bssid(session, self.raw_target))

            if self.vt_api_key and self.target_type in ["IP", "DOMAIN"]:
                tasks.append(self._async_virustotal(session, self.raw_target, self.target_type))

            if self.target_type == "DOMAIN":
                tasks.append(self._async_wayback_cdx(session, self.raw_target))

            if tasks:
                await asyncio.gather(*tasks)

    async def _async_geoip(self, session: aiohttp.ClientSession, ip: str):
        try:
            async with session.get(f"http://ip-api.com/json/{ip}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        self.node.location = LocationData(
                            country=data.get("country", "Unknown"),
                            city=data.get("city", "Unknown"),
                            latitude=data.get("lat", 0.0),
                            longitude=data.get("lon", 0.0),
                            isp=data.get("isp", "Unknown"),
                            precision_level="Network"
                        )
                        self._log(f"GeoIP Acquired: {data.get('city')}, {data.get('country')} ({data.get('isp')})", "SUCCESS", indent=2)
        except Exception as e:
            self._log(f"GeoIP Error: {e}", "WARN", indent=2)

    async def _async_wigle_bssid(self, session: aiohttp.ClientSession, bssid: str):
        import urllib.parse
        url = f"https://api.wigle.net/api/v2/network/detail?netid={urllib.parse.quote(bssid)}"
        headers = {"Authorization": f"Basic {self.wigle_api_key}", "Accept": "application/json"}
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and len(data.get("results", [])) > 0:
                        res = data["results"][0]
                        self.node.location = LocationData(
                            country=res.get("country", "Unknown"),
                            city=res.get("city", "Unknown"),
                            latitude=res.get("trilat", 0.0),
                            longitude=res.get("trilong", 0.0),
                            isp="WIFI/BSSID",
                            precision_level="Street"
                        )
                        self.node.metadata["Wigle_SSID"] = res.get("ssid", "")
                        self.node.metadata["Wigle_Encryption"] = res.get("encryption", "")
                        self._log(f"BSSID Street-Level Geo Acquired: Lat {res.get('trilat')} Lon {res.get('trilong')}", "CRITICAL", indent=2)
        except Exception: pass

    async def _async_crt_sh(self, session: aiohttp.ClientSession, query: str):
        url = f"https://crt.sh/?q={query}&output=json"
        for attempt in range(3):
            try:
                async with session.get(url, timeout=10 + (attempt * 5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        unique_names = {n.lower() for entry in data for n in entry.get("name_value", "").split("\n") if n and not n.startswith("*")}
                        self.node.ssl_certificates = list(unique_names)[:50]
                        self._log(f"Certificate Transparency: Found {len(unique_names)} related subdomains/SANs.", "SUCCESS", indent=2)
                        return
            except Exception: pass
            await asyncio.sleep(2 ** (attempt + 1))

    async def _async_virustotal(self, session: aiohttp.ClientSession, query: str, target_type: str):
        headers = {"x-apikey": self.vt_api_key}
        vt_type = "ip_addresses" if target_type == "IP" else "domains"
        try:
            async with session.get(f"https://www.virustotal.com/api/v3/{vt_type}/{query}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    self.node.threat_intel = ThreatRecord(
                        source="VirusTotal",
                        malicious_votes=stats.get("malicious", 0) + stats.get("suspicious", 0),
                        total_votes=sum(stats.values())
                    )
                    if self.node.threat_intel.malicious_votes > 0:
                        self._log(f"VirusTotal Threat Alert: {self.node.threat_intel.malicious_votes} malicious vendors flagged this infrastructure.", "CRITICAL", indent=2)
        except Exception: pass

    async def _async_wayback_cdx(self, session: aiohttp.ClientSession, domain: str):
        url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=timestamp,original,mimetype,statuscode&filter=statuscode:200&collapse=urlkey&limit=50"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data) > 1:
                        endpoints = [HistoricalEndpoint(timestamp=r[0], url=r[1], mime_type=r[2], status_code=r[3]) for r in data[1:]]
                        self.node.historical_endpoints = endpoints
                        self._log(f"Wayback Machine: Extracted {len(endpoints)} historical active endpoints.", "SUCCESS", indent=2)
        except Exception: pass

    async def _async_ip_scan(self, session_http: aiohttp.ClientSession):
        self.data["Fundne_IPer"] = list(self.target_ips)
        tasks = [self._process_single_ip(session_http, ip) for ip in self.target_ips]
        results = await asyncio.gather(*tasks)
        for res in results:
            if res: self.data["IP_Detaljer"][res["IP"]] = res

    async def _process_single_ip(self, session_http: aiohttp.ClientSession, ip: str) -> Dict:
        ip_data = {"IP": ip, "GeoLocation": {}, "Shodan": {}, "Reverse_DNS": "", "Åbne_Porte": []}
        try: ip_data["Reverse_DNS"] = socket.gethostbyaddr(ip)[0]
        except: pass
        
        try:
            async with session_http.get(f"https://ipapi.co/{ip}/json/", timeout=5) as res:
                if res.status == 200:
                    geo = await res.json()
                    ip_data["GeoLocation"] = {"Country": geo.get("country_name"), "City": geo.get("city"), "ISP": geo.get("org")}
        except: pass

        # GOLIATH EXPANSION: Asynkron Shodan API Integration
        shodan_key = CONFIG.get("api_keys", {}).get("shodan_api_key", "")
        if shodan_key:
            try:
                async with session_http.get(f"https://api.shodan.io/shodan/host/{ip}?key={shodan_key}", timeout=5) as res:
                    if res.status == 200:
                        s_data = await res.json()
                        ip_data["Shodan"] = {
                            "OS": s_data.get("os", "Unknown"),
                            "Ports": s_data.get("ports", []),
                            "Vulns": s_data.get("vulns", [])
                        }
            except: pass
        
        if nmap:
            try:
                loop = asyncio.get_event_loop()
                def run_nmap():
                    nm = nmap.PortScanner()
                    nm.scan(ip, arguments='-Pn -F -T4')
                    return [{"Port": port, "Service": nm[ip][proto][port]['name']} for proto in nm[ip].all_protocols() for port in nm[ip][proto].keys() if nm[ip][proto][port]['state'] == 'open']
                ip_data["Åbne_Porte"] = await loop.run_in_executor(None, run_nmap)
            except: pass
        return ip_data

    # =========================================================================
    # FASE 3: FINALIZE & ARCHIVE
    # =========================================================================
    def _phase_3_finalize(self):
        output_dict = self.node.dict()
        
        # Udskriv pænt i konsollen
        with self.print_lock:
            print(f"\n{C.CYAN}--- TACTICAL INFRASTRUCTURE SUMMARY: {self.raw_target} ---{C.RESET}")
            print(f"Target Type:       {C.WHITE}{self.target_type}{C.RESET}")
            
            if self.node.resolves_to:
                print(f"Resolves To:       {C.WHITE}{', '.join(self.node.resolves_to)}{C.RESET}")
                
            loc = self.node.location
            if loc.country != "Unknown":
                loc_col = C.RED if loc.precision_level == "Street" else C.YELLOW
                print(f"Location:          {loc_col}{loc.city}, {loc.country} (Precision: {loc.precision_level}){C.RESET}")
                if loc.latitude != 0.0:
                    print(f"Coordinates:       {C.GREEN}https://www.google.com/maps?q={loc.latitude},{loc.longitude}{C.RESET}")

            threat = self.node.threat_intel
            if threat.total_votes > 0:
                threat_col = C.RED if threat.malicious_votes > 0 else C.GREEN
                print(f"Threat Score (VT): {threat_col}{threat.malicious_votes}/{threat.total_votes} Malicious/Suspicious{C.RESET}")
                if threat.tags:
                    print(f"Tags:              {C.WHITE}{', '.join(threat.tags)}{C.RESET}")

            if self.node.ssl_certificates:
                print(f"SSL/SAN Domains:   {C.WHITE}{len(self.node.ssl_certificates)} unique domains extracted{C.RESET}")
                
            if self.node.historical_endpoints:
                print(f"Historical URLs:   {C.WHITE}{len(self.node.historical_endpoints)} active endpoints indexed in Wayback Machine{C.RESET}")
                
            print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")

        # Ingest til Datalake og Disk
        datalake.ingest(self.name, self.raw_target, output_dict)
        self._export_results(output_dict)

    def _export_results(self, output_dict):
        ws_folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(ws_folder, exist_ok=True)
        safe_target = sanitize_filename(self.raw_target)
        path = Path(ws_folder) / f"10_INFRA_INTEL_{safe_target}.json"
        
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
            
        path.write_text(json.dumps(output_dict, indent=4, ensure_ascii=False), encoding="utf-8")
        
        csv_path = Path(ws_folder) / f"10_IP_TRACKER_{safe_target}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(["Input", "IP-adresse", "Hostname", "Land", "ISP", "Åbne Porte"])
            for ip, details in self.data.get("IP_Detaljer", {}).items():
                geo = details.get("GeoLocation", {})
                ports = ", ".join([str(p["Port"]) for p in details.get("Åbne_Porte", [])])
                writer.writerow([self.target, ip, details.get("Reverse_DNS", ""), geo.get("Country", ""), geo.get("ISP", ""), ports])
                
        self._log(f"Infrastructure Intel securely archived: {path} and {csv_path}", "SUCCESS")