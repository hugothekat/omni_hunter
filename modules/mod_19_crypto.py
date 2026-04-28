# -*- coding: utf-8 -*-
import json
import os
import requests
import time
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search # NY V8 TILFØJELSE: Web-søgning efter adressen

class CryptoLedgerAnalyzer:
    def __init__(self, address):
        self.address = address.strip()
        self.data = {
            "Adresse": self.address, 
            "Valuta": "Ukendt", 
            "Balance": 0, 
            "Total_Modtaget": 0, 
            "Transaktioner": 0, 
            "Seneste_Transaktioner": [],   # NY V8 TILFØJELSE: Aktivitetssporing
            "Svindel_Advarsler": [],       # NY V8 TILFØJELSE: Threat Intel
            "Web_Spor": [],                # NY V8 TILFØJELSE: Hacker forums / Pastes
            "Direct_OSINT_Links": {},      # NY V8 TILFØJELSE: Klikbare Arkham/Explorer links
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[19] Blockchain Efterretning (Whale-Trace & Threat Intel V8)\n{'='*60}{C.RESET}")
        print(f"[*] Analyserer krypto-adresse: {self.address}")

        self._generate_osint_links()

        if self.address.startswith("1") or self.address.startswith("3") or self.address.startswith("bc1"):
            self.data["Valuta"] = "Bitcoin (BTC)"
            self._trace_btc()
        elif self.address.startswith("0x"):
            self.data["Valuta"] = "Ethereum (ETH) / EVM Compatible"
            self._trace_eth()
        else:
            print(f"{C.RED}[!] Ukendt kæde-format. Understøtter BTC og ETH (samt EVM kæder).{C.RESET}")

        # --- NY V8 TILFØJELSE: Dork the Web for Scam/Ransomware reports ---
        if driver:
            self._dork_crypto_address(driver)
        else:
            print(f"{C.DIM}[-] Ingen stealth-driver angivet. Skipper Web Threat-Opslag.{C.RESET}")

        self.save()

    def _generate_osint_links(self):
        """NY V8 TILFØJELSE: Bygger genveje til manuelle dybde-analyser"""
        print(f"\n{C.YELLOW}[*] Genererer direkte OSINT Explorer links...{C.RESET}")
        
        self.data["Direct_OSINT_Links"]["Arkham_Intelligence"] = f"https://platform.arkhamintelligence.com/explorer/address/{self.address}"
        
        if self.address.startswith("0x"):
            self.data["Direct_OSINT_Links"]["Etherscan"] = f"https://etherscan.io/address/{self.address}"
            self.data["Direct_OSINT_Links"]["BscScan"] = f"https://bscscan.com/address/{self.address}"
            self.data["Direct_OSINT_Links"]["PolygonScan"] = f"https://polygonscan.com/address/{self.address}"
        else:
            self.data["Direct_OSINT_Links"]["Blockchain_com"] = f"https://www.blockchain.com/explorer/addresses/btc/{self.address}"
            
        print(f"{C.CYAN}    -> Arkham (Platform for De-Anonymisering): {self.data['Direct_OSINT_Links']['Arkham_Intelligence']}{C.RESET}")

    def _trace_btc(self):
        try:
            print(f"{C.YELLOW}[*] Forbinder til Bitcoin Blockchain API...{C.RESET}")
            res = requests.get(f"https://blockchain.info/rawaddr/{self.address}", timeout=10).json()
            self.data["Balance"] = res.get("final_balance", 0) / 100000000
            self.data["Total_Modtaget"] = res.get("total_received", 0) / 100000000
            self.data["Transaktioner"] = res.get("n_tx", 0)

            print(f"{C.GREEN}    ✓ Netværk: Bitcoin{C.RESET}")
            print(f"{C.GREEN}    ✓ Aktuel Balance: {self.data['Balance']} BTC{C.RESET}")
            print(f"{C.GREEN}    ✓ Total Modtaget: {self.data['Total_Modtaget']} BTC{C.RESET}")
            print(f"{C.GREEN}    ✓ Antal Transaktioner: {self.data['Transaktioner']}{C.RESET}")
            
            # --- NY V8 TILFØJELSE: Udtrækker de seneste transaktioner for whale-tracking ---
            txs = res.get("txs", [])
            if txs:
                print(f"\n{C.YELLOW}[*] Analyserer seneste aktivitet...{C.RESET}")
                for tx in txs[:3]: # Top 3 seneste txs
                    tx_hash = tx.get("hash")
                    tx_time = datetime.fromtimestamp(tx.get("time", 0)).strftime('%Y-%m-%d %H:%M:%S')
                    # Meget forsimplet beløb (fokus på tidsstempel og aktivitet)
                    self.data["Seneste_Transaktioner"].append({"Dato": tx_time, "TX_Hash": tx_hash})
                    print(f"{C.CYAN}      -> TX Dato: {tx_time} | Hash: {tx_hash[:15]}...{C.RESET}")

        except Exception as e:
            print(f"{C.RED}    [-] Fejl ved BTC opslag: Kunne ikke finde adresse.{C.RESET}")

    def _trace_eth(self):
        try:
            print(f"{C.YELLOW}[*] Forbinder til Etherscan API (Balance)...{C.RESET}")
            res = requests.get(f"https://api.etherscan.io/api?module=account&action=balance&address={self.address}&tag=latest", timeout=10).json()
            if res.get("status") == "1":
                bal = int(res.get("result", 0)) / 10**18
                self.data["Balance"] = bal
                print(f"{C.GREEN}    ✓ Netværk: Ethereum{C.RESET}")
                print(f"{C.GREEN}    ✓ Aktuel Balance: {bal:.4f} ETH{C.RESET}")
                print(f"{C.MAGENTA}    [!] Note: 0x adresser kan også have midler på BSC, Polygon, Arbitrum etc.{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen data fundet på Etherscan.{C.RESET}")
                
            # --- NY V8 TILFØJELSE: Trækker Transaction History for ETH ---
            print(f"\n{C.YELLOW}[*] Forbinder til Etherscan API (Seneste Transaktioner)...{C.RESET}")
            tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={self.address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc"
            tx_res = requests.get(tx_url, timeout=10).json()
            
            if tx_res.get("status") == "1" and tx_res.get("result"):
                transactions = tx_res.get("result")
                self.data["Transaktioner"] = len(transactions) # Hvis mere end 5, viser den bare 5 som baseline
                
                for tx in transactions[:3]:
                    tx_hash = tx.get("hash")
                    tx_time = datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime('%Y-%m-%d %H:%M:%S')
                    value_eth = int(tx.get("value", 0)) / 10**18
                    direction = "UD" if tx.get("from", "").lower() == self.address.lower() else "IND"
                    
                    self.data["Seneste_Transaktioner"].append({
                        "Dato": tx_time, "Retning": direction, "Beløb_ETH": value_eth, "TX_Hash": tx_hash
                    })
                    
                    color = C.RED if direction == "UD" else C.GREEN
                    print(f"{color}      -> {direction}: {value_eth:.4f} ETH | Dato: {tx_time} | TX: {tx_hash[:10]}...{C.RESET}")
            else:
                print(f"{C.DIM}      [-] Ingen nyere Ethereum-transaktioner fundet på denne kæde.{C.RESET}")

        except Exception as e:
            print(f"{C.RED}    [-] Fejl ved ETH opslag: {e}{C.RESET}")

    def _dork_crypto_address(self, driver):
        """NY V8 TILFØJELSE: Dorker adressen for at finde pastebins, scams og darkweb referencer"""
        print(f"\n{C.YELLOW}[*] Threat Intelligence: Søger på nettet efter adressen (Scams/Hacks)...{C.RESET}")
        
        # Vi søger generelt efter adressen for at fange forum posts og pastebins
        dork = f'"{self.address}"'
        links = omni_dork_search(driver, dork, max_links=5)
        
        if links:
            for link in links:
                url = link['url']
                title = link.get('title', '').lower()
                snippet = link.get('snippet', '').lower()
                
                # Hvis vi spotter scam/hack relaterede ord i resultatet
                if any(x in title or x in snippet for x in ["scam", "hack", "ransomware", "stolen", "phishing", "abuse", "fraud"]):
                    print(f"{C.RED}    🔥 KRITISK: Adresse er kædet sammen med svindel/hacking!{C.RESET}")
                    print(f"{C.RED}      -> {url}{C.RESET}")
                    if url not in self.data["Svindel_Advarsler"]:
                        self.data["Svindel_Advarsler"].append(url)
                else:
                    # Almindelige fund på nettet (github, pastebin, forums)
                    print(f"{C.GREEN}    ✓ Web-Spor Fundet: {url[:70]}...{C.RESET}")
                    if url not in self.data["Web_Spor"]:
                        self.data["Web_Spor"].append(url)
        else:
            print(f"{C.DIM}    [-] Ingen offentlige spor eller svindel-rapporter fundet via Dorking.{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/19_CRYPTO_{self.address[:10]}.json"
        
        # NY V8 TILFØJELSE: Sikker overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")