import os
import json
import csv
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class GoliathGraphExporter:
    """Samler alt loot data og genererer en Maltego/Gephi venlig CSV-fil."""
    def __init__(self):
        self.loot_dir = session["loot_folder"]
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.csv_file = f"GRAPH_EXPORT_{self.timestamp}.csv"

    def generate(self):
        print(f"\n{C.CYAN}{'='*60}\n[28] Visual Graph Exporter (Maltego / Link Analyse)\n{'='*60}{C.RESET}")
        files = list(Path(self.loot_dir).glob("*.json"))
        
        if not files:
            print(f"{C.YELLOW}[!] Ingen JSON-rapporter fundet i {self.loot_dir}.{C.RESET}")
            return

        print(f"{C.YELLOW}[*] Støvsuger {len(files)} bevisfiler for relationer (Nodes & Edges)...{C.RESET}")
        
        # Liste til vores netværks-links: [Kilde, Forbindelse_Type, Mål]
        edges = []
        target_name = session.get('name', 'Hovedmål')

        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                
                # Hvis vi finder Email-mønstre
                if "Email" in data:
                    edges.append([target_name, "Har Email", data["Email"]])
                    # Hvis emailen var med i datalæk
                    if "Lækager" in data or "Free_Breach_Hits" in data:
                        leaks = data.get("Lækager", []) + data.get("Free_Breach_Hits", [])
                        for leak in leaks:
                            edges.append([data["Email"], "Lækket I", leak])
                
                # Hvis vi finder Telefonnumre (Fra Krak)
                if "Telefonnumre" in data:
                    for tlf in data["Telefonnumre"]:
                        edges.append([target_name, "Har Telefon", tlf])
                        
                # Fra TITAN mass-scan
                if "Intelligence" in data:
                    intel = data["Intelligence"]
                    for e in intel.get("Emails", []): edges.append(["TITAN Mappe", "Indeholder Email", e])
                    for k in intel.get("Krypto", []): edges.append(["TITAN Mappe", "Indeholder Wallet", k])

            except Exception: continue

        # Skriv til CSV
        self._write_csv(edges)

    def _write_csv(self, edges):
        # Fjern dubletter
        unique_edges = []
        for edge in edges:
            if edge not in unique_edges:
                unique_edges.append(edge)

        file_path = os.path.join(self.loot_dir, self.csv_file)
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Relation", "Target"]) # Maltego format headers
            writer.writerows(unique_edges)

        print(f"{C.GREEN}[✓] Data-netværk eksporteret succesfuldt!{C.RESET}")
        print(f"{C.CYAN}    -> Fil klar til import i Maltego/Gephi: {file_path}{C.RESET}")
        print(f"{C.YELLOW}    (Dette kortlægger {len(unique_edges)} forbindelser visuelt!){C.RESET}")