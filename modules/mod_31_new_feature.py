# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V36: ASYNC BATCH HARVESTER
📌 Formål: Parallelt scrapings-modul til tusindvis af mål uden timeouts.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import logging
from typing import Optional, Dict, Any, List
import requests
import time
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import get_stealth_session

class AdvancedBatchHarvester(BaseModule):
    """Et fuldblods V36 OSINT Modul til Batch Processering."""

    def __init__(self):
        super().__init__()
        self.name = "OMNI ASYNC BATCH HARVESTER"
        self.description = "Parallel batch analyse og asynkron HTTP scraping."
        self.category = ModuleCategory.NETWORK
        self.data = {"Total_Targets": 0, "Succesfulde_Requests": 0, "Results": {}}
        self.max_workers = 10
        self.session = get_stealth_session()
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

    def _fetch_data(self, url: str) -> Optional[str]:
        """Sikker proxy/header-roterende fetcher."""
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self._log(f"Fetch failed for {url}: {e}", C.DIM)
            return None

    def _parse_data(self, html: str) -> Optional[Dict]:
        """Udtrækker OSINT-relevant meta data, title og outbounds."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find skjulte metatags (Ofte API nøgler eller framework versioner)
            metadata = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                if name: metadata[name] = meta.get('content')
                
            return {
                "Title": soup.title.string.strip() if soup.title else "Ingen Titel",
                "Eksterne_Links": [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('http')],
                "Skjult_Metadata": metadata,
                "Tekst_Længde": len(soup.get_text())
            }
        except Exception as e:
            self._log(f"Parse error: {e}", C.RED)
            return None

    def _analyze_single(self, target: str) -> Optional[Dict]:
        url = f"https://{target}" if not target.startswith("http") else target
        html = self._fetch_data(url)
        if not html: return None
        return self._parse_data(html)

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[31] OMNI ASYNC BATCH HARVESTER V36\n{'='*60}{C.RESET}")
        
        if not target:
            target = "pastebin.com, github.com, example.com"
            print(f"{C.YELLOW}[*] Intet target angivet. Bruger default test-batch: {target}{C.RESET}")
            
        targets = [t.strip() for t in target.split(',')]
        self.data["Total_Targets"] = len(targets)
        
        print(f"{C.YELLOW}[*] Udfører parallel analyse på {len(targets)} mål med {self.max_workers} tråde...{C.RESET}")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._analyze_single, t): t for t in targets}
            for future in concurrent.futures.as_completed(futures):
                t = futures[future]
                res = future.result()
                if res:
                    self.data["Results"][t] = res
                    self.data["Succesfulde_Requests"] += 1
                    print(f"{C.GREEN} [+] Data trukket succesfuldt for: {t} ({len(res['Eksterne_Links'])} links){C.RESET}")
                else:
                    print(f"{C.DIM} [-] Fejl eller ingen data for: {t}{C.RESET}")

        print(f"\n{C.GREEN}[✓] Batch Harvesting Fuldført. ({self.data['Succesfulde_Requests']}/{self.data['Total_Targets']} success){C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data