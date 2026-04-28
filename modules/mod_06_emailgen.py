# -*- coding: utf-8 -*-
import sys
import json
import os
import requests
import socket
import smtplib
import dns.resolver
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import omni_dork_search

class EmailPatternGenerator:
    def __init__(self, name):
        parts = name.strip().split()
        self.first = parts[0].lower() if len(parts) > 0 else "unknown"
        self.last = parts[-1].lower() if len(parts) > 1 else self.first
        self.middle = parts[1].lower() if len(parts) > 2 else ""
        self.name = name
        self.data = {
            "Navn": name,
            "Generated_Emails": [],
            "Verified_Emails": [],
            "SMTP_Bekræftede_Emails": [], # NY V8: E-mails bekræftet direkte via mailserver
            "Leaked_Emails": [],          # NY V8: E-mails fundet i hacker-databaser
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[06] E-mail-mønster & SMTP Validering (GOLIATH V8)\n{'='*60}{C.RESET}")
        print(f"Target: {self.name}\n")
        
        # Udvidet domæneliste for moderne trusselsbilleder og danske brugere
        domains = [
            "gmail.com", "hotmail.com", "live.dk", "mail.com", 
            "yahoo.dk", "yahoo.com", "icloud.com", "me.com", 
            "mac.com", "outlook.dk", "outlook.com", "protonmail.com"
        ]
        
        print(f"{C.YELLOW}[*] Genererer permutations-matrix for e-mails...{C.RESET}")
        
        # Standard Mønstre
        patterns = [
            f"{self.first}{self.last}", f"{self.first}.{self.last}",
            f"{self.first}_{self.last}", f"{self.first[0]}{self.last}",
            f"{self.first}{self.last[0]}", f"{self.last}{self.first}"
        ]
        
        # Udvidede danske mønstre (inkl. mellemnavn og fødselsår)
        if self.middle:
            patterns.extend([
                f"{self.first}{self.middle[0]}{self.last}",
                f"{self.first}.{self.middle[0]}.{self.last}"
            ])
            
        # Tilføjer typiske danske tal-endelser
        extended_patterns = list(patterns)
        for p in patterns:
            extended_patterns.extend([f"{p}88", f"{p}123", f"{p}1"])
            
        for domain in domains:
            for pat in set(extended_patterns):
                email = f"{pat}@{domain}"
                self.data["Generated_Emails"].append(email)

        print(f"{C.GREEN}    [+] Genererede {len(self.data['Generated_Emails'])} potentielle e-mails.{C.RESET}")
        
        # Udvælger de absolut mest sandsynlige mål for dybdeanalyse
        top_targets = [f"{self.first}{self.last}@{d}" for d in ["gmail.com", "hotmail.com"]] + \
                      [f"{self.first}.{self.last}@{d}" for d in ["gmail.com", "hotmail.com"]]
        
        # --- NY V8 INTELLIGENS: SMTP / DIRECT SERVER VERIFICATION ---
        print(f"\n{C.YELLOW}[*] Udfører direkte SMTP Server-validering (Stealth Ping)...{C.RESET}")
        for email in top_targets:
            if self._smtp_verify(email):
                print(f"{C.RED}    🔥 BEKRÆFTET VIA SERVER: E-mailen eksisterer! ({email}){C.RESET}")
                if email not in self.data["SMTP_Bekræftede_Emails"]:
                    self.data["SMTP_Bekræftede_Emails"].append(email)
            else:
                print(f"{C.DIM}      [-] {email} afvist af server eller server-timeout.{C.RESET}")
        
        # --- NY V8 INTELLIGENS: XPOSED OR NOT KRYDSTJEK ---
        print(f"\n{C.YELLOW}[*] Krydstjekker mod Hacker-lækager for eksistensbevis...{C.RESET}")
        for email in top_targets:
            if self._check_leak_db(email):
                print(f"{C.RED}    🔥 EKSISTENS BEVIST: {email} figurerer i datalæk!{C.RESET}")
                if email not in self.data["Leaked_Emails"]:
                    self.data["Leaked_Emails"].append(email)

        # --- EKSISTERENDE V7: LIVE DORK VALIDERING ---
        print(f"\n{C.YELLOW}[*] Udfører Live Dork-Validering af de mest sandsynlige e-mails...{C.RESET}")
        if driver:
            # Kombinerer de top e-mails i ét kald for hastighed
            dork = " OR ".join([f'"{t}"' for t in top_targets])
            hits = omni_dork_search(driver, dork, max_links=4)
            if hits:
                print(f"{C.GREEN}    🔥 OFFENTLIGE SPOR FUNDET PÅ NETTET!{C.RESET}")
                for h in hits:
                    url = h['url']
                    print(f"      -> {C.CYAN}{url}{C.RESET}")
                    
                    # Identificer hvilken e-mail der gav udslaget
                    for target in top_targets:
                        if target in h.get('snippet', '').lower():
                            if target not in self.data["Verified_Emails"]:
                                self.data["Verified_Emails"].append(target)
            else:
                print(f"{C.DIM}    [-] Ingen offentlige spor fundet via Google Dorking.{C.RESET}")
        else:
            print(f"{C.DIM}    [-] Ingen stealth-driver givet. Skipper Live Dork-Validering.{C.RESET}")

        self.save()

    def _smtp_verify(self, email):
        """
        NY V8: Forsøger at forbinde til e-mailens MX server og bruge 'RCPT TO'
        til at tjekke om mailboksen faktisk eksisterer (uden at sende en mail).
        """
        domain = email.split('@')[-1]
        try:
            # Find MX record for domænet
            records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(records[0].exchange)
            
            # Forbind til MX server (timeout sat til 3 sek for speed)
            server = smtplib.SMTP(timeout=3)
            server.set_debuglevel(0)
            
            server.connect(mx_record)
            server.helo(server.local_hostname)
            server.mail('admin@localhost.com')
            code, message = server.rcpt(str(email))
            server.quit()
            
            # Statuskode 250 betyder at serveren accepterer e-mailadressen!
            if code == 250:
                return True
            return False
            
        except Exception:
            # Fejler typisk pga timeout eller blokering - returner False
            return False

    def _check_leak_db(self, email):
        """NY V8: Slår op i XposedOrNot. Hvis emailen er lækket, SKAL den eksistere."""
        url = f"https://api.xposedornot.com/v1/check-email/{email}"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return True
            return False
        except Exception:
            return False

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/06_EMAILGEN_{self.name.replace(' ', '_')}.json"
        
        # Sikrer overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] E-mail rapport gemt: {filename}{C.RESET}")