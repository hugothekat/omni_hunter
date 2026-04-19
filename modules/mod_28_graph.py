import os
import json
import csv
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class GoliathGraphExporter:
    """Trawler loot-mappen og bygger en netværksgraf (Nodes & Edges) til Maltego/Gephi"""
    def __init__(self):
        self.loot_dir = session["loot_folder"]
        self.nodes = set()
        self.edges = [] # Format: (Source, Target, Relation)

    def generate(self):
        print(f"\n{C.CYAN}[*] Starter Graph-Analyse af Sagsmappe...{C.RESET}")
        files = list(Path(self.loot_dir).glob("*.json"))
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                
                # Regler for at bygge grafen
                # Eksempel: Modul 03 (Breach) - Forbinder Email med Paste-links
                if "Email" in data and "Paste_Sites" in data:
                    email = data["Email"]
                    self.nodes.add(email)
                    for site in data["Paste_Sites"]:
                        self.nodes.add(site)
                        self.edges.append((email, site, "Optraeder_i_Leak"))

                # Eksempel: Modul 01 (Directory) - Forbinder Navn med Telefon og Adresse
                if "Identitet" in data:
                    navn = data["Identitet"]
                    self.nodes.add(navn)
                    for tlf in data.get("Telefonnumre", []):
                        self.nodes.add(tlf)
                        self.edges.append((navn, tlf, "Ejer_Telefon"))
                    if "Ejendom" in data and "Vej" in data["Ejendom"]:
                        adresse = f"{data['Ejendom']['Vej']}, {data['Ejendom'].get('By', '')}"
                        self.nodes.add(adresse)
                        self.edges.append((navn, adresse, "Bor_paa_Adresse"))

                # Eksempel: Modul 16 (TITAN) - Forbinder Filer med fundne CPR/Emails
                if "Case_Intelligence" in data:
                    intel = data["Case_Intelligence"]
                    for tlf in intel.get("Physical_Leads", {}).get("Adresser", []):
                        self.nodes.add(tlf)
                    for cpr in intel.get("ID_Documents", {}).get("CPR_Numre", []):
                        self.nodes.add(cpr)
                        self.edges.append(("TITAN_Dump", cpr, "Indeholder_CPR"))

            except Exception:
                continue

        self._export_to_csv()

    def _export_to_csv(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        edges_path = f"{self.loot_dir}/GRAPH_EDGES_{timestamp}.csv"
        
        with open(edges_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Target", "Label"])
            # Sikrer at vi kun eksporterer unikke edges
            for edge in list(set(self.edges)):
                writer.writerow([edge[0], edge[1], edge[2]])
                
        print(f"{C.GREEN}[✓] Netværksgraf eksporteret! Klar til Maltego/Gephi.{C.RESET}")
        print(f"    -> Link-fil: {edges_path}")
        print(f"    -> Total Nodes (Entiteter): {len(self.nodes)}")
        print(f"    -> Total Edges (Forbindelser): {len(set(self.edges))}")