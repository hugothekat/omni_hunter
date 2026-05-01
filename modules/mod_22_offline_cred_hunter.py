#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V65: OFFLINE CREDENTIAL & HASH RIPPER
📌 Formål: Dybdegående OSINT parsing af offline SITERIP workspaces for lækkede credentials, hashes og JWTs.
"""

import os
import re
import json
import concurrent.futures
import hashlib
import gzip
from pathlib import Path
import sys

# GOLIATH AUTO-HEAL: Sikrer at vi kan importere core uanset hvorfra scriptet kaldes
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.utils import logger, C, datalake, JWTExtractor, ThreatIntelExtractor

class OfflineCredHunter:
    def __init__(self, workspace_dir: str):
        # Rens 'file://' væk, så drag-and-drop fra filhåndtering virker fejlfrit
        self.workspace_dir = Path(workspace_dir.replace("file://", ""))
        self.results_found = 0
        
        # Aggressive mønstre til at fange kryptografiske hashes og credentials
        self.patterns = {
            "bcrypt": re.compile(r'(\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53})'),
            "argon2": re.compile(r'(\$argon2(?:id?|d)\$v=\d+\$m=\d+,t=\d+,p=\d+\$[A-Za-z0-9+/]+\$[A-Za-z0-9+/]+)'),
            "sha256": re.compile(r'\b([a-fA-F0-9]{64})\b'),
            "md5": re.compile(r'\b([a-fA-F0-9]{32})\b'),
            "sha1": re.compile(r'\b([a-fA-F0-9]{40})\b'),
            "htpasswd": re.compile(r'^([a-zA-Z0-9_-]+):(\$apr1\$[a-zA-Z0-9./]{22}|\{SHA\}[a-zA-Z0-9+/]{27}=)$', re.MULTILINE),
            "basic_auth": re.compile(r'(?i)Authorization:\s*Basic\s+([A-Za-z0-9+/=]+)'),
            "cleartext_json": re.compile(r'(?i)"(?:password|passwd|pwd|secret)"\s*:\s*"([^"]+)"'),
            "aws_key": re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),
            "ssh_key": re.compile(r'(-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----[\s\S]+?-----END (?:RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----)')
        }
        
        # GOLIATH EXPANSION: RAM-Optimeret Auto-Cracker (Understøtter nu .gz fra Parrot OS)
        self.wordlist_lines = []
        self.wordlist_path = Path("/usr/share/wordlists/rockyou.txt")
        self.wordlist_gz_path = Path("/usr/share/wordlists/rockyou.txt.gz")
        
        if self.wordlist_path.exists() or self.wordlist_gz_path.exists():
            logger.info("GOLIATH AUTO-CRACKER: Indlæser Top-1M ordbog i RAM (dette tager et sekund)...")
            try:
                if self.wordlist_path.exists():
                    with open(self.wordlist_path, 'r', encoding='latin-1') as f:
                        self.wordlist_lines = [next(f).strip() for _ in range(1000000)]
                else:
                    with gzip.open(self.wordlist_gz_path, 'rt', encoding='latin-1') as f:
                        self.wordlist_lines = [next(f).strip() for _ in range(1000000)]
            except StopIteration:
                pass
        else:
            logger.warning(f"GOLIATH AUTO-CRACKER: Ingen wordlist fundet. Auto-cracking deaktiveret.")

    def _crack_hashes(self, hashes: set, hashtype: str) -> dict:
        """Auto-cracker MD5 og SHA1 asynkront mod RAM-cachet wordlist."""
        cracked = {}
        if not hashes or not self.wordlist_lines:
            return cracked
            
        target_hashes = hashes.copy()
        for word in self.wordlist_lines:
            if not word: continue
            
            # Genererer hashet lynhurtigt i RAM og tjekker om vi har et match
            h = hashlib.md5(word.encode('utf-8', errors='ignore')).hexdigest() if hashtype == 'md5' else hashlib.sha1(word.encode('utf-8', errors='ignore')).hexdigest()
            
            if h in target_hashes:
                cracked[h] = word
                target_hashes.remove(h)
                if not target_hashes: break # Stop hvis vi har krækket alle hashes for denne fil
        return cracked

    def parse_file(self, file_path: Path):
        """Læser filen iterativt for at bevare RAM og udtrukne artefakter pumpes i Data Laket."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            extracted_creds = set()
            extracted_jwts = []
            found_md5 = set()
            found_sha1 = set()
            
            # 1. Søg efter JWT Tokens (GOLIATH V65 Integration)
            jwts = JWTExtractor.extract_and_decode(content)
            if jwts:
                extracted_jwts.extend(jwts)

            # 2. Søg efter stærke password hashes (Bcrypt / Argon2)
            for match in self.patterns["bcrypt"].findall(content):
                extracted_creds.add(f"UNKNOWN_USER:{match}")
            for match in self.patterns["argon2"].findall(content):
                extracted_creds.add(f"UNKNOWN_USER:{match}")
                
            # 3. Søg efter Basic Auth Base64 strenge og dekod dem
            for b64_match in self.patterns["basic_auth"].findall(content):
                try:
                    import base64
                    decoded = base64.b64decode(b64_match).decode('utf-8')
                    if ':' in decoded:
                        extracted_creds.add(decoded)
                except Exception: pass

            # 4. JSON / Klartekst Password felter
            for pwd_match in self.patterns["cleartext_json"].findall(content):
                if len(pwd_match) > 2: # Filtrer tomme strenge ud
                    extracted_creds.add(f"JSON_TARGET:{pwd_match}")
                    
            # 5. Htpasswd Filer (Apache/Nginx leak)
            for ht_user, ht_hash in self.patterns["htpasswd"].findall(content):
                extracted_creds.add(f"{ht_user}:{ht_hash}")
                
            # 6. GOLIATH EXPANSION: Cloud & Infrastructure HVT Intel (AWS / SSH)
            for aws_key in self.patterns["aws_key"].findall(content):
                extracted_creds.add(f"AWS_ACCESS_KEY:{aws_key}")
            for ssh_key in self.patterns["ssh_key"].findall(content):
                # For at bevare overblikket i Data Lake, noterer vi kun at filen rummer nøglen
                extracted_creds.add(f"SSH_PRIVATE_KEY:FOUND_IN_{file_path.name}")
                
            # 7. GOLIATH EXPANSION: MD5 & SHA1 Auto-Cracking
            found_md5.update(self.patterns["md5"].findall(content))
            found_sha1.update(self.patterns["sha1"].findall(content))
            
            if found_md5 or found_sha1:
                cracked_md5 = self._crack_hashes(found_md5, 'md5')
                cracked_sha1 = self._crack_hashes(found_sha1, 'sha1')
                
                for h in found_md5:
                    if h in cracked_md5: extracted_creds.add(f"CRACKED_MD5_{h}:{cracked_md5[h]}")
                    else: extracted_creds.add(f"UNCRACKED_MD5:{h}")
                    
                for h in found_sha1:
                    if h in cracked_sha1: extracted_creds.add(f"CRACKED_SHA1_{h}:{cracked_sha1[h]}")
                    else: extracted_creds.add(f"UNCRACKED_SHA1:{h}")

            # --- GOLIATH INGESTION ---
            # Vi formatterer det, så core/utils.py og web_server.py automatisk fanger det til Django ORM.
            if extracted_creds or extracted_jwts:
                self.results_found += 1
                payload = {
                    "source_file": str(file_path.name),
                    "Rå_Kredentialer": list(extracted_creds),
                    "intercepted_jwts": extracted_jwts
                }
                
                # Smid det ind i den centrale Datalake for at trigge Web Dashboard og Telegram Alerts
                datalake.ingest(
                    source_module="mod_22_offline_cred_hunter", 
                    target=file_path.stem, 
                    data=payload
                )
                logger.info(f"[+] FOUND LOOT: {len(extracted_creds)} creds & {len(extracted_jwts)} JWTs i {file_path.name}")

        except Exception as e:
            logger.error(f"Fejl ved læsning af {file_path}: {e}")

    def hunt(self, max_workers=10):
        """Dykker asynkront ned i SITERIP-mappen og analyserer filer i parallel."""
        if not self.workspace_dir.exists():
            logger.critical(f"[-] Workspace mappen findes ikke: {self.workspace_dir}")
            return

        target_files = []
        # GOLIATH EXPANSION: Single-Target Mode (Skanner kun 1 fil af gangen hvis bedt om det)
        if self.workspace_dir.is_file():
            target_files.append(self.workspace_dir)
        else:
            for ext in ["*.json", "*.html", "*.txt", "*.js"]:
                target_files.extend(list(self.workspace_dir.rglob(ext)))

        logger.info(f"🚀 Starter Offline Credential Hunt på {len(target_files)} filer i {self.workspace_dir}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.parse_file, target_files)
            
        print(f"\n{C.GREEN}[✓] Operation komplet! Fandt lækager i {self.results_found} filer.{C.RESET}")
        print(f"{C.CYAN}[i] Tjek dit GOLIATH Command Center Dashboard for eksponerede credentials og dekodede JWTs.{C.RESET}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GOLIATH: Offline Credential & Hash Ripper")
    parser.add_argument("-d", "--directory", type=str, required=True, help="Sti til mappen ELLER en specifik .json/.html fil")
    parser.add_argument("-w", "--workers", type=int, default=10, help="Antal parallelle tråde (Default: 10)")
    args = parser.parse_args()
    
    hunter = OfflineCredHunter(args.directory)
    hunter.hunt(max_workers=args.workers)