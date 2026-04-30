# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import time
import json
import os
import re
import socket
import asyncio
import aiohttp
import threading
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake, sanitize_filename

try:
    from core.config_vault import vault
    CONFIG = vault.state if vault else {}
except ImportError:
    CONFIG = {}

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

class ThreatRecord(BaseModel):
    source: str
    malicious_votes: int = 0
    total_votes: int = 0
    tags: List[str] = Field(default_factory=list)
    last_analysis_date: Optional[str] = None

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
class InfrastructureJuggernaut(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.name = "OMNI-NETWORK & INFRASTRUCTURE ENGINE"
        self.description = "Dyb asynkron analyse af IP, Domæner, BSSID (Wigle), Wayback og VirusTotal."
        self.category = ModuleCategory.NETWORK
        self.print_lock = threading.Lock()
        
        self.raw_target = ""
        self.target_type = "UNKNOWN"
        self.vt_api_key = CONFIG.get("api_keys", {}).get("virustotal_api_key", "")
        self.wigle_api_key = CONFIG.get("api_keys", {}).get("wigle_api_key", "") # Base64 encoded 'Name:Password'
        
        self.node = InfraIntelNode(target="INIT", target_type="INIT")

    def _log(self, message: str, level: str = "INFO", indent: int = 0) -> None:
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "ERROR": C.RED, "SUCCESS": C.GREEN, "PIVOT": C.MAGENTA, "CRITICAL": C.RED}
        color = colors.get(level, C.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "  " * indent
        with self.print_lock:
            sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {prefix}[{color}{level}{C.RESET}] {message}\n")

    def _determine_target_type(self, target: str) -> str:
        target = target.strip()
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

        self.node = InfraIntelNode(target=self.raw_target, target_type=self.target_type)

        print(f"\n{C.BG_RED}{C.WHITE} === THE OMNI-NETWORK JUGGERNAUT V39 ENGAGED === {C.RESET}\n")
        self._log(f"Initiating Global Infrastructure Sequence for: {self.raw_target} [TYPE: {self.target_type}]", "INFO")

        # FASE 1: Lokal Resolution
        self._phase_1_local_resolution()

        # FASE 2: Asynkron API Matrix (VT, Wayback, GeoIP, Certs)
        self._log("FASE 2: Executing Parallel API Matrix (Geo, Threat, Historical)...", "INFO")
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(self._phase_2_async_execution())
        except Exception as e:
            self._log(f"Async Loop failed: {e}", "ERROR", indent=1)

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
            except Exception:
                self._log("Domain DNS resolution failed.", "WARN", indent=1)
        elif self.target_type == "IP":
            try:
                host = socket.gethostbyaddr(self.raw_target)
                self.node.resolves_to.append(host[0])
                self._log(f"IPv4 Resolves to Host: {host[0]}", "SUCCESS", indent=1)
            except Exception:
                self._log("Reverse DNS resolution failed.", "WARN", indent=1)

    # =========================================================================
    # FASE 2: ASYNCHRONOUS ENGINE
    # =========================================================================
    async def _phase_2_async_execution(self):
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = []
            
            # Altid kør GeoIP (gratis endpoint uden key)
            if self.target_type in ["IP", "DOMAIN"]:
                query_target = self.node.resolves_to[0] if self.target_type == "DOMAIN" and self.node.resolves_to else self.raw_target
                tasks.append(self._async_geoip(session, query_target))
                tasks.append(self._async_crt_sh(session, self.raw_target if self.target_type == "DOMAIN" else query_target))
            
            # Kør BSSID Geolocation
            if self.target_type == "BSSID" and self.wigle_api_key:
                tasks.append(self._async_wigle_bssid(session, self.raw_target))
            elif self.target_type == "BSSID":
                self._log("BSSID Target angivet, men ingen Wigle API nøgle i config. Springer over.", "WARN", indent=1)

            # Kør VirusTotal hvis API nøgle findes
            if self.vt_api_key and self.target_type in ["IP", "DOMAIN"]:
                tasks.append(self._async_virustotal(session, self.raw_target, self.target_type))

            # Kør Wayback Machine
            if self.target_type == "DOMAIN":
                tasks.append(self._async_wayback_cdx(session, self.raw_target))

            # Kør asynkront og vent på alle
            if tasks:
                await asyncio.gather(*tasks)

    async def _async_geoip(self, session: aiohttp.ClientSession, ip: str):
        url = f"http://ip-api.com/json/{ip}"
        try:
            async with session.get(url) as response:
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
                else:
                    self._log(f"Wigle API afviste request (Status {response.status})", "WARN", indent=2)
        except Exception as e:
            self._log(f"Wigle BSSID Error: {e}", "WARN", indent=2)

    async def _async_crt_sh(self, session: aiohttp.ClientSession, query: str):
        """Henter subdomæner og certifikater via gratis crt.sh endpoint (Med Exponential Backoff)."""
        url = f"https://crt.sh/?q={query}&output=json"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Dynamisk timeout der øges ved hvert forsøg
                current_timeout = 10 + (attempt * 5)
                async with session.get(url, timeout=current_timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        unique_names = set()
                        for entry in data:
                            names = entry.get("name_value", "").split("\n")
                            for n in names:
                                if n and not n.startswith("*"): unique_names.add(n.lower())
                        
                        self.node.ssl_certificates = list(unique_names)[:50] # Gem op til 50
                        self._log(f"Certificate Transparency: Found {len(unique_names)} related subdomains/SANs.", "SUCCESS", indent=2)
                        return # Succes - afbryd backoff loopet
                    elif response.status in [502, 503, 504]:
                        self._log(f"crt.sh overbelastet (HTTP {response.status}). Venter før nyt forsøg...", "WARN", indent=2)
                    else:
                        self._log(f"crt.sh returnerede uventet status: {response.status}. Afbryder.", "WARN", indent=2)
                        break # Bryd ved hard-fails som 400/403/404
            except asyncio.TimeoutError:
                self._log(f"crt.sh timeout (Forsøg {attempt + 1}/{max_retries}).", "WARN", indent=2)
            except aiohttp.ClientError as e:
                self._log(f"crt.sh netværksfejl: {e} (Forsøg {attempt + 1}/{max_retries}).", "WARN", indent=2)
            except Exception as e:
                self._log(f"crt.sh uventet fejl: {e}", "ERROR", indent=2)
                break
                
            if attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                sleep_time = 2 ** (attempt + 1)
                await asyncio.sleep(sleep_time)
                
        if not self.node.ssl_certificates:
            self._log("crt.sh opslag opgav efter maksimale forsøg.", "ERROR", indent=2)

    async def _async_virustotal(self, session: aiohttp.ClientSession, query: str, target_type: str):
        headers = {"x-apikey": self.vt_api_key}
        vt_type = "ip_addresses" if target_type == "IP" else "domains"
        url = f"https://www.virustotal.com/api/v3/{vt_type}/{query}"
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    attrs = data.get("data", {}).get("attributes", {})
                    stats = attrs.get("last_analysis_stats", {})
                    
                    self.node.threat_intel = ThreatRecord(
                        source="VirusTotal",
                        malicious_votes=stats.get("malicious", 0) + stats.get("suspicious", 0),
                        total_votes=sum(stats.values()),
                        tags=attrs.get("tags", []),
                        last_analysis_date=datetime.fromtimestamp(attrs.get("last_analysis_date", 0)).isoformat() if attrs.get("last_analysis_date") else None
                    )
                    
                    if self.node.threat_intel.malicious_votes > 0:
                        self._log(f"VirusTotal Threat Alert: {self.node.threat_intel.malicious_votes} malicious vendors flagged this infrastructure.", "CRITICAL", indent=2)
                    else:
                        self._log("VirusTotal: Infrastructure appears clean.", "SUCCESS", indent=2)
                elif response.status == 401:
                    self._log("VirusTotal API Key invalid.", "ERROR", indent=2)
        except Exception as e:
            self._log(f"VirusTotal API Error: {e}", "WARN", indent=2)

    async def _async_wayback_cdx(self, session: aiohttp.ClientSession, domain: str):
        """Time-Machine: Henter historiske endpoints via Wayback CDX API."""
        url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=timestamp,original,mimetype,statuscode&filter=statuscode:200&collapse=urlkey&limit=50"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data) > 1: # Index 0 er headers
                        endpoints = []
                        for row in data[1:]: # Spring headers over
                            try:
                                endpoints.append(HistoricalEndpoint(
                                    timestamp=row[0], url=row[1], mime_type=row[2], status_code=row[3]
                                ))
                            except IndexError: pass
                        
                        self.node.historical_endpoints = endpoints
                        self._log(f"Wayback Machine: Extracted {len(endpoints)} historical active endpoints.", "SUCCESS", indent=2)
        except Exception as e:
            self._log(f"Wayback CDX Error: {e}", "WARN", indent=2)

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
        
        ws_folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(ws_folder, exist_ok=True)
        safe_target = sanitize_filename(self.raw_target)
        path = Path(ws_folder) / f"10_INFRA_INTEL_{safe_target}.json"
        
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
            
        path.write_text(json.dumps(output_dict, indent=4, ensure_ascii=False), encoding="utf-8")
        self._log(f"Infrastructure Intel securely archived: {path}", "SUCCESS")