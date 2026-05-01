#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GOLIATH UNIVERSAL MASS-INJECTOR
📌 Formål: Fodrer Celery-køen med 1.000+ vilkårlige domæner.
"""
import sys
import time
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.utils import logger, C

try:
    from core.web_server import scan_generic_url_task
except ImportError as e:
    print(f"{C.RED}[!] Kritisk Fejl: Kunne ikke importere Celery tasken. Fejl: {e}{C.RESET}")
    sys.exit(1)

def inject_urls(filepath: str):
    path = Path(filepath)
    if not path.exists():
        print(f"{C.RED}[!] Fejl: Mål-filen '{filepath}' blev ikke fundet.{C.RESET}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        return

    print(f"{C.CYAN}[*] Starter GOLIATH Universal URL Injection...{C.RESET}")
    print(f"[*] Pumper {len(urls)} URL'er ind i Redis brokeren...")

    success_count = 0
    for url in urls:
        try:
            # Send uafhængigt til worker-køen
            scan_generic_url_task.delay(url)
            success_count += 1
            time.sleep(0.01) # Broker rate-limit beskyttelse
        except Exception as e:
            logger.error(f"Fejl ved afsendelse af '{url}': {e}")

    print(f"{C.GREEN}[+] {success_count} domæner ligger nu klar i bagholdskøen.{C.RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GOLIATH Universal URL Queue Injector")
    parser.add_argument("-f", "--file", type=str, required=True, help="Sti til fil med URL'er (én pr linje)")
    args = parser.parse_args()
    inject_urls(args.file)