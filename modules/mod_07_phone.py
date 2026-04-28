# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
import re
import time
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By 

from core.utils import C, session
from core.network import omni_dork_search, safe_get_with_retry

# NY V7: Omdøbt fra PhoneIntelligenceHunter til PhoneIntelligenceAnalyst 
# Dette FIXER fejlen, hvor Modul 02 Pivoten ikke kunne importere modulet!
class PhoneIntelligenceHunter:
    """Deep web search for phone number occurrences (GOLIATH V8)"""
    def __init__(self, phone):
        self.phone = str(phone).replace(" ", "").replace("+45", "").replace("-", "")
        self.data = {
            "Nummer": f"+45 {self.phone}",
            "Web_Spor": [],
            "Social_Spor": [],            # NY V7: Tjekker Facebook/Insta
            "Direct_App_Links": [],       # NY V7: WhatsApp, Telegram osv.
            "Deep_Scrape_Mål": {          # NY V7: Dybde-udtræk
                "Emails": [],
                "CVR": []
            },
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        """Execute phone search"""
        print(f"\n{C.CYAN}{'='*60}\n[07] Telefon-efterretning (Dorking Matrix & Deep Scrape)\n{'='*60}{C.RESET}")
        print(f"Target: +45 {self.phone}\n")

        # NY V7 TILFØJELSE: Genererer Messaging Links før vi dorker
        self._generate_app_links()

        # Bygger alle tænkelige måder et dansk nummer kan skrives på
        formats = [
            f'"{self.phone}"',
            f'"{self.phone[:2]} {self.phone[2:4]} {self.phone[4:6]} {self.phone[6:8]}"',
            f'"{self.phone[:4]} {self.phone[4:]}"',
            f'"{self.phone[:2]}-{self.phone[2:4]}-{self.phone[4:6]}-{self.phone[6:8]}"',
            f'"+45{self.phone}"',
            f'"+45 {self.phone}"'
        ]
        
        print(f"\n{C.YELLOW}[*] Udruller massiv søgning på {len(formats)} tal-formater...{C.RESET}")
        
        # Samler alt i ét stort DORK call for stealth og speed
        combined_dork = " OR ".join(formats)
        
        # Bruger din centrale omni_dork_search for anti-bot beskyttelse og bing-fallback
        links = omni_dork_search(driver, combined_dork, max_links=10)
        
        if links:
            for link in links:
                href = link["url"]
                # Vi ignorerer krak/dgs/118 da vi allerede har et dedikeret modul (01) til det
                if "krak.dk" not in href and "degulesider.dk" not in href and "118.dk" not in href:
                    print(f"{C.GREEN}    🔥 SPOR: {href[:80]}{C.RESET}")
                    if href not in self.data["Web_Spor"]:
                        self.data["Web_Spor"].append(href)
        else:
            print(f"{C.DIM}    [-] Ingen offentlige web-spor fundet udover standard registre.{C.RESET}")
        
        # NY V7 TILFØJELSE: Dedikeret Social Media Scanner for telefonnummeret
        self._social_media_dork(driver)
        
        # NY V7 TILFØJELSE: Gå ind på de fundne links og stjæl emails og CVR numre!
        self._deep_scrape_links(driver)

        print(f"\n{C.GREEN}[✓] Telefon-efterretning 100% færdig.{C.RESET}")
        self.save()

    def _generate_app_links(self):
        """Bygger klikbare URL'er til OSINT på Messaging Apps"""
        print(f"{C.YELLOW}[*] Genererer direkte API-links til Messaging OSINT...{C.RESET}")
        
        wa_link = f"https://wa.me/45{self.phone}"
        tg_link = f"https://t.me/+45{self.phone}"
        vi_link = f"viber://add?number=45{self.phone}"
        
        self.data["Direct_App_Links"] = [
            {"App": "WhatsApp", "URL": wa_link},
            {"App": "Telegram", "URL": tg_link},
            {"App": "Viber", "URL": vi_link}
        ]
        
        print(f"{C.CYAN}    -> WhatsApp: {wa_link} (Brug til at tjekke profilbillede){C.RESET}")

    def _social_media_dork(self, driver):
        """Krydssøger på Sociale Medier (Ofte skriver folk 'Ring til mig på XXXX' i grupper)"""
        print(f"\n{C.YELLOW}[*] Udfører dedikeret Social Media Dorking på nummeret...{C.RESET}")
        if not driver: return
        
        dork = f'(site:facebook.com OR site:instagram.com OR site:linkedin.com OR site:twitter.com) "{self.phone}" OR "+45 {self.phone}"'
        links = omni_dork_search(driver, dork, max_links=4)
        
        if links:
            for link in links:
                print(f"{C.GREEN}    🔥 SOCIAL HIT: {link['url'][:80]}{C.RESET}")
                if link['url'] not in self.data["Social_Spor"]:
                    self.data["Social_Spor"].append(link['url'])
        else:
            print(f"{C.DIM}    [-] Ingen åbenlyse hits på sociale medier.{C.RESET}")

    def _deep_scrape_links(self, driver):
        """Går fysisk ind på de fundne websider for at trække E-mails og CVR ud!"""
        if not driver or not self.data["Web_Spor"]: return
        
        print(f"\n{C.YELLOW}[*] Deep Scrape: Analyserer fundne sider for tilknyttede data...{C.RESET}")
        
        for url in self.data["Web_Spor"][:4]: # Tager de top 4 bedste spor
            print(f"{C.DIM}    -> Åbner: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(3)
                
                # Fjerner Cookie popups
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["accept", "tillad", "godkend", "ok"]):
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1); break
                except: pass

                page_text = driver.find_element(By.TAG_NAME, "body").text

                # 1. Udtræk CVR
                cvr_matches = re.findall(r'\b(?:CVR|cvr)[\s:-]*(\d{8})\b', page_text)
                for cvr in set(cvr_matches):
                    if cvr not in self.data["Deep_Scrape_Mål"]["CVR"]:
                        self.data["Deep_Scrape_Mål"]["CVR"].append(cvr)
                        print(f"{C.MAGENTA}      ✓ Tilknyttet CVR fundet: {cvr}{C.RESET}")

                # 2. Udtræk Emails
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', page_text)
                for em in set(emails):
                    clean_em = em.lower()
                    if clean_em not in self.data["Deep_Scrape_Mål"]["Emails"] and not any(ext in clean_em for ext in [".png", ".jpg", "sentry"]):
                        self.data["Deep_Scrape_Mål"]["Emails"].append(clean_em)
                        print(f"{C.CYAN}      ✓ Tilknyttet Email fundet: {clean_em}{C.RESET}")

            except Exception as e:
                print(f"{C.DIM}      [-] Kunne ikke deep-scrape {url}{C.RESET}")

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/07_PHONE_{self.phone}.json"
        
        # Sikrer overskrivning
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass
            
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n{C.GREEN}[✓] Rapport gemt (Overskrevet succesfuldt): {filename}{C.RESET}")