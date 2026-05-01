#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GOLIATH CELERY INJECTOR
📌 Formål: Læser en liste af mål (f.eks. targets.txt) og pumper dem 
           direkte ind i Redis-brokeren, så Celery workers kan angribe.
"""
import sys
import time
import argparse
from pathlib import Path

# Sikrer at vi kan importere fra roden af projektet
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.utils import logger, C

try:
    # Importerer din Celery task direkte fra din web_server (som defineret i din arkitektur)
    from core.web_server import scrape_user_task
except ImportError as e:
    print(f"{C.RED}[!] Kritisk Fejl: Kunne ikke importere Celery appen. Fejl: {e}{C.RESET}")
    print(f"{C.YELLOW}[*] Sørg for at køre dette script fra roden af dit workspace.{C.RESET}")
    sys.exit(1)

def inject_targets(filepath: str):
    path = Path(filepath)
    if not path.exists():
        print(f"{C.RED}[!] Fejl: Mål-filen '{filepath}' blev ikke fundet.{C.RESET}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip()]

    if not targets:
        print(f"{C.YELLOW}[!] Filen er tom. Intet at angribe.{C.RESET}")
        return

    print(f"{C.CYAN}[*] Starter GOLIATH Celery Payload Injection...{C.RESET}")
    print(f"[*] Pumper {len(targets)} mål fra '{filepath}' direkte ind i Redis brokeren...")

    success_count = 0
    for target in targets:
        try:
            # .delay() skubber opgaven asynkront til Redis-køen
            scrape_user_task.delay(target)
            success_count += 1
            # OPSEC: 10ms forsinkelse forhindrer Redis i at afvise forbindelsen (Error 111) ved massive lister
            time.sleep(0.01) 
        except Exception as e:
            logger.error(f"Fejl ved afsendelse af '{target}' til Celery: {e}")

    print(f"{C.GREEN}[+] Mission fuldført! {success_count} operationer ligger nu klar i køen.{C.RESET}")
    print(f"{C.YELLOW}[ℹ] Dine aktive Celery workers vil automatisk begynde at nedbryde køen.{C.RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GOLIATH Celery Queue Injector")
    parser.add_argument("-f", "--file", type=str, default="targets.txt", help="Sti til fil med mål (standard: targets.txt)")
    args = parser.parse_args()
    inject_targets(args.file)