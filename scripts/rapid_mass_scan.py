#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GOLIATH RAPID MASS RECON (PARALLEL SCRAPER)
📌 Formål: Scraper 10+ URL'er samtidigt via The Apex Browser (SOCKS5 + WAF Bypass).
"""
import sys
import time
import argparse
import concurrent.futures
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.browser import OmniHunterBrowser, BrowserConfig
from core.utils import logger, C, datalake

def scan_target(url: str):
    try:
        # Starter The Apex Browser med proxy rotation aktiveret
        config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            proxy_rotation_enabled=True,
            anti_detection=True,
            auto_extract_osint=True
        )
        hunter = OmniHunterBrowser(config)
        hunter.start() # Manglende opstart tilføjet
        result = hunter.fetch(url)
        datalake.ingest(source_module="rapid_mass_recon", target=url, data=result)
        print(f"{C.GREEN}[+] Succes: {url} (OSINT data gemt i FTS5 Data Lake){C.RESET}")
    except Exception as e:
        print(f"{C.RED}[!] Fejl under infiltration af {url}: {e}{C.RESET}")
    finally:
        if 'hunter' in locals():
            hunter.close() # OPSEC: Sikrer at vi ikke efterlader zombi-processer i RAM

def run_mass_scan(filepath: str = None, target_urls: list = None, max_workers: int = 10):
    urls = []
    if target_urls:
        for u in target_urls:
            urls.append(u if u.startswith("http") else f"https://{u}")
    if filepath:
        path = Path(filepath)
        if not path.exists():
            print(f"{C.RED}[!] Fejl: Mål-filen '{filepath}' blev ikke fundet.{C.RESET}")
            return
        urls = [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip() and line.startswith("http")]
    
    if not urls:
        print(f"{C.YELLOW}[!] Ingen gyldige URL'er at scanne.{C.RESET}")
        return
        
    print(f"{C.CYAN}[*] Initiating Rapid Mass Recon mod {len(urls)} mål...{C.RESET}")
    print(f"{C.CYAN}[*] Spinder op til {max_workers} samtidige stealth-browsere.{C.RESET}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(scan_target, urls)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GOLIATH Rapid Mass Recon")
    parser.add_argument("-f", "--file", type=str, help="Fil med URL'er (én pr. linje)")
    parser.add_argument("-u", "--url", nargs='+', help="En eller flere URL'er adskilt af mellemrum (fx https://mitur.dk https://dr.dk)")
    parser.add_argument("-w", "--workers", type=int, default=10, help="Antal parallelle browsere")
    args = parser.parse_args()
    
    if not args.file and not args.url:
        print(f"{C.RED}[!] Fejl: Angiv enten -f <fil> eller -u <url>{C.RESET}")
        sys.exit(1)
        
    run_mass_scan(filepath=args.file, target_urls=args.url, max_workers=args.workers)