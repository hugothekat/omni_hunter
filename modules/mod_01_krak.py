# modules/mod_01_krak.py
import re
import time
import json
import os
import urllib.parse
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.utils import C, session
from core.network import safe_get_with_retry
from core.browser import zap_cookies

class DirectoryIntelligenceHunter:
    """Søger personinformation og ejendomsdata (Krak + DinGeo)."""
    def __init__(self, name, city):
        self.name = name.strip()
        self.city = city.strip()
        self.data = {
            "Identitet": self.name,
            "Lokation": self.city,
            "Telefonnumre": [],
            "Ejendom": {},
            "DinGeo_Data": {},
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[01] Personregister-efterretning (Krak + DinGeo)\n{'='*60}{C.RESET}")
        
        # Kraks nye søge-URL
        query = f"{self.name} {self.city}".strip().replace(" ", "+").lower()
        krak_url = f"https://www.krak.dk/{query}/personer"
        
        print(f"{C.YELLOW}[*] Forbinder til Krak: {krak_url}{C.RESET}")
        
        if safe_get_with_retry(driver, krak_url):
            zap_cookies(driver)
            time.sleep(4) # Giver React tid til at loade DOM'en
            
            # Tjek for bot-blokering
            if "Robot" in driver.title or "Cloudflare" in driver.title:
                print(f"{C.RED}[!] Krak blokerer vores anmodning (Bot Protection aktiv). Prøver at omgå...{C.RESET}")
                time.sleep(5)
            
            try:
                # 1. Prøv at læse direkte fra søgesiden først
                if not self._extract_profile_data(driver):
                    print(f"{C.YELLOW}[*] Data ikke åben på forsiden. Leder efter profil-links...{C.RESET}")
                    
                    # 2. Aggressiv Link-Finder (Opdateret til Kraks nye struktur)
                    links = driver.find_elements(By.TAG_NAME, "a")
                    first_name = self.name.split()[0].lower()
                    unique_links = []
                    
                    for link in links:
                        href = link.get_attribute("href")
                        # Sikrer at vi kun fanger person-profiler, der indeholder fornavnet
                        if href and "/person/" in href and "/personer" not in href:
                            if first_name in href.lower() and href not in unique_links:
                                unique_links.append(href)
                    
                    target_url = None
                    if len(unique_links) > 1:
                        print(f"\n{C.YELLOW}[!] Fandt {len(unique_links)} mulige matches på Krak:{C.RESET}")
                        for i, link in enumerate(unique_links):
                            # Forsøger at pynte på linket til display
                            display_name = link.split('/')[-1].replace('-', ' ').replace('+', ' ').title()
                            print(f"{C.CYAN}[{i+1}]{C.RESET} Mulig profil -> {display_name}")
                        
                        val = input(f"\n{C.YELLOW}Hvilken profil er den rigtige? (1-{len(unique_links)}, 0 for afbryd): {C.RESET}").strip()
                        if val.isdigit() and 0 < int(val) <= len(unique_links):
                            target_url = unique_links[int(val)-1]
                    elif len(unique_links) == 1:
                        target_url = unique_links[0]
                
                    if target_url:
                        print(f"{C.GREEN}\n    ✓ Graver dybere i valgt profil: {target_url}{C.RESET}")
                        driver.get(target_url)
                        time.sleep(3)
                        if not self._extract_profile_data(driver):
                            print(f"{C.YELLOW}    [-] Kunne ikke udtrække adressen fra profilen. Den er muligvis hemmelig.{C.RESET}")
                    else:
                        print(f"{C.RED}    [-] Ingen profil fundet for {self.name}.{C.RESET}")

            except Exception as e:
                print(f"{C.RED}    [!] Fejl under Krak-søgning: {e}{C.RESET}")
        
        self.save()
        return self.data

    def _extract_profile_data(self, driver):
        """Leder efter Telefon og Adresse på den aktuelle side"""
        success = False
        
        try:
            # Venter til der er mindst 4 tal på skærmen (Postnummer/telefon)
            WebDriverWait(driver, 5).until(
                lambda d: re.search(r'\b\d{4}\b', d.find_element(By.TAG_NAME, "body").text)
            )
        except Exception:
            pass

        # Udvinder al tekst på siden
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # --- TELEFONNUMRE ---
        phone_matches = re.findall(r'(?<!\d)(?:(?:\+45\s?)?[2-9]\d\s?\d{2}\s?\d{2}\s?\d{2})(?!\d)', body_text)
        for pm in phone_matches:
            p = pm.replace("+45", "").replace(" ", "")
            if len(p) == 8:
                formatted_p = f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}"
                if formatted_p not in self.data["Telefonnumre"]:
                    self.data["Telefonnumre"].append(formatted_p)
                    print(f"{C.GREEN}    ✓ Telefon Fundet: {formatted_p}{C.RESET}")
                    success = True

        # --- ADRESSE ---
        if not self.data.get("Ejendom"):
            lines = body_text.split('\n')
            for line in lines:
                # Leder efter "Vejnavn Nummer, 1234 By"
                match_a = re.search(r'(.*?)[,\s]+([1-9]\d{3})\s+(.*)', line)
                if match_a and len(match_a.group(1)) > 3 and any(char.isdigit() for char in match_a.group(1)):
                    vej = match_a.group(1).strip()
                    post = match_a.group(2).strip()
                    by = match_a.group(3).strip().split()[0]
                    
                    # Frasorterer støjsider og knapper
                    if "Krak" not in vej and "Ruteplan" not in vej:
                        self.data["Ejendom"] = {"Vej": vej, "Post": post, "By": by}
                        print(f"{C.GREEN}    ✓ Adresse Fundet: {vej}, {post} {by}{C.RESET}")
                        self._scrape_dingeo(driver, vej, post)
                        success = True
                        break

        return success

    def _scrape_dingeo(self, driver, vej, post):
        print(f"{C.CYAN}    [*] Angriber DinGeo.dk for: {vej}, {post}...{C.RESET}")
        search_query = urllib.parse.quote(f"{vej}, {post}")
        dingeo_url = f"https://www.dingeo.dk/adresse/{search_query.replace('%20', '-').replace(',', '')}"
        
        if safe_get_with_retry(driver, dingeo_url, max_retries=1):
            try:
                text = driver.find_element(By.TAG_NAME, "body").text
                if "BBR informationer" in text or "Salgshistorik" in text:
                    print(f"{C.GREEN}    ✓ DinGeo Data fundet!{C.RESET}")
                    self.data["DinGeo_Data"]["Link"] = dingeo_url
                    self.data["DinGeo_Data"]["Opsummering"] = text[:300] + "..." 
            except Exception: pass

    def save(self):
        has_data = bool(self.data.get("Telefonnumre")) or bool(self.data.get("Ejendom")) or bool(self.data.get("DinGeo_Data"))
        if not has_data:
            gem = input(f"\n{C.YELLOW}[?] Intet brugbart fundet. Vil du gemme rapporten alligevel? (j/n): {C.RESET}").strip().lower()
            if gem != 'j':
                print(f"{C.RED}[*] Rapport kasseret. Sparer plads.{C.RESET}")
                return

        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/01_DIRECTORY_{self.name.replace(' ', '_')}.json"
        
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        self.last_saved_file = filename
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")