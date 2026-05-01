# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V59: INFRASTRUCTURE AUDITOR (FTP/WEB)
📌 Formål: Aggressiv audit af FTP Anonymous logins og Web Directory Exposure baseret på Violent Python kapitel 2.
"""
import ftplib
import concurrent.futures
import urllib.parse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import http

class InfraAuditor(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "INFRASTRUCTURE AUDITOR (FTP/WEB)"
        self.description = "Sårbarhedsscanner for FTP fejlkonfigurationer og web-lækager."
        self.category = ModuleCategory.NETWORK
        
        # Matcher datastrukturen fra Active Service Prober for at sikre Dashboard integration
        self.data = {"Discovered_Vulns": [], "Timestamp": datetime.now().isoformat()}
        
        self.web_payloads = [
            '/.git/config', '/.env', '/phpinfo.php', 
            '/backup.zip', '/wp-config.php.bak', '/docker-compose.yml'
        ]
        self.ftp_creds = [
            ("admin", "admin"), ("root", "root"), 
            ("administrator", "password"), ("test", "test")
        ]

    def _audit_ftp(self, ip: str):
        """Tester for Anonymous login og svage credentials."""
        try:
            ftp = ftplib.FTP(ip, timeout=5)
            ftp.login('anonymous', 'anonymous@domain.com')
            print(f"{C.RED}    [!] SÅRBARHED: FTP Anonymous Login tilladt på {ip}{C.RESET}")
            self.data["Discovered_Vulns"].append({
                "persona_id": 0, "port": 21, "banner": ftp.getwelcome() or "FTP Open",
                "vuln": "Anonymous FTP Login Allowed", "severity": "HIGH"
            })
            ftp.quit()
        except Exception:
            pass # Anonymous fejlede, vi prøver bruteforce

        for user, pwd in self.ftp_creds:
            try:
                ftp = ftplib.FTP(ip, timeout=5)
                ftp.login(user, pwd)
                print(f"{C.RED}    [!] SÅRBARHED: Svagt FTP login ({user}:{pwd}) på {ip}{C.RESET}")
                self.data["Discovered_Vulns"].append({
                    "persona_id": 0, "port": 21, "banner": "FTP Auth Bypass",
                    "vuln": f"Weak FTP Credentials ({user}:{pwd})", "severity": "CRITICAL"
                })
                ftp.quit()
                break # Stop hvis vi finder en vej ind
            except Exception:
                pass

    def _audit_web(self, target: str):
        """Enumererer efter eksponerede filer."""
        base_url = target if target.startswith("http") else f"http://{target}"
        
        for payload in self.web_payloads:
            url = f"{base_url}{payload}"
            try:
                res = http.get(url, timeout=5, allow_redirects=False)
                # Heuristik: Tjekker om filindholdet faktisk er et git-config, en zip eller en env fil
                if res.status_code == 200 and any(sig in res.text for sig in ["DB_PASSWORD", "[core]", "PK\x03\x04", "<?php"]):
                    print(f"{C.RED}    [!] SÅRBARHED: Følsom fil eksponeret på {url}{C.RESET}")
                    self.data["Discovered_Vulns"].append({
                        "persona_id": 0, "port": 80, "banner": res.headers.get("Server", "Webserver"),
                        "vuln": f"Exposed File/Directory ({payload})", "severity": "HIGH"
                    })
            except Exception: pass

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[34] INFRASTRUCTURE AUDITOR V59\n{'='*60}{C.RESET}")
        if not target:
            print(f"{C.YELLOW}[*] Intet target angivet. Eksempel: run 34 192.168.1.10, www.mitdomæne.dk{C.RESET}")
            return self.data

        targets = [t.strip() for t in target.split(",")]
        print(f"{C.YELLOW}[*] Starter parallel FTP og Web Audit på {len(targets)} mål...{C.RESET}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for t in targets:
                clean_ip = t.replace("http://", "").replace("https://", "").split("/")[0]
                executor.submit(self._audit_ftp, clean_ip)
                executor.submit(self._audit_web, t)

        datalake.ingest(self.name, target, self.data)
        print(f"\n{C.GREEN}[✓] Infrastructure Audit fuldført.{C.RESET}")
        return self.data