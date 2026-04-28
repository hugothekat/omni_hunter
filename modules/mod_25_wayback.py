# -*- coding: utf-8 -*-
import os
import json
import requests
import urllib.parse
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class WaybackMachineIntelligence:
    """Wayback Bevissikring, CDX Timeline Analysis og Auto-Preservation (GOLIATH V8)"""
    def __init__(self, url):
        self.url = url.strip()
        # Sikrer at vi har et gyldigt URL format
        if not self.url.startswith("http"):
            self.url = f"https://{self.url}"
            
        self.data = {
            "Mål": self.url, 
            "Arkiveret_Link": None,
            "Total_Snapshots": 0,          # NY V8 TILFØJELSE: CDX API
            "Første_Snapshot": None,       # NY V8 TILFØJELSE: Ældste bevis
            "Seneste_Snapshot": None,      # NY V8 TILFØJELSE: Nyeste bevis
            "Snapshot_Tidslinje": [],      # NY V8 TILFØJELSE: Fuld historik
            "Direct_OSINT_Links": {},      # NY V8 TILFØJELSE: Alternative arkiver
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[25] Wayback Bevissikring (CDX Timeline & Auto-Preservation)\n{'='*60}{C.RESET}")
        print(f"[*] Starter arkiv-efterforskning for: {self.url}")

        # 1. Alternative Arkiver (GhostArchive & Archive.today)
        self._generate_osint_links()

        # 2. CDX Timeline Scan (Finder AL historik, ikke kun det seneste)
        self._cdx_timeline_scan()

        # 3. Den originale tjek-og-download funktion (Bevissikring)
        print(f"\n{C.YELLOW}[*] Søger efter det bedste snapshot til offline bevissikring...{C.RESET}")
        try:
            res = requests.get(f"http://archive.org/wayback/available?url={self.url}", timeout=10).json()
            if "closest" in res.get("archived_snapshots", {}):
                hit = res["archived_snapshots"]["closest"]["url"]
                self.data["Arkiveret_Link"] = hit
                print(f"{C.GREEN}    🔥 ARKIVERET VERSION KØRER: {hit}{C.RESET}")
                
                # Bevissikring: Download hele siden offline
                self._download_archive(hit)
            else:
                print(f"{C.YELLOW}    [-] Ingen tidligere arkiveret version fundet i den offentlige database.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved arkiv-søgning: {e}{C.RESET}")
            
        # 4. Force Archive (Tvinger Wayback til at gemme siden, som den ser ud LIGE NU)
        self._force_new_snapshot()
        
        self.save()

    def _generate_osint_links(self):
        """NY V8: Bygger links til alternative "Rogue" arkiver, der ignorerer robots.txt"""
        print(f"{C.YELLOW}[*] Genererer links til uafhængige arkiver (GhostArchive / Archive.today)...{C.RESET}")
        encoded_url = urllib.parse.quote(self.url)
        
        self.data["Direct_OSINT_Links"]["Archive_Today"] = f"https://archive.is/{self.url}"
        self.data["Direct_OSINT_Links"]["GhostArchive"] = f"https://ghostarchive.org/search?term={encoded_url}"
        
        print(f"{C.CYAN}    -> Archive.today (God til blokerede sider): {self.data['Direct_OSINT_Links']['Archive_Today']}{C.RESET}")
        print(f"{C.CYAN}    -> GhostArchive (God til slettede YouTube videoer): {self.data['Direct_OSINT_Links']['GhostArchive']}{C.RESET}")

    def _cdx_timeline_scan(self):
        """NY V8: Forbinder til CDX Server API for at trække hele sidens tidslinje"""
        print(f"\n{C.YELLOW}[*] Forbinder til CDX Server API for tidslinje-analyse...{C.RESET}")
        try:
            # Henter JSON output med de op til 10.000 seneste snapshots for URL'en
            cdx_url = f"http://web.archive.org/cdx/search/cdx?url={self.url}&output=json&fl=timestamp,original,statuscode,mimetype&collapse=timestamp:6&limit=10000"
            res = requests.get(cdx_url, timeout=15)
            
            if res.status_code == 200 and res.text.strip():
                data = res.json()
                if len(data) > 1: # Index 0 er headers (["timestamp", "original", "statuscode", "mimetype"])
                    snapshots = data[1:]
                    self.data["Total_Snapshots"] = len(snapshots)
                    
                    # Gemmer de 5 seneste for json fylde
                    for snap in snapshots[-5:]:
                        ts = snap[0]
                        formatted_date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]}"
                        wb_url = f"https://web.archive.org/web/{ts}/{snap[1]}"
                        self.data["Snapshot_Tidslinje"].append({"Dato": formatted_date, "URL": wb_url, "Status": snap[2]})

                    first_ts = snapshots[0][0]
                    last_ts = snapshots[-1][0]
                    self.data["Første_Snapshot"] = f"{first_ts[:4]}-{first_ts[4:6]}-{first_ts[6:8]}"
                    self.data["Seneste_Snapshot"] = f"{last_ts[:4]}-{last_ts[4:6]}-{last_ts[6:8]}"

                    print(f"{C.RED}    🔥 CDX DATA FUNDET! Siden er blevet arkiveret {self.data['Total_Snapshots']} gange.{C.RESET}")
                    print(f"{C.GREEN}    ✓ Første spor: {self.data['Første_Snapshot']}{C.RESET}")
                    print(f"{C.GREEN}    ✓ Seneste spor: {self.data['Seneste_Snapshot']}{C.RESET}")
                else:
                    print(f"{C.DIM}    [-] Ingen historik i CDX databasen.{C.RESET}")
            else:
                print(f"{C.DIM}    [-] CDX serveren returnerede ingen data.{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [-] Fejl ved CDX opslag: {e}{C.RESET}")

    def _force_new_snapshot(self):
        """NY V8: Sender et gem-kald for at sikre bevismateriale nu og her"""
        print(f"\n{C.YELLOW}[*] Udfører Auto-Preservation: Tvinger Wayback Machine til at tage et friskt snapshot NU...{C.RESET}")
        try:
            save_url = f"https://web.archive.org/save/{self.url}"
            res = requests.get(save_url, timeout=10)
            if res.status_code == 200:
                print(f"{C.GREEN}    ✓ SUCCESS: Friskt snapshot af URL'en er nu sat i kø hos Internet Archive!{C.RESET}")
            else:
                print(f"{C.DIM}    [-] Kunne ikke tvinge snapshot (Siden blokerer måske crawlere).{C.RESET}")
        except Exception:
            print(f"{C.DIM}    [-] Auto-Preservation timeout. Archive.org er muligvis overbelastet.{C.RESET}")

    def _download_archive(self, archive_url):
        print(f"{C.YELLOW}    [*] Downloader offline kopi til bevissikring...{C.RESET}")
        try:
            # Wayback machine tilføjer "id_" til URL'en for at give dig den RÅ originale HTML uden deres top-bar
            raw_url = archive_url.replace("/web/", "/web/id_/", 1)
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            page_data = requests.get(raw_url, headers=headers, timeout=20).text
            
            mappe = os.path.join(session["loot_folder"], "wayback_archives")
            os.makedirs(mappe, exist_ok=True)
            
            safe_name = self.url.replace("https://", "").replace("http://", "").replace("/", "_")
            filsti = os.path.join(mappe, f"OFFLINE_{safe_name}.html")
            
            with open(filsti, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(page_data)
                
            print(f"{C.GREEN}    ✓ Komplet webside sikret offline: {filsti}{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [-] Kunne ikke downloade rå HTML: {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        safe_url = self.url.replace("https://", "").replace("http://", "").replace("/", "_")
        filename = f"{session['loot_folder']}/25_WAYBACK_{safe_url}.json"
        
        # NY V8: Sikker overskrivning af fil
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"\n{C.GREEN}[✓] Wayback Intelligence Rapport gemt: {filename}{C.RESET}")