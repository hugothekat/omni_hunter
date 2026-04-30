# -*- coding: utf-8 -*-
import os
import json
import csv
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class GoliathGraphExporter:
    """GOLIATH V8: Universal Link Analysis Engine til Maltego, Gephi & Obsidian."""
    def __init__(self):
        self.loot_dir = session.get("loot_folder", "loot_evidence")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.csv_file = f"GOLIATH_NETWORK_MAP_{self.timestamp}.csv"
        self.edges = []
        self.target_name = session.get('name', 'Hovedmål')

    def generate(self):
        print(f"\n{C.CYAN}{'='*60}\n[28] Visual Link Analysis Exporter (GOLIATH V8)\n{'='*60}{C.RESET}")
        files = list(Path(self.loot_dir).glob("*.json"))
        
        if not files:
            print(f"{C.YELLOW}[!] Ingen JSON-rapporter fundet i {self.loot_dir}. Kør nogle skanninger først!{C.RESET}")
            return

        print(f"{C.YELLOW}[*] Konstruerer relations-matrix ud fra {len(files)} bevisfiler...{C.RESET}")
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                self._process_json_logic(data, file.name)
            except Exception:
                continue

        if self.edges:
            self._write_csv()
        else:
            print(f"{C.RED}[!] Ingen brugbare relationer fundet i dataen.{C.RESET}")

    def _process_json_logic(self, data, filename):
        """Intelligent mapping af edges baseret på tværgående modul-output"""
        
        # 1. PERSONDATA & EMAILS
        if "Email" in data or "Brugernavn" in data:
            uid = data.get("Email") or data.get("Brugernavn")
            self.edges.append([self.target_name, "Relateret_Til", uid])
            
            # Breach relationer (Modul 03 / Modul 05)
            if "Data_Leaks" in data:
                for leak in data["Data_Leaks"]:
                    self.edges.append([uid, "Eksponeret_I", leak.get("Name", "Ukendt Læk")])

        # 2. TELEFONNUMRE & BOPÆL
        if "Telefonnumre" in data:
            for tlf in data["Telefonnumre"]:
                self.edges.append([self.target_name, "Bruger_Telefon", tlf])
        
        if "Ejendom" in data and data["Ejendom"].get("Vej"):
            addr = f"{data['Ejendom']['Vej']}, {data['Ejendom']['By']}"
            self.edges.append([self.target_name, "Bopæl", addr])

        # 3. NETVÆRK & IP (Modul 10 / Modul 21)
        if "IP" in data:
            ip = data["IP"]
            self.edges.append([self.target_name, "Forbundet_Til_IP", ip])
            if data.get("Reverse_DNS"):
                self.edges.append([ip, "Opløser_Til", data["Reverse_DNS"]])

        if "BSSID" in data:
            bssid = data["BSSID"]
            self.edges.append([self.target_name, "Set_Nær_BSSID", bssid])
            if data.get("Producent_OUI") and data["Producent_OUI"] != "Ukendt":
                self.edges.append([bssid, "Hardware_Fra", data["Producent_OUI"]])

        # 4. KØRETØJER (Modul 20)
        if "RegNr" in data:
            plate = data["RegNr"]
            self.edges.append([self.target_name, "Ejer_Køretøj", plate])
            if data.get("Stelnummer"):
                self.edges.append([plate, "Har_VIN", data["Stelnummer"]])

        # 5. BLOCKCHAIN (Modul 19)
        if "Adresse" in data and "Valuta" in data:
            wallet = data["Adresse"]
            self.edges.append([self.target_name, "Kontrollerer_Wallet", wallet])
            for tx in data.get("Seneste_Transaktioner", []):
                if tx.get("TX_Hash"):
                    self.edges.append([wallet, "Transaktion", tx["TX_Hash"][:15]])

        # 6. TITAN MASS-SCAN (Modul 16)
        if "Case_Intelligence" in data:
            intel = data["Case_Intelligence"]
            for email in intel.get("Digital_Footprint", {}).get("Emails", {}):
                self.edges.append(["TITAN_Dataset", "Fundet_Email", email])
            for bank in intel.get("Financial_Leads", {}).get("Bankkonti", []):
                self.edges.append([self.target_name, "Tilknyttet_Bank", bank])

    def _write_csv(self):
        # Fjern dubletter via set-mønster for at undgå "spaghetti-graf"
        unique_edges = []
        seen = set()
        for edge in self.edges:
            edge_tuple = tuple(edge)
            if edge_tuple not in seen:
                unique_edges.append(edge)
                seen.add(edge_tuple)

        file_path = os.path.join(self.loot_dir, self.csv_file)
        
        # Sikker fil-overskrivning
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Standard headers for Maltego og Gephi import
            writer.writerow(["Source", "Edge Type", "Target"]) 
            writer.writerows(unique_edges)

        print(f"{C.GREEN}[✓] Relations-netværk eksporteret succesfuldt!{C.RESET}")
        print(f"{C.CYAN}    -> Fil klar til professionel link-analyse: {file_path}{C.RESET}")
        print(f"{C.MAGENTA}    [*] Kortlagte unikke relationer: {len(unique_edges)}{C.RESET}")