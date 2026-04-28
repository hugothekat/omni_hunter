# -*- coding: utf-8 -*-
import os
import json
import re
import requests
import base64
from datetime import datetime
from pathlib import Path
from core.utils import C, session
from core.network import CONFIG

class VirusTotalAnalyzer:
    """GOLIATH V8: Dybdegående Threat Intelligence & Malware Profiling"""
    def __init__(self, hash_or_ip):
        self.target = str(hash_or_ip).strip()
        self.api_key = CONFIG.get("api_keys", {}).get("virus_total", "")
        self.target_type = self._detect_target_type()
        
        self.data = {
            "Target": self.target, 
            "Type": self.target_type,
            "Malicious": 0, 
            "Undetected": 0, 
            "Suspicious": 0,
            "Trussels_Kategori": [],       # NY V8: Ransomware, Phishing, Trojan etc.
            "Populært_Trusselsnavn": "",   # NY V8: Familiens navn (fx Emotet)
            "Community_Kommentarer": [],   # NY V8: Indsigter fra andre analytikere
            "Direct_OSINT_Links": {},      # NY V8: Genveje til Any.Run / HybridAnalysis
            "Details": {},
            "Timestamp": datetime.now().isoformat()
        }

    def _detect_target_type(self):
        """Intelligent detektion af input typen for korrekt API routing"""
        if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", self.target):
            return "ip_addresses"
        elif re.match(r"^[A-Fa-f0-9]{32}$|^[A-Fa-f0-9]{40}$|^[A-Fa-f0-9]{64}$", self.target):
            return "files"
        elif self.target.startswith("http://") or self.target.startswith("https://"):
            return "urls"
        else:
            return "domains" # Fallback, antager domæne hvis det ikke er IP, Hash eller eksplicit URL

    def run(self, driver=None): # Driver tilføjet for Omni-Pivot kompatibilitet
        print(f"\n{C.CYAN}{'='*60}\n[26] VirusTotal Threat Intelligence (GOLIATH V8 Engine)\n{'='*60}{C.RESET}")
        print(f"[*] Analyserer Target: {self.target}")
        print(f"[*] Klassificering: {self.target_type.upper().replace('_', ' ')}")

        if not self.api_key:
            print(f"{C.RED}[!] VirusTotal API-nøgle mangler i config.json{C.RESET}")
            return
            
        self._generate_osint_links()
            
        headers = {
            "accept": "application/json",
            "x-apikey": self.api_key
        }

        # Format URL for API kald
        api_target = self.target
        if self.target_type == "urls":
            # VirusTotal kræver base64 url-safe encodede strenge (uden '=') til URL scanning
            api_target = base64.urlsafe_b64encode(self.target.encode()).decode().strip("=")

        url = f"https://www.virustotal.com/api/v3/{self.target_type}/{api_target}"

        try:
            print(f"{C.YELLOW}[*] Forbinder til VirusTotal API (Henter primær analyse)...{C.RESET}")
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                json_data = res.json()
                attrs = json_data.get('data', {}).get('attributes', {})
                stats = attrs.get('last_analysis_stats', {})
                
                # Original Logik Bevaret & Udvidet
                self.data["Malicious"] = stats.get('malicious', 0)
                self.data["Undetected"] = stats.get('undetected', 0)
                self.data["Suspicious"] = stats.get('suspicious', 0)
                
                if self.data["Malicious"] > 0:
                    print(f"{C.RED}    🔥 KRITISK TRUSSEL: Flaged som 'Malicious' af {self.data['Malicious']} motorer!{C.RESET}")
                elif self.data["Suspicious"] > 0:
                    print(f"{C.YELLOW}    [!] MISTÆNKELIGT: Flaget som 'Suspicious' af {self.data['Suspicious']} motorer.{C.RESET}")
                else:
                    print(f"{C.GREEN}    ✓ RENT: {self.data['Undetected']} motorer anser target for at være rent.{C.RESET}")

                # --- NY V8: TRUSSELS KATEGORISERING ---
                if 'popular_threat_classification' in attrs:
                    threat_class = attrs['popular_threat_classification']
                    if 'suggested_threat_label' in threat_class:
                        self.data["Populært_Trusselsnavn"] = threat_class['suggested_threat_label']
                        print(f"{C.MAGENTA}    🔥 Malware Familie: {self.data['Populært_Trusselsnavn']}{C.RESET}")
                    
                    if 'popular_threat_category' in threat_class:
                        categories = [cat['value'] for cat in threat_class['popular_threat_category']]
                        self.data["Trussels_Kategori"] = categories
                        print(f"{C.MAGENTA}    🔥 Kategorier: {', '.join(categories)}{C.RESET}")

                # Gemmer lidt af det rå data til fremtidig brug
                if 'meaningful_name' in attrs: self.data["Details"]["Navn"] = attrs['meaningful_name']
                if 'type_description' in attrs: self.data["Details"]["Filtype"] = attrs['type_description']

                # --- NY V8: COMMUNITY COMMENTS (Intelligence Extract) ---
                self._fetch_community_comments(headers, api_target)

            elif res.status_code == 404:
                print(f"{C.DIM}    [-] Target findes endnu ikke i VirusTotals database.{C.RESET}")
            else:
                print(f"{C.RED}    [!] Fejl fra VirusTotal: {res.status_code} - {res.text}{C.RESET}")

        except Exception as e:
            print(f"{C.RED}[!] Systemfejl under VT API kommunikation: {e}{C.RESET}")

        self.save()

    def _fetch_community_comments(self, headers, api_target):
        """NY V8: Henter sikkerhedsforskeres kommentarer på target"""
        comment_url = f"https://www.virustotal.com/api/v3/{self.target_type}/{api_target}/comments?limit=3"
        try:
            print(f"{C.YELLOW}[*] Henter Threat Community Intel (Kommentarer)...{C.RESET}")
            c_res = requests.get(comment_url, headers=headers, timeout=10)
            if c_res.status_code == 200:
                comments = c_res.json().get('data', [])
                if comments:
                    for c in comments:
                        text = c.get('attributes', {}).get('text', '').replace('\n', ' | ')
                        self.data["Community_Kommentarer"].append(text)
                        print(f"{C.CYAN}      -> Intel: {text[:100]}...{C.RESET}")
                else:
                    print(f"{C.DIM}      [-] Ingen community kommentarer fundet.{C.RESET}")
        except Exception:
            pass

    def _generate_osint_links(self):
        """NY V8: Bygger direkte links til Sandbox systemer"""
        if self.target_type == "files":
            print(f"\n{C.YELLOW}[*] Genererer Taktiske Sandbox Genveje...{C.RESET}")
            self.data["Direct_OSINT_Links"]["VirusTotal"] = f"https://www.virustotal.com/gui/file/{self.target}"
            self.data["Direct_OSINT_Links"]["AnyRun"] = f"https://any.run/submissions/#filehash:{self.target}"
            self.data["Direct_OSINT_Links"]["HybridAnalysis"] = f"https://www.hybrid-analysis.com/search?query={self.target}"
            
            print(f"{C.CYAN}    -> Any.Run (Live Detonation): {self.data['Direct_OSINT_Links']['AnyRun']}{C.RESET}")
            print(f"{C.CYAN}    -> HybridAnalysis (CrowdStrike): {self.data['Direct_OSINT_Links']['HybridAnalysis']}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        # Renser filnavnet sikkert uanset type
        safe_target = self.target.replace("http://", "").replace("https://", "").replace("/", "_")[:30]
        filename = f"{session['loot_folder']}/26_VIRUSTOTAL_{safe_target}.json"
        
        # Sikker overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Threat Intel Rapport gemt: {filename}{C.RESET}")