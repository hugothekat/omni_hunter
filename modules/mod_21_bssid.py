# -*- coding: utf-8 -*-
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import CONFIG # Til at hente evt Wigle API nøgle

class BSSIDGeofencer:
    """Geolocates a router BSSID using Wigle (if configured) and Mylnikov API"""
    def __init__(self, bssid):
        self.bssid = bssid.strip().replace("-", ":").upper() # Wigle foretrækker upper
        self.wigle_key = CONFIG.get("api_keys", {}).get("wigle", "")
        
        self.data = {
            "BSSID": self.bssid, 
            "Producent_OUI": "Ukendt",    # NY V8 TILFØJELSE: Router mærke
            "Fundet": False, 
            "Kilde": "",                  # NY V8 TILFØJELSE: Mylnikov eller Wigle
            "Netværksnavn_SSID": "",      # NY V8 TILFØJELSE: Kan ofte udtrækkes fra Wigle
            "Lat": None, 
            "Lon": None, 
            "Direct_OSINT_Links": {},     # NY V8 TILFØJELSE: Både Google og Apple Maps
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[21] BSSID Geofencer (MAC Lokations-sporing V8)\n{'='*60}{C.RESET}")
        print(f"[*] Starter global triangulering for router MAC: {self.bssid}")

        # --- NY V8: Resolve OUI (Producent af netværkskortet) ---
        self._resolve_oui()

        # --- NY V8: Multi-API Fallback Engine ---
        # 1. Forsøg Wigle (Mest præcis, kræver API)
        if self.wigle_key:
            print(f"{C.YELLOW}[*] Wigle API-Nøgle detekteret. Forbinder til Wigle.net databasen...{C.RESET}")
            if self._query_wigle():
                self._generate_map_links()
                self.save()
                return # Stopper her hvis Wigle fandt den

        # 2. Forsøg Mylnikov (Gratis fallback)
        print(f"{C.YELLOW}[*] Forbinder til Mylnikov Open Wifi API...{C.RESET}")
        if self._query_mylnikov():
            self._generate_map_links()
            
        self.save()

    def _resolve_oui(self):
        """Finder ud af hvilken hardware routeren er lavet af (f.eks Netgear, Sagemcom)"""
        oui = self.bssid.replace(":", "")[:6]
        print(f"\n{C.YELLOW}[*] Slår OUI ({oui}) op for at finde hardware producent...{C.RESET}")
        try:
            res = requests.get(f"https://api.macvendors.com/{oui}", timeout=5)
            if res.status_code == 200 and res.text:
                self.data["Producent_OUI"] = res.text.strip()
                print(f"{C.MAGENTA}    ✓ Router Producent identificeret: {self.data['Producent_OUI']}{C.RESET}")
            else:
                print(f"{C.DIM}    [-] OUI ikke fundet i de offentlige registre.{C.RESET}")
        except Exception:
            pass

    def _query_wigle(self):
        """Søger i Wigle.net databasen. Kræver at 'wigle': 'encoded_auth_token' er i config.json"""
        headers = {
            'Authorization': f'Basic {self.wigle_key}',
            'Accept': 'application/json'
        }
        url = f"https://api.wigle.net/api/v2/network/detail?netid={self.bssid}"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                json_data = res.json()
                if json_data.get("success") and len(json_data.get("results", [])) > 0:
                    net_data = json_data["results"][0]
                    self.data["Fundet"] = True
                    self.data["Kilde"] = "Wigle.net"
                    self.data["Lat"] = net_data.get("trilat")
                    self.data["Lon"] = net_data.get("trilong")
                    self.data["Netværksnavn_SSID"] = net_data.get("ssid", "Skjult")
                    
                    print(f"{C.GREEN}    🔥 BINGO! Trianguleret lokation via Wigle!{C.RESET}")
                    print(f"{C.GREEN}    ✓ Netværksnavn (SSID): {self.data['Netværksnavn_SSID']}{C.RESET}")
                    print(f"{C.GREEN}    ✓ Breddegrad: {self.data['Lat']} | Længdegrad: {self.data['Lon']}{C.RESET}")
                    return True
                else:
                    print(f"{C.DIM}    [-] Wigle.net havde ingen GPS koordinater på dette BSSID.{C.RESET}")
            elif res.status_code == 401:
                print(f"{C.RED}    [!] Wigle API Nøgle er ugyldig. Falder tilbage til Mylnikov.{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [!] Fejl ved Wigle opslag: {e}{C.RESET}")
        
        return False

    def _query_mylnikov(self):
        """Det originale Mylnikov opslag som gratis fallback"""
        url = f"https://api.mylnikov.org/geolocation/wifi?v=1.1&data={self.bssid.lower()}"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("result") == 200:
                self.data["Fundet"] = True
                self.data["Kilde"] = "Mylnikov Open API"
                self.data["Lat"] = res["data"]["lat"]
                self.data["Lon"] = res["data"]["lon"]

                print(f"{C.GREEN}    🔥 BINGO! Fysisk lokation fastslået via Mylnikov!{C.RESET}")
                print(f"{C.GREEN}    ✓ Breddegrad: {self.data['Lat']} | Længdegrad: {self.data['Lon']}{C.RESET}")
                return True
            else:
                print(f"{C.YELLOW}    [-] Routeren findes ikke i de åbne databaser.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved Mylnikov API opslag: {e}{C.RESET}")
            
        return False

    def _generate_map_links(self):
        if self.data["Lat"] and self.data["Lon"]:
            print(f"\n{C.YELLOW}[*] Genererer Taktiske Kort-Links...{C.RESET}")
            
            # Google Maps
            g_link = f"https://www.google.com/maps?q={self.data['Lat']},{self.data['Lon']}"
            
            # Apple Maps (Ofte bedre opløsning i LookAround end Google Streetview)
            a_link = f"http://googleusercontent.com/maps.apple.com/0ll={self.data['Lat']},{self.data['Lon']}&q=Target_Router"
            
            self.data["Direct_OSINT_Links"]["Google_Maps"] = g_link
            self.data["Direct_OSINT_Links"]["Apple_Maps"] = a_link
            
            print(f"{C.CYAN}    -> Google Maps: {g_link}{C.RESET}")
            print(f"{C.CYAN}    -> Apple Maps: {a_link}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/21_BSSID_{self.bssid.replace(':', '')}.json"
        
        # Sikker overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] BSSID Rapport gemt: {filename}{C.RESET}")