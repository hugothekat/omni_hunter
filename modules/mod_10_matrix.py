# -*- coding: utf-8 -*-
import os
import json
import subprocess
import requests 
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session

# NY V8 FIX: Klassen er omdøbt til MatrixAnalyzer for at matche Modul 02's Pivot Engine!
class MatrixAnalyzer(BaseModule):
    def __init__(self, username=""):
        super().__init__()
        self.name = "USERNAME MATRIX"
        self.description = "Global profil-detektion via asynkront ghost-check og Sherlock."
        self.category = ModuleCategory.SOCIAL
        
        self.username = str(username).strip()
            
        self.data = {
            "Brugernavn": self.username, 
            "High_Value_Hits": [],      # NY V8 TILFØJELSE: Pre-flight fund
            "Platforme": [], 
            "Arkiverede_Profiler": [],  # NY V8 TILFØJELSE: Wayback Machine links
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver=None, target=""):
        print(f"\n{C.CYAN}{'='*60}\n[23] Global Username Matrix (GOLIATH V8 Engine)\n{'='*60}{C.RESET}")
        
        # Prioriterer target fra run-kommandoen, da det er den mest direkte instruks fra operatøren.
        run_target = target or self.username
        if isinstance(run_target, dict):
            self.username = run_target.get("Brugernavn") or \
                            run_target.get("Samlet_Pivot_Data", {}).get("Social_Media", {}).get("Brugernavn", "Unknown")
        else:
            self.username = str(run_target).strip()
        
        self.data['Brugernavn'] = self.username

        if not self.username or self.username == "Unknown":
            print(f"{C.RED}[!] Kunne ikke udtrække et gyldigt brugernavn at søge på.{C.RESET}")
            return self.data

        # --- NY V8 TILFØJELSE: High-Speed Pre-Flight Scan ---
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(self._run_async_preflight())
            else:
                loop.create_task(self._run_async_preflight())
        except Exception as e: print(f"{C.RED}[!] Async Pre-Flight Fejl: {e}{C.RESET}")

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

        self.save_loot(self.username)

    async def _check_url_async(self, name, url, session_http):
        try:
            async with session_http.get(url, timeout=10) as res:
                text = await res.text()
                status = res.status
        except Exception:
            return None, None
            
        # GOLIATH V45: Asynkron Cloudflare / Turnstile Bypass via Playwright
        if status in [403, 503] and any(cf in text.lower() for cf in ["cloudflare", "turnstile", "just a moment"]):
            print(f"{C.YELLOW}    [*] WAF Detekteret på {name}. Kører Async Playwright Bypass...{C.RESET}")
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    page = await context.new_page()
                    await page.goto(url, timeout=15000)
                    await page.wait_for_load_state("networkidle")
                    text = await page.content()
                    status = 200
                    await browser.close()
            except Exception:
                return None, None

        if name == "Reddit" and status == 200 and "name" in text:
            return name, f"https://www.reddit.com/user/{self.username}"
        elif name != "Reddit" and status == 200:
            if "Page Not Found" not in text and "404" not in text:
                return name, url
        return None, None

    async def _run_async_preflight(self):
        """NY V45 TILFØJELSE: Lynhurtig Async Pre-Flight med integreret WAF Bypass"""
        print(f"{C.YELLOW}[*] Udfører lynhurtig asynkron Pre-Flight skanning mod Top Tier mål...{C.RESET}")
        
        targets = {
            "GitHub": f"https://github.com/{self.username}",
            "Reddit": f"https://www.reddit.com/user/{self.username}/about.json",
            "Pastebin": f"https://pastebin.com/u/{self.username}",
            "Linktree": f"https://linktr.ee/{self.username}",
            "Steam": f"https://steamcommunity.com/id/{self.username}"
        }
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with aiohttp.ClientSession(headers=headers) as session_http:
            tasks = [self._check_url_async(name, url, session_http) for name, url in targets.items()]
            results = await asyncio.gather(*tasks)
            
            for name, url in results:
                if name and url:
                    print(f"{C.RED}    ⚡ PRE-FLIGHT HIT: Profil bekræftet på {name} ({url}){C.RESET}")
                    self.data["High_Value_Hits"].append(url)
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

# Alias for backwards compatibility, hvis et af dine ældre scripts bruger det gamle navn
UsernameMatrixAnalyzer = MatrixAnalyzer