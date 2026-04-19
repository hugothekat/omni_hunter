import os
import json
import requests
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class CryptoLedgerAnalyzer:
    def __init__(self, address):
        self.address = address.strip()
        self.data = {"Adresse": self.address, "Valuta": "Ukendt", "Balance": 0, "Total_Modtaget": 0, "Transaktioner": 0, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[19] Blockchain Efterretning (Crypto-Sporing)\n{'='*60}{C.RESET}")
        print(f"[*] Analyserer krypto-adresse: {self.address}")

        if self.address.startswith("1") or self.address.startswith("3") or self.address.startswith("bc1"):
            self.data["Valuta"] = "Bitcoin (BTC)"
            self._trace_btc()
        elif self.address.startswith("0x"):
            self.data["Valuta"] = "Ethereum (ETH)"
            self._trace_eth()
        else:
            print(f"{C.RED}[!] Ukendt kæde-format. Understøtter BTC og ETH.{C.RESET}")

        self.save()

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
        except Exception as e:
            print(f"{C.RED}    [-] Fejl ved BTC opslag: Kunne ikke finde adresse.{C.RESET}")

    def _trace_eth(self):
        try:
            print(f"{C.YELLOW}[*] Forbinder til Etherscan API...{C.RESET}")
            res = requests.get(f"https://api.etherscan.io/api?module=account&action=balance&address={self.address}&tag=latest", timeout=10).json()
            if res.get("status") == "1":
                bal = int(res.get("result", 0)) / 10**18
                self.data["Balance"] = bal
                print(f"{C.GREEN}    ✓ Netværk: Ethereum{C.RESET}")
                print(f"{C.GREEN}    ✓ Aktuel Balance: {bal:.4f} ETH{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen data fundet på Etherscan.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [-] Fejl ved ETH opslag: {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/19_CRYPTO_{self.address[:10]}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")