import json
import os
import requests
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class IPNetworkAnalyzer:
    """Geo, Shodan og AlienVault OTX Threat Intelligence"""
    def __init__(self, ip):
        self.ip = ip.strip()
        self.data = {"IP": self.ip, "GeoData": {}, "Shodan_Data": {}, "AlienVault_OTX": {}, "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[10] IP- & Threat Intel Analyse (Geo + Shodan + AlienVault)\n{'='*60}{C.RESET}")
        
        # 1. GeoIP
        try:
            res1 = requests.get(f"http://ip-api.com/json/{self.ip}?fields=status,country,city,isp,org,mobile,proxy,hosting").json()
            if res1.get("status") == "success":
                self.data["GeoData"] = res1
                print(f"{C.GREEN}    ✓ Lokation: {res1.get('city')}, {res1.get('country')} (ISP: {res1.get('isp')}){C.RESET}")
                if res1.get("proxy") or res1.get("hosting"):
                    print(f"{C.RED}      -> [!] ADVARSEL: IP er flaget som Datacenter/Proxy/VPN!{C.RESET}")
        except Exception: pass

        # 2. Shodan
        print(f"{C.YELLOW}[*] Scanner via Shodan InternetDB...{C.RESET}")
        try:
            shodan = requests.get(f"https://internetdb.shodan.io/{self.ip}", timeout=5).json()
            if "ports" in shodan:
                self.data["Shodan_Data"] = shodan
                print(f"{C.GREEN}    ✓ Åbne Porte: {', '.join(map(str, shodan.get('ports', [])))}{C.RESET}")
        except Exception: pass

        # 3. AlienVault OTX
        print(f"{C.YELLOW}[*] Checker IP mod AlienVault OTX Threat Pulses...{C.RESET}")
        try:
            otx = requests.get(f"https://otx.alienvault.com/api/v1/indicators/IPv4/{self.ip}/general", timeout=5).json()
            if "pulse_info" in otx and otx["pulse_info"]["count"] > 0:
                self.data["AlienVault_OTX"] = otx["pulse_info"]
                print(f"{C.RED}    🔥 KRITISK: IP optræder i {otx['pulse_info']['count']} AlienVault Threat Pulses (Kendt ondsindet aktivitet)!{C.RESET}")
            else:
                print(f"{C.GREEN}    ✓ IP'en er ren hos AlienVault.{C.RESET}")
        except Exception: pass

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/10_IP_{self.ip.replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")