# -*- coding: utf-8 -*-
"""
Modul 01: Directory & Property Intelligence
Operativ Specifikation:
- Primær dataindsamling via Search Engine Results Pages (SERP) for at omgå WAF/Cloudflare.
- Sekundær dybde-analyse af ejendomsdata (BBR, Skat, Miljø) via DinGeo.
- Zero-Disk-Footprint: Alt data holdes i RAM indtil eksplicit arkivering godkendes.
"""

import sys
import time
import json
import re
import urllib.parse
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.utils import C, session, extract_danish_phones
from core.network import safe_get_with_retry

class DirectoryIntelligenceHunter:
    
    def __init__(self, name, city=""):
        self.name = name.strip()
        self.city = city.strip()
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Datastruktur holdes i RAM
        self.data = {
            "Identitet": self.name,
            "Lokation": self.city,
            "Telefonnumre": set(),
            "Ejendom": {
                "Vej": "",
                "Post": "",
                "By": "",
                "Type": "Ukendt",
                "Koordinater": ""
            },
            "BBR_Data": {},
            "Vurdering_Skat": {},
            "Miljoe_Data": {},
            "Bofaeller": [],
            "Metadata": {
                "Scan_Tidspunkt": self.timestamp,
                "Datakilde": "SERP Extraction & DinGeo"
            }
        }

    def _log(self, level, message):
        """Klinisk standardiseret logning."""
        colors = {"INFO": C.CYAN, "WARN": C.YELLOW, "ERROR": C.RED, "SUCCESS": C.GREEN}
        color = colors.get(level, C.RESET)
        print(f"{C.DIM}[{datetime.now().strftime('%H:%M:%S')}]{C.RESET} [{color}{level}{C.RESET}] {message}")

    def run(self, driver):
        """Initierer indsamlingsprotokol."""
        print(f"\n{C.DIM}" + "-"*80 + f"{C.RESET}")
        self._log("INFO", f"Initierer person-efterforskning: {self.name}, {self.city}")
        
        try:
            driver.set_window_position(-2000, 0)
        except Exception:
            pass

        # 1. Dataindsamling (Telefon & Adresse) via Google SERP for at omgå Krak Cloudflare
        self._serp_data_extraction(driver)

        # 2. Ejendomsanalyse (Hvis adresse er identificeret)
        if self.data["Ejendom"].get("Vej"):
            self._property_deep_audit(driver)
            self._network_mapping(driver)
        else:
            self._log("WARN", "Utilstrækkelige lokationsdata. Ejendomsanalyse suspenderet.")

        # 3. Databehandling og output
        self.data["Telefonnumre"] = list(self.data["Telefonnumre"])
        self._render_tactical_report()
        self._handle_archiving()

        return self.data

    def _serp_data_extraction(self, driver):
        """
        Udtrækker Krak/DGS data direkte fra Google søgeresultater for at omgå 
        aggressive Cloudflare Turnstile blokeringer på selve platformene.
        """
        self._log("INFO", "Eksekverer SERP data extraction (Google Bypass)...")
        
        query = f'site:krak.dk OR site:degulesider.dk "{self.name}" "{self.city}"'
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        try:
            driver.get(url)
            time.sleep(2)
            
            # Håndtering af Google Cookie Consent
            try:
                consent_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(), 'Accept') or contains(text(), 'Accepter')]] | //button[@id='L2AGLb']"))
                )
                consent_btn.click()
                time.sleep(1)
            except Exception:
                pass

            # Parse DOM
            results = driver.find_elements(By.CSS_SELECTOR, "div.g")
            if not results:
                self._log("WARN", "Ingen resultater identificeret i SERP index.")
                return

            for result in results:
                text = result.text
                
                # Ekstraher telefonnumre fra snippet
                phones = extract_danish_phones(text)
                for p in phones:
                    self.data["Telefonnumre"].add(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}")
                
                # Ekstraher adresse fra titel/snippet
                if not self.data["Ejendom"].get("Vej"):
                    # Mønster der fanger 'Vejnavn 12A, 8000 By'
                    addr_match = re.search(r'([A-ZÆØÅa-zæøå\s\.\-]+?\s\d+[A-Z0-9a-z\s,]*?)[\s,]+(\d{4})\s+([A-ZÆØÅa-zæøå\s\-]+)', text)
                    if addr_match:
                        vej = addr_match.group(1).strip().strip(',')
                        if any(c.isdigit() for c in vej):
                            self.data["Ejendom"]["Vej"] = vej
                            self.data["Ejendom"]["Post"] = addr_match.group(2).strip()
                            self.data["Ejendom"]["By"] = addr_match.group(3).strip()
                            self._log("SUCCESS", f"Adresse bekræftet: {vej}, {self.data['Ejendom']['Post']} {self.data['Ejendom']['By']}")

        except Exception as e:
            self._log("ERROR", f"SERP extraction fejlede: {str(e)}")

    def _property_deep_audit(self, driver):
        """Indhenter BBR, skatte- og miljødata fra offentlige og semi-offentlige registre."""
        self._log("INFO", "Eksekverer dybdegående ejendomsanalyse...")
        
        vej = self.data["Ejendom"]["Vej"].split(',')[0].strip()
        post = self.data["Ejendom"]["Post"]
        by = self.data["Ejendom"]["By"].split(' ')[0].strip()
        
        slug_city = f"{post}-{by}".lower().replace("æ","ae").replace("ø","oe").replace("å","aa")
        slug_street = vej.lower().replace(" ","-").replace("æ","ae").replace("ø","oe").replace("å","aa").replace(".","")
        base_url = f"https://www.dingeo.dk/adresse/{slug_city}/{slug_street}"

        # Definerer moduler og deres tilhørende parser-funktion
        audit_modules = {
            "BBR": ("", self._parse_bbr),
            "Skat": ("/skat/", self._parse_tax),
            "Vurdering": ("/vurdering/", self._parse_value),
            "Miljø": ("/miljoe/", self._parse_env)
        }

        for module_name, (path, parser_func) in audit_modules.items():
            try:
                driver.get(base_url + path)
                time.sleep(1.5)
                
                if "verify you are human" in driver.page_source.lower():
                    self._log("WARN", f"WAF blokering detekteret på modul: {module_name}. Springer over.")
                    continue
                
                body_text = driver.find_element(By.TAG_NAME, "body").text
                lines = [line.strip() for line in body_text.split('\n') if line.strip()]
                
                parser_func(lines, body_text.lower())
                
            except Exception as e:
                self._log("ERROR", f"Analyse af {module_name} mislykkedes.")

    def _parse_bbr(self, lines, body_lower):
        for i, l in enumerate(lines):
            for key in ["Opførselsesår", "Antal værelser", "Etageareal", "Boligtype", "Anvendelse"]:
                if l == key and i+1 < len(lines):
                    self.data["BBR_Data"][key] = lines[i+1]

    def _parse_tax(self, lines, body_lower):
        for i, l in enumerate(lines):
            if "Boligskat 2024" in l: self.data["Vurdering_Skat"]["Skat_2024"] = lines[i+1]
            if "Grundskyld" in l: self.data["Vurdering_Skat"]["Grundskyld"] = lines[i+1]

    def _parse_value(self, lines, body_lower):
        for i, l in enumerate(lines):
            if "Dingestimat" in l: self.data["Vurdering_Skat"]["Estimeret_Værdi"] = lines[i+1]
            if "Seneste salgspris" in l: self.data["Vurdering_Skat"]["Seneste_Salg"] = lines[i+1]

    def _parse_env(self, lines, body_lower):
        if "støj" in body_lower: self.data["Miljoe_Data"]["Støjniveau"] = "Data tilgængelig"
        if "oversvømmelse" in body_lower: self.data["Miljoe_Data"]["Oversvømmelsesrisiko"] = "Tjek manuelt"
        if "radon" in body_lower: self.data["Miljoe_Data"]["Radonrisiko"] = "Data tilgængelig"

    def _network_mapping(self, driver):
        """Identificerer potentielle bofæller via adressesøgning på SERP."""
        self._log("INFO", "Kortlægger relationer på adressen...")
        vej = self.data["Ejendom"]["Vej"].split(',')[0].strip()
        query = f'site:krak.dk "{vej}" "{self.data["Ejendom"]["Post"]}"'
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        try:
            driver.get(url)
            time.sleep(2)
            results = driver.find_elements(By.CSS_SELECTOR, "div.g")
            for res in results:
                title = res.text.split('\n')[0]
                name_match = title.split('-')[0].strip()
                if name_match and self.name.lower() not in name_match.lower() and "Krak" not in name_match:
                    if name_match not in self.data["Bofaeller"]:
                        self.data["Bofaeller"].append(name_match)
        except Exception:
            pass

    def _render_tactical_report(self):
        """Udskriver data klinisk i terminalen uden at skrive til disken."""
        print(f"\n{C.BOLD}=== INTELLIGENCE RAPPORT: {self.name.upper()} ==={C.RESET}")
        
        tlf = ", ".join(self.data["Telefonnumre"]) if self.data["Telefonnumre"] else "Ingen data"
        print(f"{C.CYAN}Telefonnumre:{C.RESET} {tlf}")
        
        ejd = self.data["Ejendom"]
        addr = f"{ejd.get('Vej', '')}, {ejd.get('Post', '')} {ejd.get('By', '')}".strip(" ,")
        print(f"{C.CYAN}Adresse:{C.RESET}      {addr if addr else 'Ingen data'}")
        
        bbr = self.data["BBR_Data"]
        if bbr:
            print(f"{C.CYAN}BBR Data:{C.RESET}")
            for k, v in bbr.items():
                print(f"  - {k}: {v}")
                
        skat = self.data["Vurdering_Skat"]
        if skat:
            print(f"{C.CYAN}Økonomi:{C.RESET}")
            for k, v in skat.items():
                print(f"  - {k}: {v}")

        if self.data["Bofaeller"]:
            print(f"{C.CYAN}Bofæller/Netværk:{C.RESET}")
            for b in self.data["Bofaeller"]:
                print(f"  - {b}")

        print(f"{C.DIM}--------------------------------------------------{C.RESET}")

    def _handle_archiving(self):
        """Operatør-godkendelse til arkivering (Zero-Disk Footprint by default)."""
        save_choice = input(f"\n{C.YELLOW}[?] Arkiver rapport til disk? (j/n): {C.RESET}").lower()
        if save_choice == 'j':
            folder = session.get("loot_folder", "loot_evidence")
            os.makedirs(folder, exist_ok=True)
            path = f"{folder}/01_DIRECTORY_{self.name.replace(' ', '_')}.json"
            
            if os.path.exists(path):
                os.remove(path)
                
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            self._log("SUCCESS", f"Data sikret: {path}")
        else:
            self._log("INFO", "Data slettet fra RAM. Ingen spor efterladt.")

# Nødvendige aliaser for main.py integration (Forhindrer "name is not defined" fejl)
DirectoryIntelligenceHunter = DirectoryIntelligenceHunter
KrakIntelligenceAnalyst = DirectoryIntelligenceHunter