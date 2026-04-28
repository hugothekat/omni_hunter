# -*- coding: utf-8 -*-
import os
import json
import re
import time
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from core.utils import C, session
from core.network import safe_get_with_retry, omni_dork_search # NY V8 TILFØJELSE: omni_dork_search
from core.browser import zap_cookies

class VehicleIntelligence:
    def __init__(self, reg_nr):
        self.reg = reg_nr.upper().replace(" ", "").replace("-", "")
        self.data = {
            "RegNr": self.reg, 
            "Mærke_Model": "", 
            "Stelnummer": "", 
            "Status": "", 
            "Gæld_Pant": "Ukendt",           # NY V8 TILFØJELSE
            "Kilometerstand": "Ukendt",      # NY V8 TILFØJELSE
            "Forsikring": "Ukendt",          # NY V8 TILFØJELSE
            "Tidligere_Salgsannoncer": [],   # NY V8 TILFØJELSE (Bilbasen, DBA)
            "Direct_OSINT_Links": {},        # NY V8 TILFØJELSE
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[20] Køretøjs-Efterretning (Gæld, Pant & Annonce-Dorking V8)\n{'='*60}{C.RESET}")
        print(f"[*] Slår nummerplade op: {self.reg}")

        # --- NY V8 TILFØJELSE: OSINT genveje ---
        self._generate_osint_links()

        url = f"https://www.tjekbil.dk/nummerplade/{self.reg}/overblik"
        if safe_get_with_retry(driver, url):
            zap_cookies(driver)
            time.sleep(2)
            try:
                # Cookie/Consent clicker for at undgå blokeret DOM
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["tillad", "accept", "forstået", "ok"]):
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1)
                            break
                except: pass

                body_text = driver.find_element(By.TAG_NAME, "body").text
                
                # 1. Stelnummer
                stel_match = re.search(r'(?i)(?:stelnummer|vin)[:\s]+([A-Z0-9]{17})', body_text)
                if stel_match:
                    self.data["Stelnummer"] = stel_match.group(1)
                    print(f"{C.GREEN}    ✓ Stelnummer (VIN) fundet: {self.data['Stelnummer']}{C.RESET}")
                    # NY V8 TILFØJELSE: VIN Decode Link
                    self.data["Direct_OSINT_Links"]["VIN_Decoder"] = f"https://www.vindecoderz.com/EN/check-lookup/{self.data['Stelnummer']}"

                # 2. Mærke & Model
                try:
                    h1 = driver.find_element(By.TAG_NAME, "h1").text
                    self.data["Mærke_Model"] = h1.replace("Tjekbil", "").strip()
                    print(f"{C.GREEN}    ✓ Køretøj: {self.data['Mærke_Model']}{C.RESET}")
                except Exception: pass

                # 3. Status
                if "Afgemeldt" in body_text or "Afmeldt" in body_text:
                    self.data["Status"] = "Afmeldt"
                else:
                    self.data["Status"] = "Aktiv"
                print(f"{C.GREEN}    ✓ Status: {self.data['Status']}{C.RESET}")

                # --- NYE V8 EKSTRAKTIONER ---
                
                # 4. Gæld og Pant i bilen (Økonomisk Intel)
                if re.search(r'(?i)(?:restgæld|pant|tinglysning)[\s:]+(ja|[1-9]\d*\s*kr)', body_text) or "Der er tinglyst gæld" in body_text:
                    self.data["Gæld_Pant"] = "Gæld Registreret!"
                    print(f"{C.RED}    🔥 ØKONOMI ADVARSEL: Der er tinglyst gæld i køretøjet!{C.RESET}")
                else:
                    self.data["Gæld_Pant"] = "Ingen Gæld"
                    print(f"{C.GREEN}    ✓ Økonomi: Ingen tinglyst gæld fundet.{C.RESET}")

                # 5. Kilometerstand
                km_match = re.search(r'(?i)(?:kilometerstand|kørt)[:\s]+([\d\.]+)\s*km', body_text)
                if km_match:
                    self.data["Kilometerstand"] = km_match.group(1) + " km"
                    print(f"{C.CYAN}    ✓ Kilometerstand: {self.data['Kilometerstand']}{C.RESET}")

                # 6. Forsikringsselskab
                fors_match = re.search(r'(?i)(?:forsikringsselskab|forsikret hos)[:\s]+([A-Za-zÆØÅæøå\s]+)', body_text)
                if fors_match:
                    selskab = fors_match.group(1).strip().split('\n')[0]
                    if len(selskab) > 2 and selskab.lower() not in ["ukendt", "ikke oplyst"]:
                        self.data["Forsikring"] = selskab
                        print(f"{C.CYAN}    ✓ Forsikring: {self.data['Forsikring']}{C.RESET}")

            except Exception as e:
                print(f"{C.YELLOW}    [-] Kunne ikke udtrække alt data automatisk. Tjek manuelt: {url}{C.RESET}")
        else:
            print(f"{C.RED}    [-] Kunne ikke forbinde til motor-registret.{C.RESET}")

        # --- NY V8: DORKING EFTER HISTORISKE SALGSANNONCER ---
        self._dork_vehicle_history(driver)

        self.save()

    def _generate_osint_links(self):
        """NY V8 TILFØJELSE: Genererer genveje til manuelle opslag og tinglysning API'er"""
        print(f"{C.YELLOW}[*] Genererer Tinglysning og Motorregister Links...{C.RESET}")
        self.data["Direct_OSINT_Links"]["TjekBil"] = f"https://www.tjekbil.dk/nummerplade/{self.reg}/overblik"
        self.data["Direct_OSINT_Links"]["NummerpladeNet"] = f"https://nummerplade.net/nummerplade/{self.reg}.html"
        self.data["Direct_OSINT_Links"]["Tinglysning"] = f"https://www.tinglysning.dk/tinglysning/rest/forespoergsel/bilbogen/nummerplade/{self.reg}"
        
        print(f"{C.CYAN}    -> Auto-Tinglysning Link: {self.data['Direct_OSINT_Links']['Tinglysning']}{C.RESET}")

    def _dork_vehicle_history(self, driver):
        """NY V8 TILFØJELSE: Søger på DBA, Bilbasen og Bilgalleri for at finde gamle annoncer med ejerens data"""
        print(f"\n{C.YELLOW}[*] Dorking Web History: Leder efter gamle salgsannoncer for pladen...{C.RESET}")
        if not driver: return

        dork = f'"{self.reg}" site:bilbasen.dk OR site:dba.dk OR site:bilgalleri.dk OR site:bilsalg.dk'
        links = omni_dork_search(driver, dork, max_links=3)

        if links:
            for link in links:
                url = link['url']
                title = link.get('title', '')
                print(f"{C.GREEN}    🔥 HISTORISK SPOR FUNDET: {url[:80]}{C.RESET}")
                
                if url not in self.data["Tidligere_Salgsannoncer"]:
                    self.data["Tidligere_Salgsannoncer"].append({"Titel": title, "URL": url})
        else:
            print(f"{C.DIM}    [-] Ingen historiske salgsannoncer fundet for {self.reg}.{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/20_VEHICLE_{self.reg}.json"
        
        # NY V8 TILFØJELSE: Sikker overskrivning af rapporten
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")