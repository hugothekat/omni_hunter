#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GOLIATH LOOT EXTRACTOR
📌 Formål: Udtrukning af alle credentials (inkl. crackede hashes) fra Data Laket til rå tekst.
"""
import sys
import sqlite3
import argparse
from pathlib import Path

# GOLIATH AUTO-HEAL: Importer core konfiguration
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.utils import C, session, get_active_workspace

def dump_credentials(output_filename: str):
    # Udled stien til databasen i dit aktive workspace
    active_dir = Path(session.get("loot_folder", get_active_workspace()))
    db_path = active_dir / "omni_datalake.db"
    
    if not db_path.exists():
        print(f"{C.RED}[!] Fejl: Kunne ikke finde Data Lake databasen ved {db_path}{C.RESET}")
        return

    print(f"{C.CYAN}[*] Forbinder til GOLIATH Data Lake for udtræk...{C.RESET}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Hent alle unikke username:password kombinationer
            cursor = conn.execute("SELECT DISTINCT username, password FROM extracted_credentials")
            rows = cursor.fetchall()
            
        if not rows:
            print(f"{C.YELLOW}[!] Ingen lækkede credentials fundet i databasen endnu.{C.RESET}")
            return
            
        output_path = active_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            for user, pwd in rows:
                f.write(f"{user}:{pwd}\n")
                
        print(f"{C.GREEN}[+] SUCCESS: Eksporterede {len(rows)} unikke credentials til: {output_path}{C.RESET}")
        print(f"{C.DIM}Disse data er nu klar til at blive fodret ind i Hydra, Hashcat eller lignende værktøjer.{C.RESET}")
        
    except Exception as e:
        print(f"{C.RED}[!] Databasefejl under udtrækning: {e}{C.RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GOLIATH Credential Dumper")
    parser.add_argument("-o", "--output", type=str, default="GOLIATH_CREDENTIALS_DUMP.txt", help="Navn på output filen (gemmes i loot mappen)")
    args = parser.parse_args()
    dump_credentials(args.output)