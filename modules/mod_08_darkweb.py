# -*- coding: utf-8 -*-
import requests
import json
import os
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup 

from core.utils import C, session
from core.network import CONFIG # Til at hente Tor opsætning

class DarkWebIntelligence:
    def __init__(self, query):
        self.query = query.strip()
        self.data = {
            "Søgning": self.query, 
            "Proxy_Type": "Clearnet",
            "Onion_Hits": [], 
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[08] Mørkenet-efterretning (Ahmia Deep Context)\n{'='*60}{C.RESET}")
        print(f"Target Query: {self.query}\n")
        
        url = f"https://ahmia.fi/search/?q={requests.utils.quote(self.query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"}
        
        req_session = requests.Session()
        
        # --- NYT: Tjekker dynamisk om systemet er bedt om at køre via TOR ---
        if CONFIG.get("use_tor_proxy"):
            print(f"{C.YELLOW}[*] TOR PROXY AKTIVERET: Ruter trafiken gennem Onion-netværket...{C.RESET}")
            req_session.proxies = {
                'http': CONFIG["tor_proxy_url"],
                'https': CONFIG["tor_proxy_url"]
            }
            self.data["Proxy_Type"] = "TOR Network"
        else:
            print(f"{C.YELLOW}[*] Crawler Ahmia.fi via Clearnet...{C.RESET}")
        
        try:
            res = req_session.get(url, headers=headers, timeout=20)
            
            soup = BeautifulSoup(res.text, 'html.parser')
            results = soup.find_all('li', class_='searchResultsItem')
            
            if not results:
                print(f"{C.YELLOW}    [-] Ingen nævneværdige .onion resultater fundet.{C.RESET}")
            else:
                # Udvidet fra 10 til 20 hits for mere dybde
                for item in results[:20]: 
                    title_tag = item.find('h4')
                    link_tag = item.find('cite')
                    desc_tag = item.find('p')
                    
                    if link_tag:
                        onion_link = link_tag.text.strip()
                        titel = title_tag.text.strip() if title_tag else "Ukendt Titel"
                        beskrivelse = desc_tag.text.strip() if desc_tag else "Ingen beskrivelse tilgængelig"
                        
                        print(f"{C.RED}    🔥 HIT: {titel}{C.RESET}")
                        print(f"{C.CYAN}      -> Link: {onion_link}{C.RESET}")
                        print(f"{C.DIM}      -> Udklip: {beskrivelse[:100]}...{C.RESET}")
                        
                        self.data["Onion_Hits"].append({
                            "Titel": titel,
                            "URL": onion_link,
                            "Kontekst": beskrivelse
                        })

        except requests.exceptions.ProxyError:
            print(f"{C.RED}    [!] Proxy Fejl: Kunne ikke forbinde til Tor. Tjek at Tor-tjenesten kører på maskinen.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved crawling af Dark Web proxy: {e}{C.RESET}")
        
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/08_DARKWEB_{self.query.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Dark Web rapport gemt ({len(self.data['Onion_Hits'])} fund): {filename}{C.RESET}")