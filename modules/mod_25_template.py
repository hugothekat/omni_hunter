# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V49: SPA API INTERCEPTOR & REPLAY ENGINE
📌 Formål: Reverse-engineering af SPA-sider. Opsnapper netværkstrafik via Playwright,
udtrækker skjulte REST-endpoints og Bearer tokens, og mass-scraper backenden.
"""
import sys
import os
import json
import glob
from pathlib import Path
import re
sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncio
import aiohttp
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake, sanitize_filename
from core.browser import OmniHunterBrowser, BrowserConfig
from core.network import AsyncProxyManager, get_async_stealth_session

class SPAInterceptorEngine(BaseModule):
    """GOLIATH V49: LEO SPA Reverse Engineer."""
    
    def __init__(self):
        super().__init__()
        self.name = "SPA API INTERCEPTOR & REPLAY ENGINE"
        self.description = "Bypasser WAF og scraper skjulte SPA JSON-endpoints asynkront."
        self.category = ModuleCategory.NETWORK
        
        self.data = {
            "Target": "",
            "Intercepted_APIs": [],
            "Extracted_Bearer_Tokens": set(),
            "Mass_Scrape_Results": [],
            "Timestamp": datetime.now().isoformat()
        }

    async def _async_replay_attacks(self, endpoints: List[str], tokens: List[str]):
        """Roterer proxies og asynkront suger data fra backenden udenom frontend-DOM'en."""
        proxy_manager = AsyncProxyManager()
        async with await get_async_stealth_session(proxy_manager) as http_session:
            tasks = []
            for endpoint in endpoints:
                # Hvis vi har fundet et token, bruger vi det i headeren
                token = tokens[0] if tokens else ""
                tasks.append(self._fetch_endpoint(http_session, endpoint, proxy_manager, token))
            
            results = await asyncio.gather(*tasks)
            for res in results:
                if res: self.data["Mass_Scrape_Results"].append(res)

    async def _fetch_endpoint(self, session_http: aiohttp.ClientSession, url: str, proxy_mgr: AsyncProxyManager, token: str):
        proxy = await proxy_mgr.get_proxy()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            async with session_http.get(url, proxy=proxy, headers=headers, timeout=10) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"{C.GREEN}    🔥 REPLAY SUCCESS: Sugede data direkte fra {url[:60]}...{C.RESET}")
                        return {"url": url, "payload": data}
                    except Exception: pass
        except Exception: pass
        return None

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[25] SPA API INTERCEPTOR & REPLAY ENGINE V49\n{'='*60}{C.RESET}")
        self.target = target.strip() if target else "https://example.com"
        
        # GOLIATH AUTO-HEAL: Retter slåfejl som 'httpswww.' eller manglende skema
        self.target = re.sub(r'^(https?://)?https?www\.', 'https://www.', self.target)
        self.target = re.sub(r'^(https?://)+', 'https://', self.target)
        if not self.target.startswith("http"): 
            self.target = f"https://{self.target}"
            
        self.data["Target"] = self.target
        
        print(f"{C.YELLOW}[*] Initierer passiv netværks-interception via Playwright mod: {self.target}...{C.RESET}")
        
        loot_dir = session.get("loot_folder", "loot_evidence")
        capture_dir = os.path.join(loot_dir, "network_captures")
        
        config = BrowserConfig(
            headless=True, browser_type="chromium", anti_detection=True, 
            js_rendering=True, network_capture=True, network_capture_dir=capture_dir
        )
        
        hunter = OmniHunterBrowser(config)
        hunter.start()
        try:
            res = hunter.fetch(self.target)
            captured_files = res.get("captured_files", [])
            
            print(f"{C.YELLOW}[*] Analyserer {len(captured_files)} opsnappede API-kald for backend-endpoints...{C.RESET}")
            
            endpoints_to_replay = []
            for file in captured_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        c_data = json.load(f)
                        api_url = c_data.get("url", "")
                        if "/api/" in api_url or "graphql" in api_url or ".json" in api_url:
                            if api_url not in endpoints_to_replay:
                                endpoints_to_replay.append(api_url)
                                self.data["Intercepted_APIs"].append({"endpoint": api_url, "method": "GET"})
                                print(f"{C.MAGENTA}    -> Opsnappet Endpoint: {api_url}{C.RESET}")
                except Exception: pass
                
            if endpoints_to_replay:
                print(f"\n{C.YELLOW}[*] Initierer Asynkront API Replay-Attack udenom Frontend DOM'en...{C.RESET}")
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                    
                if loop and loop.is_running():
                    loop.create_task(self._async_replay_attacks(endpoints_to_replay[:15], list(self.data["Extracted_Bearer_Tokens"])))
                else:
                    asyncio.run(self._async_replay_attacks(endpoints_to_replay[:15], list(self.data["Extracted_Bearer_Tokens"])))
        except Exception as e:
            print(f"{C.RED}[!] Interception fejl: {e}{C.RESET}")
        finally:
            hunter.close()
        
        self.data["Extracted_Bearer_Tokens"] = list(self.data["Extracted_Bearer_Tokens"])
        datalake.ingest(self.name, self.target, self.data)
        
        print(f"\n{C.GREEN}[✓] SPA Reverse Engineering fuldført!{C.RESET}")
        return self.data
        
# Beholder gammelt referencenavn midlertidigt for kompatibilitet
AdvancedCyberOperation = SPAInterceptorEngine