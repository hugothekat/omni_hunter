# -*- coding: utf-8 -*-
import json
import os
import re
import requests
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class IPNetworkAnalyzer:
    """Geo, Shodan og AlienVault OTX Threat Intelligence"""
    def __init__(self, ip):
        self.ip = ip.strip()
        self.data = {
            "IP": self.ip, 
            "GeoData": {}, 
            "Shodan_Data": {}, 
            "AlienVault_OTX": {}, 
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[10] IP- & Threat Intel Analyse (Geo + Shodan + AlienVault)\n{'='*60}{C.RESET}")
        
        # Simpel IP validering (IPv4)
        if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", self.ip):
            print(f"{C.RED}[!] Ugyldigt IPv4 format angivet: {self.ip}{C.RESET}")
            return

        print(f"[*] Analyserer target IP: {self.ip}\n")
        
        # 1. GeoIP
        print(f"{C.YELLOW}[*] Henter global routing og lokationsdata...{C.RESET}")
        try:
            res1 = requests.get(f"http://ip-api.com/json/{self.ip}?fields=status,country,city,isp,org,mobile,proxy,hosting", timeout=10).json()
            if res1.get("status") == "success":
                self.data["GeoData"] = res1
                print(f"{C.GREEN}    ✓ Lokation: {res1.get('city')}, {res1.get('country')} (ISP: {res1.get('isp')}){C.RESET}")
                if res1.get("proxy") or res1.get("hosting"):
                    print(f"{C.RED}      -> [!] ADVARSEL: IP er flaget som Datacenter/Proxy/VPN! (Mulig OPSEC sløring){C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] GeoIP opslag fejlede eller IP er lokal/reserveret.{C.RESET}")
        except Exception as e: 
            print(f"{C.DIM}    [!] Forbindelsesfejl til GeoIP: {e}{C.RESET}")

        # 2. Shodan
        print(f"\n{C.YELLOW}[*] Scanner via Shodan InternetDB (Porte og sårbarheder)...{C.RESET}")
        try:
            shodan = requests.get(f"https://internetdb.shodan.io/{self.ip}", timeout=10).json()
            if "ports" in shodan:
                self.data["Shodan_Data"] = shodan
                print(f"{C.GREEN}    ✓ Åbne Porte: {', '.join(map(str, shodan.get('ports', [])))}{C.RESET}")
                if shodan.get('hostnames'):
                    print(f"{C.CYAN}    ✓ Hostnames: {', '.join(shodan.get('hostnames'))}{C.RESET}")
            elif "error" in shodan:
                print(f"{C.GREEN}    ✓ Ingen åbne porte registreret af Shodan.{C.RESET}")
        except Exception: 
            print(f"{C.DIM}    [-] Shodan gav intet svar.{C.RESET}")

        # 3. AlienVault OTX
        print(f"\n{C.YELLOW}[*] Checker IP mod AlienVault OTX Threat Pulses...{C.RESET}")
        try:
            otx = requests.get(f"https://otx.alienvault.com/api/v1/indicators/IPv4/{self.ip}/general", timeout=10).json()
            if "pulse_info" in otx and otx["pulse_info"]["count"] > 0:
                self.data["AlienVault_OTX"] = otx["pulse_info"]
                print(f"{C.RED}    🔥 KRITISK: IP optræder i {otx['pulse_info']['count']} AlienVault Threat Pulses (Kendt ondsindet aktivitet)!{C.RESET}")
            else:
                print(f"{C.GREEN}    ✓ IP'en er ren hos AlienVault.{C.RESET}")
        except Exception: 
            print(f"{C.DIM}    [-] AlienVault OTX kunne ikke kontaktes.{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/10_IP_{self.ip.replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Netværksrapport gemt: {filename}{C.RESET}")