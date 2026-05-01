# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V57: ACTIVE SERVICE PROBER
📌 Formål: Banner grabbing og sårbarhedskortlægning via socket-probes.
"""
import socket
import sys
import sqlite3
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake

class ServiceProber(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "ACTIVE SERVICE PROBER"
        self.description = "Parallel banner grabbing og vulnerability matching."
        self.category = ModuleCategory.NETWORK
        self.ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080]
        self.data = {"Discovered_Vulns": [], "Timestamp": datetime.now().isoformat()}

    def retBanner(self, ip: str, port: int) -> Optional[str]:
        """Implementering af socket-forbindelse fra Violent Python."""
        try:
            socket.setdefaulttimeout(2)
            s = socket.socket()
            s.connect((ip, port))
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
            s.close()
            return banner
        except Exception:
            return None

    def checkVulns(self, banner: str) -> Optional[tuple]:
        """Simpelt matchings-system baseret på Violent Python opskrifter og gængse CVEs."""
        vulnerable_signatures = {
            "FreeFloat Ftp Server (Version 1.00)": ("FreeFloat FTP Exploit", "CRITICAL"),
            "3Com 3CDaemon FTP Server Version 2.0": ("3Com Overflow", "HIGH"),
            "Ability Server 2.34": ("Ability Directory Traversal", "MEDIUM"),
            "vsFTPd 2.3.4": ("vsFTPd 2.3.4 Backdoor (CVE-2011-2523)", "CRITICAL"),
            "ProFTPD 1.3.3c": ("ProFTPD 1.3.3c Backdoor", "CRITICAL"),
            "OpenSSH 4.3": ("OpenSSH 4.3 Exploit", "MEDIUM"),
            "Apache/2.2.8": ("Apache 2.2.8 Mod_negotiation", "LOW"),
            "Microsoft-IIS/6.0": ("IIS 6.0 WebDAV RCE (CVE-2017-7269)", "CRITICAL")
        }
        for sig, info in vulnerable_signatures.items():
            if sig.lower() in banner.lower():
                return info
        return None

    def _probe_target(self, pid: int, ip: str, port: int):
        banner = self.retBanner(ip, port)
        if banner:
            print(f"{C.GREEN}    [+] Port {port} åben på {ip}: {banner[:50]}...{C.RESET}")
            vuln_info = self.checkVulns(banner)
            if vuln_info:
                print(f"{C.RED}    [!] SÅRBARHED FUNDET: {vuln_info[0]} ({vuln_info[1]}){C.RESET}")
                self.data["Discovered_Vulns"].append({
                    "persona_id": pid, 
                    "port": port, 
                    "banner": banner,
                    "vuln": vuln_info[0], 
                    "severity": vuln_info[1]
                })

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[32] ACTIVE SERVICE PROBER V57\n{'='*60}{C.RESET}")
        
        db_path = Path(session.get("loot_folder", "loot_evidence")) / "omni_datalake.db"
        if not db_path.exists():
            print(f"{C.RED}[!] Kunne ikke lokalisere datalake.db. Har du kørt Modul 27?{C.RESET}")
            return self.data

        print(f"{C.YELLOW}[*] Udfører asynkron Socket-Probing mod verificerede Master Personas IP-adresser...{C.RESET}")
        
        targets_to_probe = []
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, target, last_ip FROM master_personas WHERE last_ip IS NOT NULL AND last_ip != '' AND last_ip != 'Ukendt'")
            for pid, tgt, ip in cursor.fetchall():
                targets_to_probe.append((pid, tgt, ip))

        if not targets_to_probe:
            print(f"{C.DIM}[-] Ingen IP-adresser knyttet til Personas endnu.{C.RESET}")
            return self.data

        # Kør multi-threaded banner grabbing for lynhurtig performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for pid, tgt, ip in targets_to_probe:
                for port in self.ports:
                    futures.append(executor.submit(self._probe_target, pid, ip, port))
            
            concurrent.futures.wait(futures)

        print(f"\n{C.GREEN}[✓] Active Service Probing fuldført. Fandt {len(self.data['Discovered_Vulns'])} sårbarheder.{C.RESET}")
        datalake.ingest(self.name, "Network-Wide", self.data)
        
        return self.data