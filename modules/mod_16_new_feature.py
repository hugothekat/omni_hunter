# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V48: ASYNC BATCH HARVESTER
📌 Formål: Massivt skalerbar, asynkron scraping med WAF-evasion.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import logging
from typing import Tuple
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
import time
import random
from bs4 import BeautifulSoup

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import get_async_stealth_session, AsyncProxyManager

class AdvancedBatchHarvester(BaseModule):
    """GOLIATH V48: Asynkron Batch Harvester med proxy-rotation og header-spoofing."""

    def __init__(self):
        super().__init__()
        self.name = "OMNI ASYNC BATCH HARVESTER"
        self.description = "Parallel batch analyse og asynkron HTTP scraping."
        self.category = ModuleCategory.NETWORK
        self.data = {"Total_Targets": 0, "Succesfulde_Requests": 0, "Results": {}}
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

    async def _fetch_data(self, session: aiohttp.ClientSession, proxy_mgr: AsyncProxyManager, url: str) -> Optional[str]:
        """Sikker proxy/header-roterende asynkron fetcher med WAF-evasion."""
        try:
            proxy = await proxy_mgr.get_proxy()
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            }
            async with session.get(url, headers=headers, proxy=proxy, timeout=15) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            self._log(f"Fetch failed for {url}: {e}", C.DIM)
            return None

    def _parse_data(self, html: str) -> Optional[Dict]:
        """Udtrækker OSINT-relevant meta data, title og outbounds."""
        except Exception as e:
            self._log(f"Parse error: {e}", C.RED)
            return None

    async def _analyze_single(self, session: aiohttp.ClientSession, proxy_mgr: AsyncProxyManager, target: str) -> Tuple[str, Optional[Dict]]:
        url = f"https://{target}" if not target.startswith("http") else target
        html = await self._fetch_data(session, proxy_mgr, url)
        if not html: return target, None
        return target, self._parse_data(html)
        
    async def _run_batch(self, targets: List[str]):
        proxy_mgr = AsyncProxyManager()
        async with await get_async_stealth_session(proxy_mgr) as session:
            tasks = [self._analyze_single(session, proxy_mgr, t) for t in targets]
            results = await asyncio.gather(*tasks)
            
            for t, res in results:
                if res:
                    self.data["Results"][t] = res
                    self.data["Succesfulde_Requests"] += 1
                    print(f"{C.GREEN} [+] Data trukket succesfuldt for: {t} ({len(res['Eksterne_Links'])} links){C.RESET}")
                else:
                    print(f"{C.DIM} [-] Fejl eller ingen data for: {t}{C.RESET}")

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[31] OMNI ASYNC BATCH HARVESTER V48\n{'='*60}{C.RESET}")
        
        if not target:
            target = "pastebin.com, github.com, example.com"
            print(f"{C.YELLOW}[*] Intet target angivet. Bruger default test-batch: {target}{C.RESET}")
            
        targets = [t.strip() for t in target.split(',')]
        self.data["Total_Targets"] = len(targets)
        
        print(f"{C.YELLOW}[*] Udfører parallel asynkron analyse på {len(targets)} mål...{C.RESET}")
        
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop.run_until_complete(self._run_batch(targets))
        else:
            loop.create_task(self._run_batch(targets))

        print(f"\n{C.GREEN}[✓] Batch Harvesting Fuldført. ({self.data['Succesfulde_Requests']}/{self.data['Total_Targets']} success){C.RESET}")
        datalake.ingest(self.name, target, self.data)

