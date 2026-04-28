# -*- coding: utf-8 -*-
import requests
import json
import os
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup 

from core.utils import C, session
from core.network import CONFIG, omni_dork_search # NY V8: Tilføjet omni_dork_search

class DarkwebScanner: 
    def __init__(self, query):
        self.query = query.strip()
        self.data = {
            "Søgning": self.query, 
            "Proxy_Type": "Clearnet",
            "Onion_Hits": [], 
            "Ekstraherede_Emails": [], # NY V8: Finder skjulte emails på darkweb
            "Ekstraherede_Crypto": [], # NY V8: Finder BTC/XMR adresser
            "Clearnet_Onion_Spor": [], # NY V8: Indexed onions på det åbne net
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[08] Mørkenet-efterretning (Ahmia Deep Context & Crypto Harvest)\n{'='*60}{C.RESET}")
        print(f"Target Query: {self.query}\n")
        
        # --- NYT V7/V8: HÅNDTERING AF RIGTIGT ONION LINK NÅR TOR ER AKTIVERET ---
        req_session = requests.Session()
        
        if CONFIG.get("use_tor_proxy"):
            print(f"{C.YELLOW}[*] TOR PROXY AKTIVERET: Ruter trafiken gennem Onion-netværket...{C.RESET}")
            req_session.proxies = {
                'http': CONFIG.get("tor_proxy_url", "socks5h://127.0.0.1:9050"),
                'https': CONFIG.get("tor_proxy_url", "socks5h://127.0.0.1:9050")
            }
            self.data["Proxy_Type"] = "TOR Network"
            url = f"http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={requests.utils.quote(self.query)}"
        else:
            print(f"{C.YELLOW}[*] Crawler Ahmia.fi via Clearnet...{C.RESET}")
            url = f"https://ahmia.fi/search/?q={requests.utils.quote(self.query)}"
            
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"}
        
        try:
            res = req_session.get(url, headers=headers, timeout=60)
            
            soup = BeautifulSoup(res.text, 'html.parser')
            results = soup.find_all('li', class_='searchResultsItem')
            
            if not results:
                print(f"{C.YELLOW}    [-] Ingen nævneværdige .onion resultater fundet på Ahmia.{C.RESET}")
            else:
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
                        
                        # NY V8 TILFØJELSE: Intel Harvest via Regex
                        self._harvest_intel(beskrivelse, onion_link)
                        
                        self.data["Onion_Hits"].append({
                            "Titel": titel,
                            "URL": onion_link,
                            "Kontekst": beskrivelse
                        })

        except requests.exceptions.ProxyError:
            print(f"{C.RED}    [!] Proxy Fejl: Kunne ikke forbinde til Tor. Tjek at Tor-tjenesten kører på maskinen.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved crawling af Dark Web proxy: {e}{C.RESET}")
            
        # NY V8 TILFØJELSE: Søg efter indekserede onions på Clearnet via proxy-dorks
        if driver:
            self._search_clearnet_proxies(driver)
        
        self.save()

    def _harvest_intel(self, text, source_link):
        """NY V8: Udtrækker Emails og Crypto-adresser fra Darkweb beskrivelser"""
        # Tjekker for emails
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        for em in emails:
            if em.lower() not in self.data["Ekstraherede_Emails"]:
                self.data["Ekstraherede_Emails"].append(em.lower())
                print(f"{C.MAGENTA}      ✓ Email fundet i Mørkenettet: {em.lower()}{C.RESET}")
                
        # Tjekker for Bitcoin (P2PKH, P2SH, Bech32) og Monero
        btc_pattern = re.findall(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', text)
        xmr_pattern = re.findall(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b', text)
        
        for btc in btc_pattern:
            if btc not in self.data["Ekstraherede_Crypto"]:
                self.data["Ekstraherede_Crypto"].append(f"BTC: {btc}")
                print(f"{C.MAGENTA}      ✓ Bitcoin Adresse fundet: {btc}{C.RESET}")
                
        for xmr in xmr_pattern:
            if xmr not in self.data["Ekstraherede_Crypto"]:
                self.data["Ekstraherede_Crypto"].append(f"XMR: {xmr}")
                print(f"{C.MAGENTA}      ✓ Monero Adresse fundet: {xmr}{C.RESET}")

    def _search_clearnet_proxies(self, driver):
        """NY V8: Dorker clearnet for Tor2Web proxy sider som lækker info til Google"""
        print(f"\n{C.YELLOW}[*] Dorking Clearnet Tor-Proxies (Google Index)...{C.RESET}")
        
        # Søger efter vores query på kendte proxy domæner
        dork = f'(site:onion.ly OR site:onion.ws OR site:onion.pet OR site:onion.dog) "{self.query}"'
        links = omni_dork_search(driver, dork, max_links=3)
        
        if links:
            for link in links:
                url = link.get('url', '')
                print(f"{C.RED}    🔥 CLEARNET ONION HIT: {url[:80]}{C.RESET}")
                if url not in self.data["Clearnet_Onion_Spor"]:
                    self.data["Clearnet_Onion_Spor"].append(url)
                    
                snippet = link.get('snippet', '')
                self._harvest_intel(snippet, url)
        else:
            print(f"{C.DIM}    [-] Ingen indekserede lækager fundet på åbne Tor-proxies.{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/08_DARKWEB_{self.query.replace(' ', '_')}.json"
        
        # NY V8 TILFØJELSE: Sikker overskrivning af fil
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Dark Web rapport gemt ({len(self.data['Onion_Hits'])} Ahmia-fund, {len(self.data['Clearnet_Onion_Spor'])} Clearnet-fund): {filename}{C.RESET}")

DarkWebIntelligence = DarkwebScanner