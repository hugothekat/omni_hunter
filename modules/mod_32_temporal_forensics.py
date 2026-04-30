# -*- coding: utf-8 -*-
import sys
import asyncio
import aiohttp
import json
import difflib
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any, List

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake, logger

class TemporalForensicsEngine(BaseModule):
    """
    GOLIATH V36: Change-Fingerprint, Social Handle Recovery & Snapshot Quality Index.
    Identificerer slettet indhold og profiler via historisk HTML-diffing på Archive.org.
    """
    def __init__(self):
        super().__init__()
        self.name = "TEMPORAL FORENSICS ENGINE"
        self.description = "Dybdegående historisk diffing, snapshot kvalitet og alias-recovery."
        self.category = ModuleCategory.FORENSICS
        self.data = {
            "Target": "",
            "Total_Snapshots": 0,
            "Top_Quality_Snapshots": [],
            "Change_Fingerprint": {"Added_Content": [], "Removed_Content": []},
            "Recovered_Social_Profiles": {"Old_Profiles": [], "Current_Profiles": []},
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[32] TEMPORAL FORENSICS (WAYBACK DIFFING V36)\n{'='*60}{C.RESET}")
        self.data["Target"] = target
        
        domain = target.replace("http://", "").replace("https://", "").split("/")[0]
        
        # Kør Asynkron Event Loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self._async_run(domain))
        else:
            loop.run_until_complete(self._async_run(domain))
            
        return self.data

    async def _async_run(self, domain: str):
        print(f"{C.YELLOW}[*] Henter Wayback CDX Tidslinje for {domain}...{C.RESET}")
        snapshots = await self._fetch_cdx_timeline(domain)
        self.data["Total_Snapshots"] = len(snapshots)
        
        if len(snapshots) < 2:
            print(f"{C.RED}[!] Ikke nok snapshots til at udføre diffing. Finder {len(snapshots)}.{C.RESET}")
            datalake.ingest(self.name, domain, self.data)
            return

        print(f"{C.YELLOW}[*] Udregner Snapshot Quality Index for {len(snapshots)} punkter...{C.RESET}")
        scored_snaps = await self._score_snapshots(snapshots)
        self.data["Top_Quality_Snapshots"] = [s['url'] for s in scored_snaps[:5]]
        
        # Udvælg ældste højkvalitets og nyeste højkvalitets
        scored_snaps.sort(key=lambda x: x['timestamp'])
        oldest = scored_snaps[0]
        newest = scored_snaps[-1]
        
        print(f"{C.CYAN}[*] Sammenligner:\n    Ældste: {oldest['url']}\n    Nyeste: {newest['url']}{C.RESET}")
        await self._diff_snapshots(oldest['html'], newest['html'])
        
        print(f"\n{C.GREEN}[✓] Temporal Forensics fuldført.{C.RESET}")
        self._print_summary()
        datalake.ingest(self.name, domain, self.data)

    async def _fetch_cdx_timeline(self, domain: str) -> List[Dict]:
        url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&fl=timestamp,original,statuscode&filter=statuscode:200&limit=50"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as res:
                    if res.status == 200:
                        data = await res.json()
                        if len(data) > 1:
                            return [{"timestamp": r[0], "url": f"http://web.archive.org/web/{r[0]}id_/{r[1]}"} for r in data[1:]]
            except Exception as e:
                logger.error(f"CDX Fetch Fejl: {e}")
        return []

    async def _score_snapshots(self, snapshots: List[Dict]) -> List[Dict]:
        """Quality Index Heuristic: Straffer tomme sider, belønner rigt DOM-indhold."""
        scored = []
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_and_score(session, snap) for snap in snapshots[:20]] # Max 20 for performance
            results = await asyncio.gather(*tasks)
            for res in results:
                if res and res['score'] > 10: scored.append(res)
        
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored

    async def _fetch_and_score(self, session: aiohttp.ClientSession, snap: Dict) -> Dict:
        try:
            async with session.get(snap['url'], timeout=10) as res:
                html = await res.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Heuristik for kvalitet
                text_len = len(soup.get_text())
                img_count = len(soup.find_all('img'))
                script_count = len(soup.find_all('script'))
                score = (text_len / 100) + (img_count * 2) + (script_count * 1)
                
                # Straffer redirects eller paywalls
                if "301 Moved" in html or "Captcha" in html: score -= 500
                
                return {"timestamp": snap['timestamp'], "url": snap['url'], "html": html, "score": score, "soup": soup}
        except: return None

    async def _diff_snapshots(self, html_old: str, html_new: str):
        """Change-Fingerprint Engine & Social Recovery"""
        soup_old = BeautifulSoup(html_old, 'html.parser')
        soup_new = BeautifulSoup(html_new, 'html.parser')
        
        # 1. Social Handle Recovery
        social_regex = re.compile(r'(facebook\.com|twitter\.com|instagram\.com|linkedin\.com|t\.me)/([a-zA-Z0-9_\-\.]+)')
        old_socials = set([a['href'] for a in soup_old.find_all('a', href=True) if social_regex.search(a['href'])])
        new_socials = set([a['href'] for a in soup_new.find_all('a', href=True) if social_regex.search(a['href'])])
        
        self.data["Recovered_Social_Profiles"]["Current_Profiles"] = list(new_socials)
        self.data["Recovered_Social_Profiles"]["Old_Profiles"] = list(old_socials - new_socials)
        
        # 2. Text Diffing
        text_old = soup_old.get_text(separator='\n').splitlines()
        text_new = soup_new.get_text(separator='\n').splitlines()
        
        # Rens tomme linjer
        text_old = [t.strip() for t in text_old if len(t.strip()) > 10]
        text_new = [t.strip() for t in text_new if len(t.strip()) > 10]
        
        differ = difflib.SequenceMatcher(None, text_old, text_new)
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'delete':
                for line in text_old[i1:i2]:
                    # Check om der blev slettet CPR, Telefon eller Navne
                    if re.search(r'\d', line): 
                        self.data["Change_Fingerprint"]["Removed_Content"].append(line)
            elif tag == 'insert':
                for line in text_new[j1:j2]:
                    if re.search(r'(hacked|malware|casino|viagra)', line, re.IGNORECASE):
                        self.data["Change_Fingerprint"]["Added_Content"].append(f"[MALWARE/SEO SUSPECT] {line}")

    def _print_summary(self):
        print(f"\n{C.MAGENTA}[!] Tactical Temporal Summary:{C.RESET}")
        old_soc = self.data["Recovered_Social_Profiles"]["Old_Profiles"]
        if old_soc:
            print(f"{C.RED}    🔥 Slettede Sociale Aliaser (Recovery):{C.RESET}")
            for s in old_soc[:5]: print(f"       -> {s}")
            
        removed = self.data["Change_Fingerprint"]["Removed_Content"]
        if removed:
            print(f"{C.YELLOW}    🔥 Sensitivt Indhold Fjernet/Scrubbed over tid:{C.RESET}")
            for r in list(set(removed))[:5]: print(f"       -> {r[:80]}...")