# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from core.utils import C, session
from core.network import safe_get_with_retry, omni_dork_search

class ReversePhoneIntelligence:
    """True Reverse lookup med Kontekst-Injektion og Data-Fletning"""
    def __init__(self, phone, context_data=None, save_path=None):
        self.raw_phone = phone.replace(" ", "").replace("+45", "").replace("-", "")
        self.save_path = save_path
        
        self.data = context_data if context_data else {
            "Telefon": f"+45 {self.raw_phone}",
            "Identificeret_Navn": "Ukendt",
            "Lokation": "Ukendt",
            "Timestamp": datetime.now().isoformat()
        }
        
        if "Telefon_Efterretning" not in self.data:
            self.data["Telefon_Efterretning"] = {"Kilder": [], "SoMe_Spor": []}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[12] Identificer ukendt telefonnummer\n{'='*60}{C.RESET}")
        print(f"Søger på: +45 {self.raw_phone}\n")
        
        kendt_identitet = self.data.get("Identitet", None)
        if kendt_identitet:
            print(f"{C.GREEN}[*] Springer Krak over. Identitet allerede fastslået: {kendt_identitet}{C.RESET}")
        else:
            # 1. Direkte opslag på Krak for ukendte numre
            krak_url = f"https://www.krak.dk/søg/{self.raw_phone}/personer"
            print(f"{C.YELLOW}[*] Tjekker offentlige danske registre (Krak)...{C.RESET}")
            
            if safe_get_with_retry(driver, krak_url):
                try:
                    name_elements = driver.find_elements(By.CSS_SELECTOR, "h2 a, h1.name")
                    if name_elements:
                        navn = name_elements[0].text.strip()
                        self.data["Identificeret_Navn"] = navn
                        self.data["Telefon_Efterretning"]["Kilder"].append("Krak.dk")
                        print(f"{C.GREEN}    ✓ IDENTIFICERET: {navn}{C.RESET}")
                    else:
                        print(f"{C.YELLOW}    [-] Intet match på Krak (Muligvis hemmeligt nummer eller taletidskort){C.RESET}")
                except Exception: pass

        # 2. Advanced Dorking & SoMe Spor
        print(f"\n{C.YELLOW}[*] Graver efter sociale netværk og MobilePay links...{C.RESET}")
        
        wa_url = f"https://wa.me/45{self.raw_phone}"
        mp_url = f"https://box.mobilepay.dk/pay?phone={self.raw_phone}"
        
        print(f"{C.CYAN}    -> WhatsApp Direct: {wa_url} (Åbn på mobil for at se profilbillede){C.RESET}")
        print(f"{C.CYAN}    -> MobilePay Check: {mp_url} (Åbn i app for at bekræfte navn){C.RESET}")
        
        self.data["Telefon_Efterretning"]["SoMe_Spor"].extend([wa_url, mp_url])
        
        # TrueCaller, Sync.me og 118.dk Dorking for at fange spam/hemmelige numre
        print(f"\n{C.YELLOW}[*] Checker globale spam-databaser og 118...{C.RESET}")
        dork = f'"{self.raw_phone}" OR "+45 {self.raw_phone}" site:truecaller.com OR site:sync.me OR site:118.dk'
        links = omni_dork_search(driver, dork, max_links=3)
        
        if links:
            for link in links:
                print(f"{C.GREEN}    🔥 Eksternt database-hit fundet: {link['url']}{C.RESET}")
                self.data["Telefon_Efterretning"]["Kilder"].append(link['url'])
        else:
            print(f"{C.DIM}    [-] Ingen hits i globale telefon-databaser.{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = self.save_path if self.save_path else f"{session['loot_folder']}/12_REVERSE_PHONE_{self.raw_phone}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding='utf-8')
        print(f"\n{C.GREEN}[✓] Data flettet og gemt i sagmappe: {filename}{C.RESET}")