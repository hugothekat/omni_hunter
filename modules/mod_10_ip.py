# -*- coding: utf-8 -*-
import json
import os
import re
import requests
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class IPNetworkAnalyzer:
    """Geo, Shodan, AlienVault OTX Threat Intelligence og Reverse IP"""
    def __init__(self, ip):
        self.ip = ip.strip()
        self.data = {
            "IP": self.ip, 
            "Ping_Status": "Ukendt",          # NY V8 TILFØJELSE: Host-Alive tjek
            "Reverse_DNS": "",                # NY V8 TILFØJELSE: Hostname
            "GeoData": {}, 
            "Shodan_Data": {}, 
            "AlienVault_OTX": {}, 
            "Virtual_Hosts": [],              # NY V8 TILFØJELSE: Domæner på samme IP
            "Direct_OSINT_Links": {},         # NY V8 TILFØJELSE: VirusTotal, AbuseIPDB osv.
            "Actionable_Commands": [],        # NY V8 TILFØJELSE: Nmap commands
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[10] IP- & Threat Intel Analyse (GOLIATH V8)\n{'='*60}{C.RESET}")
        
        # Simpel IP validering (IPv4 eller IPv6 for at være robust)
        if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", self.ip) and ":" not in self.ip:
            print(f"{C.RED}[!] Ugyldigt IP format angivet: {self.ip}{C.RESET}")
            return

        print(f"[*] Analyserer target IP: {self.ip}\n")
        
        # --- NY V8 TILFØJELSE: ICMP Ping ---
        print(f"{C.YELLOW}[*] Udfører ICMP Ping for Host-Alive status...{C.RESET}")
        param = '-n' if sys.platform.lower() == 'win32' else '-c'
        try:
            ping_res = subprocess.run(['ping', param, '1', '-W', '2', self.ip], capture_output=True, text=True)
            if ping_res.returncode == 0:
                print(f"{C.GREEN}    ✓ Host er OPPE (ICMP Reply modtaget){C.RESET}")
                self.data["Ping_Status"] = "Online"
            else:
                print(f"{C.DIM}    [-] Host svarer ikke på ping (Kan være bag firewall){C.RESET}")
                self.data["Ping_Status"] = "Offline/Firewalled"
        except: pass

        # --- NY V8 TILFØJELSE: Native Reverse DNS ---
        print(f"\n{C.YELLOW}[*] Opløser Reverse DNS (PTR Record)...{C.RESET}")
        try:
            hostname = socket.gethostbyaddr(self.ip)[0]
            self.data["Reverse_DNS"] = hostname
            print(f"{C.GREEN}    ✓ Hostname: {hostname}{C.RESET}")
        except Exception:
            print(f"{C.DIM}    [-] Ingen PTR record fundet (Ingen native hostname).{C.RESET}")

        # 1. GeoIP
        print(f"\n{C.YELLOW}[*] Henter global routing og lokationsdata...{C.RESET}")
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

        # --- NY V8 TILFØJELSE: Reverse IP Lookup (Find Domæner) ---
        print(f"\n{C.YELLOW}[*] Checker HackerTarget for Reverse IP (Domæner på samme server)...{C.RESET}")
        try:
            ht_res = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={self.ip}", timeout=10)
            if ht_res.status_code == 200 and "error" not in ht_res.text.lower() and "no dns A records" not in ht_res.text.lower():
                vhosts = [v.strip() for v in ht_res.text.strip().split('\n') if v.strip()]
                if vhosts and len(vhosts) > 0 and vhosts[0] != self.ip:
                    print(f"{C.RED}    🔥 Fandt {len(vhosts)} domæner hostet på denne IP!{C.RESET}")
                    for vh in vhosts[:5]:
                        print(f"      -> {vh}")
                    if len(vhosts) > 5:
                        print(f"{C.DIM}      -> ... og {len(vhosts)-5} flere.{C.RESET}")
                    self.data["Virtual_Hosts"] = vhosts
            else:
                print(f"{C.DIM}    [-] Ingen virtuelle hosts (domæner) fundet på denne IP.{C.RESET}")
        except Exception:
            print(f"{C.DIM}    [-] HackerTarget opslag timeout.{C.RESET}")

        # 2. Shodan
        print(f"\n{C.YELLOW}[*] Scanner via Shodan InternetDB (Porte og sårbarheder)...{C.RESET}")
        try:
            shodan = requests.get(f"https://internetdb.shodan.io/{self.ip}", timeout=10).json()
            if "ports" in shodan:
                self.data["Shodan_Data"] = shodan
                print(f"{C.GREEN}    ✓ Åbne Porte: {', '.join(map(str, shodan.get('ports', [])))}{C.RESET}")
                if shodan.get('hostnames'):
                    print(f"{C.CYAN}    ✓ Hostnames (Shodan): {', '.join(shodan.get('hostnames'))}{C.RESET}")
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

        # --- NY V8 TILFØJELSE: OSINT Links & Taktiske Kommandoer ---
        self._generate_osint_links()

        self.save()

    def _generate_osint_links(self):
        """Bygger klikbare URL'er til OSINT og kommandoer"""
        print(f"\n{C.YELLOW}[*] Bygger direkte Intelligence-Links og Scanningskommandoer...{C.RESET}")
        
        links = {
            "VirusTotal": f"https://www.virustotal.com/gui/ip-address/{self.ip}",
            "AbuseIPDB": f"https://www.abuseipdb.com/check/{self.ip}",
            "Shodan_Web": f"https://www.shodan.io/host/{self.ip}",
            "Censys": f"https://search.censys.io/hosts/{self.ip}",
            "Spur (VPN Tracker)": f"https://spur.us/context/{self.ip}"
        }
        self.data["Direct_OSINT_Links"] = links
        
        print(f"{C.CYAN}    -> VirusTotal Opslag: {links['VirusTotal']}{C.RESET}")
        print(f"{C.CYAN}    -> AbuseIPDB Opslag:  {links['AbuseIPDB']}{C.RESET}")
        print(f"{C.CYAN}    -> Spur VPN Tracker:  {links['Spur (VPN Tracker)']}{C.RESET}")

        nmap_cmd = f"nmap -Pn -sV -sC -O -A -p- -T4 {self.ip}"
        self.data["Actionable_Commands"].append({"Værktøj": "Nmap Aggressive Scan", "Kommando": nmap_cmd})
        print(f"\n{C.MAGENTA}    🔥 Taktisk Kommando Genereret for dybdegående scan:{C.RESET}")
        print(f"       {nmap_cmd}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/10_IP_{self.ip.replace('.', '_').replace(':', '_')}.json"
        
        # NY V8 TILFØJELSE: Sikker overskrivning af fil
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Netværksrapport gemt: {filename}{C.RESET}")