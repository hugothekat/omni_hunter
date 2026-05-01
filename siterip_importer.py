#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V63: SITERIP DATA LAKE INJECTOR
📌 Formål: Importerer offline SITERIP JSON-filer direkte ind i OmniDataLake.
"""

import json
import os
from pathlib import Path
import argparse

from core.utils import datalake, logger, C

def import_siterip_data(directory: str):
    """
    Scanner en mappe rekursivt for .json filer og pumper dem ind i datalake.
    """
    siterip_path = Path(directory)
    if not siterip_path.is_dir():
        logger.error(f"Fejl: Mappen '{directory}' blev ikke fundet.")
        return

    json_files = list(siterip_path.rglob("*.json"))
    logger.info(f"Fandt {len(json_files)} SITERIP JSON-filer til import i '{directory}'.")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Bruger filnavnet som 'target' for at kunne spore oprindelsen
                datalake.ingest(source_module="siterip_importer", target=file_path.stem, data=data)
                print(f"{C.GREEN}[+] Importerede med succes: {file_path.name}{C.RESET}")
        except Exception as e:
            logger.error(f"Kunne ikke importere {file_path.name}", error=str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importerer SITERIP JSON-filer til OmniDataLake.")
    parser.add_argument("directory", type=str, help="Mappen, der indeholder SITERIP-filerne.")
    args = parser.parse_args()
    import_siterip_data(args.directory)