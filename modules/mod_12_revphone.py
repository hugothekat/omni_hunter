# -*- coding: utf-8 -*-
import json
import os
import sys
import re
import time
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By # NY V8 FIX: Manglende import for WhatsApp scraperen

from core.utils import C, session
from core.network import omni_dork_search, safe_get_with_retry

class ReversePhoneIntelligence:
    def __init__(self, phone):
        self.phone = phone.replace(" ", "").replace("+45", "").strip()
        self.data = {
            "Telefon": self.phone,
            "OSINT_Hits": [],
            "Brugtmarked_Spor": [],       # NY V8: DBA, G&G
            "Svindel_Advarsler": [],      # NY V8: 180.dk, ukendtnummer.dk
            "WhatsApp_Status": "Ukendt",
            "Telegram_Status": "Ukendt",  # NY V8: Telegram Tjek
            "Viber_Status": "Ukendt",     # NY V8: Viber Tjek
            "Identificeret_Navn": "",
            "Alias_Brugernavne": [],      # NY V8: Dæknavne fra annoncer
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[12] Omvendt Telefon-Intelligence (GOLIATH V8)\n{'='*60}{C.RESET}")
        print(f"Target Nummer: {self.phone}\n")

        if not driver:
            print(f"{C.RED}[!] Fejl: Modul 12 kræver en aktiv stealth driver.{C.RESET}")
            return

        # V7: Genererer formater
        p = self.phone
        formats = [
            p,                                  # 12345678
            f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:]}", # 12 34 56 78
            f"{p[:4]} {p[4:]}",                 # 1234 5678
            f"+45 {p}",                         # +45 12345678
            f"45{p}"                            # 4512345678 (WhatsApp format)
        ]

        print(f"{C.YELLOW}[*] Udfører Multi-Format OSINT Dorking over 15+ platforme...{C.RESET}")
        search_query = " OR ".join([f'"{f}"' for f in formats[:4]])
        
        # --- NY V8: CHUNK DORKING (Krak, Brugtmarked, Spam-databaser, Global OSINT) ---
        dork_chunks = [
            # Chunk 1: Klassiske registre og Social
            f"({search_query}) site:krak.dk OR site:degulesider.dk OR site:118.dk OR site:facebook.com",
            # Chunk 2: Danske Brugtmarkeder (Guldgrube for taletidskort og svindlere)
            f"({search_query}) site:dba.dk OR site:guloggratis.dk OR site:trendsales.dk OR site:trustpilot.com",
            # Chunk 3: Svindel-databaser og Globale Caller-ID's
            f"({search_query}) site:180.dk OR site:ukendtnummer.dk OR site:truecaller.com OR site:sync.me"
        ]

        for chunk_idx, dork in enumerate(dork_chunks):
            sys.stdout.write(f"\r{C.CYAN}    [*] Skanner Matrix Del {chunk_idx+1}/{len(dork_chunks)}...      {C.RESET}")
            sys.stdout.flush()
            
            links = omni_dork_search(driver, dork, max_links=5)
            
            if links:
                for link in links:
                    url = link['url']
                    titel = link.get('title', '')
                    snippet = link.get('snippet', '')
                    
                    sys.stdout.write("\r" + " " * 80 + "\r")
                    print(f"{C.GREEN}    🔥 SPOR FUNDET: {url[:70]}...{C.RESET}")
                    
                    # V7 Auto-Identifikation fra Gule Sider / Krak
                    if any(x in url for x in ["krak.dk", "degulesider.dk", "118.dk"]):
                        pot_navn = titel.split('-')[0].strip()
                        if pot_navn and not self.data["Identificeret_Navn"] and "Krak" not in pot_navn:
                            self.data["Identificeret_Navn"] = pot_navn
                            print(f"{C.MAGENTA}      -> Identitet detekteret ud fra nummer: {pot_navn}{C.RESET}")
                            
                    # NY V8: Auto-Identifikation fra Brugtmarkeder
                    elif any(x in url for x in ["dba.dk", "guloggratis.dk"]):
                        if url not in self.data["Brugtmarked_Spor"]:
                            self.data["Brugtmarked_Spor"].append(url)
                        
                        # Prøver at trække "Sælger:" eller navnet fra titlen
                        seller_match = re.search(r'af ([A-ZÆØÅa-zæøå\s]+)\s*[-|]', titel)
                        if seller_match:
                            alias = seller_match.group(1).strip()
                            if alias not in self.data["Alias_Brugernavne"]:
                                self.data["Alias_Brugernavne"].append(alias)
                                print(f"{C.MAGENTA}      -> Brugtmarkeds-Alias fundet: {alias}{C.RESET}")
                                
                    # NY V8: Auto-Advarsel fra Spam-databaser
                    elif any(x in url for x in ["180.dk", "ukendtnummer.dk"]):
                        if url not in self.data["Svindel_Advarsler"]:
                            self.data["Svindel_Advarsler"].append(url)
                            print(f"{C.RED}      [!] ADVARSEL: Nummeret er flaget i svindel/spam database!{C.RESET}")
                    
                    if url not in self.data["OSINT_Hits"]:
                        self.data["OSINT_Hits"].append(url)

        if not self.data["OSINT_Hits"]:
            sys.stdout.write("\r" + " " * 80 + "\r")
            print(f"{C.DIM}    [-] Ingen resultater via åben OSINT-dorking.{C.RESET}")

        # V7: WhatsApp Web API Tjek
        print(f"\n{C.YELLOW}[*] Checker WhatsApp-registrering via Web API...{C.RESET}")
        wa_url = f"https://api.whatsapp.com/send?phone=45{self.phone}"
        if safe_get_with_retry(driver, wa_url, max_retries=1):
            time.sleep(2)
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "isn't on whatsapp" in page_text or "er ikke på whatsapp" in page_text:
                self.data["WhatsApp_Status"] = "Ikke Registreret"
                print(f"{C.DIM}    [-] Nummeret er IKKE registreret på WhatsApp.{C.RESET}")
            else:
                self.data["WhatsApp_Status"] = "Sandsynligvis Aktiv"
                print(f"{C.RED}    [!] Nummeret ER sandsynligvis aktivt på WhatsApp!{C.RESET}")

        # NY V8: Telegram Web API Tjek
        print(f"{C.YELLOW}[*] Checker Telegram-registrering via t.me...{C.RESET}")
        tg_url = f"https://t.me/+45{self.phone}"
        if safe_get_with_retry(driver, tg_url, max_retries=1):
            time.sleep(2)
            tg_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "if you have telegram, you can contact" in tg_text or "send message" in tg_text:
                self.data["Telegram_Status"] = "Sandsynligvis Aktiv"
                print(f"{C.RED}    [!] Nummeret ER sandsynligvis aktivt på Telegram!{C.RESET}")
            else:
                self.data["Telegram_Status"] = "Ukendt / Skjult"
                print(f"{C.DIM}    [-] Ingen offentlig profil fundet på Telegram.{C.RESET}")

        # NY V8: Viber Opslag
        print(f"{C.YELLOW}[*] Genererer direkte Viber API link...{C.RESET}")
        vi_link = f"viber://add?number=45{self.phone}"
        print(f"{C.CYAN}    -> Viber Tjek-link: {vi_link}{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/12_REVPHONE_{self.phone}.json"
        
        # NY V8: Sikker fil-overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Telefon rapport gemt: {filename}{C.RESET}")