# -*- coding: utf-8 -*-
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from core.utils import C, session
from core.network import omni_dork_search, safe_get_with_retry

class ReversePhoneIntelligence:
    def __init__(self, phone):
        self.phone = phone.replace(" ", "").replace("+45", "").strip()
        self.data = {
            "Telefon": self.phone,
            "OSINT_Hits": [],
            "WhatsApp_Status": "Ukendt",
            "Identificeret_Navn": "",
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[12] Omvendt Telefon-Intelligence (GOLIATH V7)\n{'='*60}{C.RESET}")
        print(f"Target Nummer: {self.phone}\n")

        if not driver:
            print(f"{C.RED}[!] Fejl: Modul 12 kræver en aktiv stealth driver.{C.RESET}")
            return

        # V7: Genererer formater
        p = self.phone
        formats = [
            p,                                  # 12345678
            f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:]}", # 12 34 56 78
            f"+45 {p}",                         # +45 12345678
            f"45{p}"                            # 4512345678 (WhatsApp format)
        ]

        print(f"{C.YELLOW}[*] Udfører Multi-Format OSINT Dorking...{C.RESET}")
        
        search_query = " OR ".join([f'"{f}"' for f in formats[:3]])
        # Rammer MobilePay bokse, Gule Sider, og sociale medier hvor numre ofte lækkes
        dork = f"({search_query}) site:krak.dk OR site:degulesider.dk OR site:118.dk OR site:facebook.com"
        
        links = omni_dork_search(driver, dork, max_links=5)
        
        if links:
            for link in links:
                url = link['url']
                titel = link.get('title', '')
                snippet = link.get('snippet', '')
                print(f"{C.GREEN}    🔥 SPOR FUNDET: {url[:70]}...{C.RESET}")
                
                # V7 Auto-Identifikation fra Gule Sider / Krak
                if any(x in url for x in ["krak.dk", "degulesider.dk", "118.dk"]):
                    pot_navn = titel.split('-')[0].strip()
                    if pot_navn and not self.data["Identificeret_Navn"]:
                        self.data["Identificeret_Navn"] = pot_navn
                        print(f"{C.MAGENTA}      -> Identitet detekteret ud fra nummer: {pot_navn}{C.RESET}")
                
                self.data["OSINT_Hits"].append(url)
        else:
            print(f"{C.DIM}    [-] Ingen resultater via åben OSINT-dorking.{C.RESET}")

        # V7: WhatsApp Web API Tjek (Undersøger om nummeret er registreret på WhatsApp uden at logge ind)
        print(f"\n{C.YELLOW}[*] Checker WhatsApp-registrering via Web API...{C.RESET}")
        wa_url = f"https://api.whatsapp.com/send?phone=45{self.phone}"
        if safe_get_with_retry(driver, wa_url, max_retries=1):
            import time
            time.sleep(2)
            # Hvis nummeret IKKE findes, skriver WhatsApp det på siden.
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "isn't on whatsapp" in page_text or "er ikke på whatsapp" in page_text:
                self.data["WhatsApp_Status"] = "Ikke Registreret"
                print(f"{C.DIM}    [-] Nummeret er IKKE registreret på WhatsApp.{C.RESET}")
            else:
                self.data["WhatsApp_Status"] = "Sandsynligvis Aktiv"
                print(f"{C.RED}    [!] Nummeret ER sandsynligvis aktivt på WhatsApp!{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/12_REVPHONE_{self.phone}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Telefon rapport gemt: {filename}{C.RESET}")