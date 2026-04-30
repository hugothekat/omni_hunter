# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V36: PASTEBIN DE-HASH INTELLIGENCE
📌 Formål: Asynkron scraping af Pastebin for lækkede passwords og real-time de-hashing.
"""
import sys
import os
import json
import re
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake, session
from core.config_vault import vault
from core.network import AsyncProxyManager, get_async_stealth_session, omni_dork_search

class PastebinDehashIntelligence(BaseModule):
    """
    GOLIATH V36: PASTEBIN DE-HASHER
    Støvsuger Pastebin, udtager credentials/hashes, og auto-knækker MD5/SHA via API.
    """
    def __init__(self):
        super().__init__()
        self.name = "PASTEBIN DE-HASH INTELLIGENCE"
        self.description = "Automatiseret asynkron Pastebin lækage-scraper og hash-knækker."
        self.category = ModuleCategory.FORENSICS
        
        # Trækker nøgler sikkert fra The Vault
        self.pastebin_api_key = vault.get("api_keys", "pastebin_api_key") if vault else None
        
        self.data = {
            "Target": "",
            "Analyserede_Pastes": 0,
            "Fundne_Emails": [],
            "Hashes_Udtrækket": {"MD5": [], "SHA1": [], "Bcrypt": []},
            "Knækkede_Passwords_Klartekst": [],
            "Rå_Kredentialer": [],
            "Timestamp": datetime.now().isoformat()
        }
        
        self.uncracked_hashes = set()
        self.hash_patterns = {
            "MD5": re.compile(r'\b[A-Fa-f0-9]{32}\b'),
            "SHA1": re.compile(r'\b[A-Fa-f0-9]{40}\b'),
            "Bcrypt": re.compile(r'\$2[ayb]\$[0-9]{2}\$[A-Za-z0-9\.\/]{53}')
        }
        self.email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        self.cred_pattern = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+):([^\s]{6,32})')

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[36] PASTEBIN LEAK & DE-HASH ENGINE V36\n{'='*60}{C.RESET}")
        self.data["Target"] = target or session.get("name", "Unknown")
        
        if not target and not driver:
            print(f"{C.RED}[!] Kræver et target (domæne, email eller firma) eller driver til dorking.{C.RESET}")
            return self.data

        urls_to_scrape = self._find_pastes_via_dork(driver, self.data["Target"])
        
        if not urls_to_scrape:
            print(f"{C.YELLOW}[*] Ingen umiddelbare pastes fundet. Mission afbrudt.{C.RESET}")
            return self.data

        print(f"{C.YELLOW}[*] Starter Asynkron Extraction Matrix på {len(urls_to_scrape)} pastes...{C.RESET}")
        
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(self._async_scrape_and_dehash(urls_to_scrape))
        except Exception as e:
            print(f"{C.RED}[!] Asynkron Fejl: {e}{C.RESET}")

        self._print_summary()
        self._save_report()
        return self.data

    def _find_pastes_via_dork(self, driver, target: str) -> List[str]:
        """Bruger OmniDork til at finde RAW paste-links for målet."""
        print(f"{C.YELLOW}[*] Opsporer lækager for '{target}' via Stealth Dorking...{C.RESET}")
        dork = f'site:pastebin.com/raw OR site:paste.ee OR site:ghostbin.co "{target}"'
        
        urls = []
        if driver:
            hits = omni_dork_search(driver, dork, max_links=10)
            for hit in hits:
                # Konverterer standard Pastebin URL'er til RAW format
                url = hit['url']
                if "pastebin.com" in url and "/raw/" not in url:
                    url = url.replace("pastebin.com/", "pastebin.com/raw/")
                urls.append(url)
                print(f"{C.GREEN}    🔥 HIT: {url}{C.RESET}")
        return urls

    async def _async_scrape_and_dehash(self, urls: List[str]):
        proxy_manager = AsyncProxyManager()
        
        async with await get_async_stealth_session(proxy_manager) as http_session:
            # 1. Scrape pastes asynkront
            scrape_tasks = [self._fetch_paste(http_session, url, proxy_manager) for url in urls]
            results = await asyncio.gather(*scrape_tasks)
            
            all_hashes = set()
            
            for res in results:
                if not res: continue
                self.data["Analyserede_Pastes"] += 1
                
                # Udtræk emails
                for email in self.email_pattern.findall(res):
                    if email not in self.data["Fundne_Emails"]:
                        self.data["Fundne_Emails"].append(email.lower())
                
                # Udtræk Klartekst Credentials (email:password format)
                for cred in self.cred_pattern.findall(res):
                    pwd = cred[1]
                    # Filtrerer falske positiver der oftest fanges af regex (ex: md5 hashes)
                    if len(pwd) != 32 and pwd not in self.data["Rå_Kredentialer"]:
                        self.data["Rå_Kredentialer"].append(f"{cred[0]}:{pwd}")
                        print(f"{C.RED}      💀 Klartekst Credential Ekstraheret: {cred[0]}:{pwd[:3]}***{C.RESET}")

                # Udtræk Hashes
                for h_type, pattern in self.hash_patterns.items():
                    found = pattern.findall(res)
                    for h in found:
                        if h not in self.data["Hashes_Udtrækket"][h_type]:
                            self.data["Hashes_Udtrækket"][h_type].append(h)
                            if h_type == "MD5": all_hashes.add(h)
                            
            # 2. De-Hash MD5 parallelt
            if all_hashes:
                print(f"\n{C.YELLOW}[*] Kører Parallel Auto-Dehashing på {len(all_hashes)} MD5 hashes...{C.RESET}")
                dehash_tasks = [self._dehash_md5(http_session, h) for h in all_hashes]
                await asyncio.gather(*dehash_tasks)
                
            if self.uncracked_hashes:
                await self._run_local_hashcat()

    async def _fetch_paste(self, session: aiohttp.ClientSession, url: str, proxy_mgr: AsyncProxyManager) -> Optional[str]:
        proxy = await proxy_mgr.get_proxy()
        try:
            async with session.get(url, proxy=proxy) as response:
                if response.status == 200:
                    return await response.text()
        except Exception: pass
        return None

    async def _dehash_md5(self, session: aiohttp.ClientSession, hash_val: str):
        """Smasher hashen mod gratis De-Hashing databaser (Nitrxgen)."""
        try:
            # Nitrxgen har en massiv MD5 database der ikke kræver Auth
            url = f"https://nitrxgen.net/md5db/{hash_val}"
            async with session.get(url) as response:
                if response.status == 200:
                    cracked = await response.text()
                    if cracked:
                        entry = {"Hash": hash_val, "Cleartext": cracked.strip()}
                        self.data["Knækkede_Passwords_Klartekst"].append(entry)
                        print(f"{C.GREEN}      💥 CRACKED: {hash_val} -> {cracked.strip()}{C.RESET}")
                        return
        except Exception: pass
        
        # Hvis API fejler eller hashen ikke findes, send til lokal Hashcat
        self.uncracked_hashes.add(hash_val)

    async def _run_local_hashcat(self):
        """GOLIATH V36: Lokal Hardware Acceleration (Hashcat) for genstridige hashes."""
        print(f"\n{C.YELLOW}[*] API De-Hash missede {len(self.uncracked_hashes)} hashes. Vækker lokal Hashcat...{C.RESET}")
        import tempfile
        import subprocess
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
                for h in self.uncracked_hashes: f.write(f"{h}\n")
                tmp_name = f.name
            
            # Standard Dictionary Attack (eller lynhurtig mask attack som fallback)
            wordlist = "/usr/share/wordlists/rockyou.txt"
            cmd = ["hashcat", "-m", "0", "-a", "0", tmp_name, wordlist, "--quiet", "--potfile-disable"]
            if not os.path.exists(wordlist):
                cmd = ["hashcat", "-m", "0", "-a", "3", tmp_name, "?l?l?l?l?l?l?d?d", "--quiet", "--potfile-disable"]

            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            
            for line in stdout.decode().splitlines():
                if ":" in line:
                    h, p = line.split(":", 1)
                    if len(h) == 32:
                        self.data["Knækkede_Passwords_Klartekst"].append({"Hash": h, "Cleartext": p.strip(), "Source": "Hashcat_Local"})
                        print(f"{C.RED}      🔥 HASHCAT CRACKED: {h} -> {p.strip()}{C.RESET}")
            os.unlink(tmp_name)
        except Exception as e:
            print(f"{C.DIM}      [-] Lokal Hashcat-eksekvering fejlede: {e}{C.RESET}")

    def _print_summary(self):
        print(f"\n{C.CYAN}--- PASTEBIN TACTICAL SUMMARY ---{C.RESET}")
        print(f"Pastes Analyseret: {C.WHITE}{self.data['Analyserede_Pastes']}{C.RESET}")
        print(f"Lækkede Emails:    {C.WHITE}{len(self.data['Fundne_Emails'])}{C.RESET}")
        print(f"Klartekst Creds:   {C.RED}{len(self.data['Rå_Kredentialer'])}{C.RESET}")
        
        tot_hashes = sum(len(v) for v in self.data['Hashes_Udtrækket'].values())
        print(f"Hashes (Total):    {C.YELLOW}{tot_hashes}{C.RESET}")
        print(f"Knækkede Hashes:   {C.GREEN}{len(self.data['Knækkede_Passwords_Klartekst'])}{C.RESET}")
        print(f"{C.DIM}" + "-"*60 + f"{C.RESET}")

    def _save_report(self):
        folder = session.get("loot_folder", "loot_evidence")
        os.makedirs(folder, exist_ok=True)
        safe_target = self.data["Target"].replace(' ', '_').replace('/', '_')
        filename = f"{folder}/36_PASTEBIN_{safe_target}_{datetime.now().strftime('%H%M%S')}.json"
        
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        datalake.ingest(self.name, self.data["Target"], self.data)
        print(f"{C.GREEN}[✓] Data og knækkede passwords arkiveret sikkert!{C.RESET}")