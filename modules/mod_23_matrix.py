# -*- coding: utf-8 -*-
import os
import json
import subprocess
import requests # NY V8 TILFØJELSE: Til Pre-Flight og Wayback opslag
import concurrent.futures # NY V8 TILFØJELSE: Til multi-threaded hurtigsøgning
from datetime import datetime
from pathlib import Path
from core.utils import C, session

# NY V8 FIX: Klassen er omdøbt til MatrixAnalyzer for at matche Modul 02's Pivot Engine!
class MatrixAnalyzer:
    def __init__(self, username):
        # Tillader dict-input hvis Pivot Engine sender hele data-objektet
        if isinstance(username, dict):
            # Extract navnet klogest muligt (hvis kaldt fra auto-pivot)
            self.username = username.get("Samlet_Pivot_Data", {}).get("Social_Media", {}).get("Brugernavn", "")
            if not self.username:
                self.username = "Unknown"
        else:
            self.username = str(username).strip()
            
        self.data = {
            "Brugernavn": self.username, 
            "High_Value_Hits": [],      # NY V8 TILFØJELSE: Pre-flight fund
            "Platforme": [], 
            "Arkiverede_Profiler": [],  # NY V8 TILFØJELSE: Wayback Machine links
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[23] Global Username Matrix (GOLIATH V8 Engine)\n{'='*60}{C.RESET}")
        
        if self.username == "Unknown":
            print(f"{C.RED}[!] Kunne ikke udtrække et gyldigt brugernavn at søge på.{C.RESET}")
            return

        # --- NY V8 TILFØJELSE: High-Speed Pre-Flight Scan ---
        self._quick_fire_scan()

        print(f"\n{C.YELLOW}[*] Starter fuld skanning over 300+ platforme for: {self.username} (Tillad op til 2 minutter)...{C.RESET}")
        
        try:
            # Vi øger timeout let, men fanger fejl bedre (Original kode bevaret 100%)
            process = subprocess.Popen(
                ['sherlock', self.username, '--timeout', '5', '--print-found'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Læser output live!
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if "[+]" in line:
                    site_url = line.split("[+]")[1].strip()
                    try:
                        platform_name = site_url.split("://")[1].split("/")[0]
                    except Exception:
                        platform_name = "UKENDT PLATFORM"
                    
                    print(f"{C.GREEN}    🔥 {platform_name.upper()}: {C.CYAN}{site_url}{C.RESET}")
                    
                    if site_url not in self.data["Platforme"]:
                        self.data["Platforme"].append(site_url)

            process.wait()
            
            if not self.data["Platforme"] and not self.data.get("High_Value_Hits"):
                print(f"{C.YELLOW}    [-] Ingen profiler fundet (eller Sherlock er ikke installeret korrekt).{C.RESET}")
                
        except FileNotFoundError:
            print(f"{C.RED}    [!] 'sherlock' er ikke installeret globalt. Kør: pip install sherlock-project{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl under Matrix skanning: {e}{C.RESET}")

        # --- NY V8 TILFØJELSE: Wayback Machine Archiver ---
        if self.data["Platforme"] or self.data.get("High_Value_Hits"):
            self._check_wayback_archives()

        self.save()

    def _quick_fire_scan(self):
        """NY V8 TILFØJELSE: Lynhurtig API Ghost-check på Top Tier OSINT mål udenom Sherlock"""
        print(f"{C.YELLOW}[*] Udfører lynhurtig Pre-Flight skanning mod Top Tier mål...{C.RESET}")
        
        targets = {
            "GitHub": f"https://github.com/{self.username}",
            "Reddit": f"https://www.reddit.com/user/{self.username}/about.json",
            "Pastebin": f"https://pastebin.com/u/{self.username}",
            "Linktree": f"https://linktr.ee/{self.username}",
            "Steam": f"https://steamcommunity.com/id/{self.username}"
        }
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        def check_url(name, url):
            try:
                res = requests.get(url, headers=headers, timeout=5)
                # Reddit kræver JSON 'name' tjek
                if name == "Reddit" and res.status_code == 200 and "name" in res.text:
                    return name, f"https://www.reddit.com/user/{self.username}"
                # Andre platforme returnerer bare 200 OK
                elif name != "Reddit" and res.status_code == 200:
                    # Sikrer at vi ikke rammer en generic redirect
                    if "Page Not Found" not in res.text and "404" not in res.text:
                        return name, url
            except Exception: pass
            return None, None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_url, name, url) for name, url in targets.items()]
            for future in concurrent.futures.as_completed(futures):
                name, url = future.result()
                if name and url:
                    print(f"{C.RED}    ⚡ PRE-FLIGHT HIT: Profil bekræftet på {name} ({url}){C.RESET}")
                    self.data["High_Value_Hits"].append(url)
                    # Sørger for at den også ligger i standard-listen for Wayback Machine opslaget
                    if url not in self.data["Platforme"]:
                        self.data["Platforme"].append(url)

    def _check_wayback_archives(self):
        """NY V8 TILFØJELSE: Tjekker om de fundne profiler har historiske (slettede) snapshots"""
        print(f"\n{C.YELLOW}[*] Søger i Wayback Machine efter slettede/historiske versioner af profilerne...{C.RESET}")
        
        # Vi tager max 5 URL'er for ikke at rate-limite Wayback Machine
        urls_to_check = self.data.get("High_Value_Hits", []) + self.data["Platforme"]
        unique_urls = list(set(urls_to_check))[:5]
        
        for url in unique_urls:
            wb_api = f"http://archive.org/wayback/available?url={url}"
            try:
                res = requests.get(wb_api, timeout=5).json()
                if res.get("archived_snapshots", {}).get("closest"):
                    snap_url = res["archived_snapshots"]["closest"]["url"]
                    print(f"{C.MAGENTA}    🔥 HISTORISK SNAPSHOT FUNDET: {snap_url}{C.RESET}")
                    self.data["Arkiverede_Profiler"].append({
                        "Original_URL": url,
                        "Archive_URL": snap_url
                    })
            except Exception:
                pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/23_MATRIX_{self.username}.json"
        
        # NY V8 TILFØJELSE: Sikker overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        total_hits = len(self.data['Platforme'])
        print(f"\n{C.GREEN}[✓] Matrix rapport gemt ({total_hits} hits): {filename}{C.RESET}")

# Alias for backwards compatibility, hvis et af dine ældre scripts bruger det gamle navn
UsernameMatrixAnalyzer = MatrixAnalyzer