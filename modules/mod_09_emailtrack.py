# -*- coding: utf-8 -*-
import json
import os
import hashlib
import subprocess
import requests
import socket # NY V8 TILFØJELSE: Til DNS/Domæne opslag
import sys
import re
from datetime import datetime
from pathlib import Path

# Henter fra Core
from core.utils import C, session, REGEX_EMAIL
from core.network import CONFIG

class EmailTracker:
    def __init__(self, email):
        self.email = email.strip().lower()
        self.api_key = CONFIG.get("api_keys", {}).get("hunter_io", "")
        self.gravatar_hash = hashlib.md5(self.email.encode()).hexdigest()
        self.data = {
            "Email": self.email, 
            "Email_Prefix": "",           # NY V8 TILFØJELSE: Til Alias-pivot
            "Gravatar_Data": {}, 
            "Holehe_Hits": [], 
            "Hunter_Data": {},
            "Domain_Intel": {},           # NY V8 TILFØJELSE: Corporate Data
            "Direct_OSINT_Links": {},     # NY V8 TILFØJELSE: Epieos / Skype
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, _=None):
        print(f"\n{C.CYAN}{'='*60}\n[09] E-mail Tracker (Hunter.io, Gravatar, Holehe & Epieos V8)\n{'='*60}{C.RESET}")
        
        if not re.match(REGEX_EMAIL, self.email):
            print(f"{C.RED}[!] Ugyldigt e-mail format angivet: {self.email}{C.RESET}")
            return
            
        print(f"Target Email: {self.email}\n")
        
        # --- NY V8 TILFØJELSE: Prefix Extraction (Brugernavn) ---
        self._extract_prefix()

        # --- NY V8 TILFØJELSE: Generer direkte Epieos og Skype OSINT links ---
        self._generate_osint_links()

        # --- NY V8 TILFØJELSE: Corporate Domain Intelligence ---
        self._domain_intelligence()
        
        # 1. Hunter.io Intelligence
        self._check_hunter()
        
        # 2. Gravatar Tjek (Med Avatar Bevissikring)
        print(f"\n{C.YELLOW}[*] Checker globalt Gravatar netværk for profildata...{C.RESET}")
        try:
            res = requests.get(f"https://en.gravatar.com/{self.gravatar_hash}.json", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if res.status_code == 200:
                grav_json = res.json()
                if "entry" in grav_json and grav_json["entry"]:
                    entry = grav_json["entry"][0]
                    print(f"{C.GREEN}    ✓ Offentlig Gravatar Profil Fundet!{C.RESET}")
                    
                    navn = entry.get("displayName", "Ukendt")
                    self.data["Gravatar_Data"]["Navn"] = navn
                    print(f"      -> Navn: {navn}")
                    
                    if "thumbnailUrl" in entry:
                        img_url = entry["thumbnailUrl"] + "?s=600"
                        self.data["Gravatar_Data"]["Billede"] = img_url
                        self._download_image(img_url)
            else:
                print(f"{C.DIM}    [-] Ingen Gravatar profil tilknyttet denne e-mail.{C.RESET}")
        except Exception: pass

        # 3. Holehe Integration (Trådsikker Live % Progress Bar)
        print(f"\n{C.YELLOW}[*] Kører Holehe OSINT engine for at finde registrerede profiler...{C.RESET}")
        try:
            process = subprocess.Popen(
                ['holehe', self.email, '--only-used'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1, 
                universal_newlines=True
            )
            
            checked_lines = 0
            estimated_total = 120 
            
            for line in iter(process.stdout.readline, ''):
                if not line: break
                
                checked_lines += 1
                pct = min(int((checked_lines / estimated_total) * 100), 99)
                
                sys.stdout.write(f"\r{C.CYAN}    [*] Analyserer platforme... {pct}% færdig {C.RESET}")
                sys.stdout.flush()

                if "[+]" in line:
                    try:
                        site = line.split("]")[1].strip().split(" ")[0].replace('\x1b[0m', '')
                        sys.stdout.write("\r" + " " * 60 + "\r")
                        print(f"{C.GREEN}    🔥 Registreret på: {C.CYAN}{site}{C.RESET}")
                        self.data["Holehe_Hits"].append(site)
                    except IndexError: pass
                    
            process.wait()
            sys.stdout.write("\r" + " " * 60 + "\r")
            print(f"{C.GREEN}    [✓] Holehe scanning 100% fuldført. Fandt {len(self.data['Holehe_Hits'])} profiler.{C.RESET}")

        except FileNotFoundError:
            sys.stdout.write("\r" + " " * 60 + "\r")
            print(f"{C.RED}    [!] 'holehe' er ikke installeret. Kør: pip install holehe{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved Holehe kørsel: {e}{C.RESET}")

        self.save()

    def _extract_prefix(self):
        """NY V8: Udtrækker prefix til brug som socialt alias"""
        prefix = self.email.split('@')[0]
        self.data["Email_Prefix"] = prefix
        print(f"{C.YELLOW}[*] Udtrækker E-mail Prefix til Alias-søgning...{C.RESET}")
        print(f"{C.GREEN}    -> Alias/Brugernavn: {prefix}{C.RESET}")

    def _generate_osint_links(self):
        """NY V8: Bygger direkte API og OSINT links"""
        print(f"\n{C.YELLOW}[*] Genererer direkte OSINT og App-links for e-mailen...{C.RESET}")
        epieos = f"https://epieos.com/?q={self.email}"
        skype = f"skype:{self.email}?userinfo"
        
        self.data["Direct_OSINT_Links"] = {"Epieos": epieos, "Skype": skype}
        print(f"{C.CYAN}    -> Epieos Dybde-Analyse: {epieos} (Tjek for Google Maps anmeldelser etc.){C.RESET}")
        print(f"{C.CYAN}    -> Skype Profil-Tjek: {skype}{C.RESET}")

    def _domain_intelligence(self):
        """NY V8: Hvis e-mailen er corporate, slås domænet op for at finde serveren"""
        domain = self.email.split('@')[1]
        generic_domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.dk", "icloud.com", "me.com", "mac.com", "protonmail.com"]
        
        if domain.lower() not in generic_domains:
            print(f"\n{C.YELLOW}[*] Corporate Domæne Detekteret: Udfører DNS opslag på {domain}...{C.RESET}")
            try:
                ip = socket.gethostbyname(domain)
                print(f"{C.GREEN}    ✓ Server IP for domæne: {ip}{C.RESET}")
                self.data["Domain_Intel"]["IP"] = ip
            except Exception as e:
                print(f"{C.DIM}    [-] Kunne ikke slå domæne op: {e}{C.RESET}")

    def _check_hunter(self):
        if not self.api_key:
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Mangler API-nøgle i config.json){C.RESET}")
            return

        print(f"\n{C.YELLOW}[*] Kontakter Hunter.io for Corporate Intelligence...{C.RESET}")
        
        ver_url = f"https://api.hunter.io/v2/email-verifier?email={self.email}&api_key={self.api_key}"
        try:
            res = requests.get(ver_url, timeout=10).json()
            if "data" in res:
                status = res["data"]["status"]
                score = res["data"]["score"]
                color = C.GREEN if score > 70 else (C.YELLOW if score > 40 else C.RED)
                print(f"{color}    ✓ Status: {status.upper()} (Sikkerhedsscore: {score}/100){C.RESET}")
                self.data["Hunter_Data"]["Verification"] = res["data"]
        except Exception as e:
            print(f"{C.DIM}    [!] Kunne ikke verificere email: {e}{C.RESET}")

        enr_url = f"https://api.hunter.io/v2/combined/find?email={self.email}&api_key={self.api_key}"
        try:
            res = requests.get(enr_url, timeout=10).json()
            if "data" in res and res["data"]:
                data = res["data"]
                print(f"{C.GREEN}    🔥 Person & Firma Berigelse Fundet!{C.RESET}")
                
                first = data.get("first_name", "")
                last = data.get("last_name", "")
                company = data.get("company", "")
                position = data.get("position", "")
                twitter = data.get("twitter", "")
                linkedin = data.get("linkedin", "")

                if first or last: print(f"      -> Navn: {first} {last}")
                if company: print(f"      -> Firma: {company}")
                if position: print(f"      -> Stilling: {position}")
                if linkedin: print(f"      -> LinkedIn: {linkedin}")
                if twitter: print(f"      -> Twitter: {twitter}")

                self.data["Hunter_Data"]["Enrichment"] = data
        except Exception:
            pass

    def _download_image(self, url):
        try:
            img_data = requests.get(url, timeout=10).content
            mappe = os.path.join(session["loot_folder"], "avatars")
            os.makedirs(mappe, exist_ok=True)
            filsti = os.path.join(mappe, f"Gravatar_{self.email.replace('@', '_at_')}.jpg")
            with open(filsti, 'wb') as handler:
                handler.write(img_data)
            print(f"{C.GREEN}      ✓ Avatar sikret lokalt: {filsti}{C.RESET}")
        except Exception: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/09_EMAILTRACK_{self.email.replace('@', '_at_')}.json"
        
        # NY V8 TILFØJELSE: Sikrer overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except: pass
            
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt (Overskrevet succesfuldt): {filename}{C.RESET}")