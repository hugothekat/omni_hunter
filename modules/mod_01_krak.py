# -*- coding: utf-8 -*-
import sys
import time
import json
import os
import re
import urllib.parse
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.utils import C, session, extract_danish_phones
from core.network import safe_get_with_retry, omni_dork_search

class DirectoryIntelligenceHunter:
    
    def __init__(self, name, city=""):
        self.name = name.strip()
        self.city = city.strip()
        self.start_time = datetime.now()
        
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
            "DinGeo_Intelligence": {
                "BBR_Stamdata": {},
                "Vurdering": {},
                "Skat": {},
                "Dokumenter": {},
                "Infrastruktur": {},
                "Miljø_Risici": {},
                "Nabolag_Profil": {}
            },
            "Bofæller_Netværk": [],
            "Metadata": {
                "Timestamp": self.start_time.isoformat(),
                "Software": "GOLIATH V28",
                "Bypass_Method": "Native Google SERP Extraction"
            }
        }

    def _log(self, message, color=C.CYAN):
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r{C.DIM}[{ts}]{C.RESET} {color}{message}{C.RESET}\n")

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.write(f"{C.MAGENTA}[*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        print(f"\n{C.WHITE}{'='*80}{C.RESET}")
        print(f"{C.WHITE} MODULE 01: DIRECTORY & PROPERTY INTELLIGENCE (V28){C.RESET}")
        print(f"{C.WHITE}{'='*80}{C.RESET}")
        self._log(f"Target: {self.name} | Location: {self.city}", C.YELLOW)

        try:
            driver.set_window_position(-2000, 0)
        except Exception:
            pass

        self._update_progress(10, "Executing Native Google SERP Strike")
        self._google_serp_strike(driver)

        if not self.data["Ejendom"].get("Vej"):
            self._update_progress(30, "Fallback: Standard Search Engine Dorking")
            self._fallback_dorking(driver)

        if self.data["Ejendom"].get("Vej"):
            self._update_progress(60, f"Initiating DinGeo Deep-Audit ({self.data['Ejendom']['Vej']})")
            self._juggernaut_dingeo_engine(driver)
            
            self._update_progress(85, "Mapping Cohabitants via Network Query")
            self._find_cohabitants(driver)
        else:
            self._log("Insufficient location data. DinGeo audit bypassed.", C.RED)

        self._update_progress(100, "Intelligence gathering complete")
        self.data["Telefonnumre"] = list(self.data["Telefonnumre"])
        
        self._print_dashboard()
        
        choice = input(f"\n{C.YELLOW}[?] Archive intelligence report to disk? (y/n): {C.RESET}").lower()
        if choice in ['y', 'j', 'yes', 'ja']:
            self.save()
        else:
            self._log("Data purged from RAM.", C.DIM)

        return self.data

    def _google_serp_strike(self, driver):
        """Native Google search implementation to bypass missing engines in core.network"""
        query = f'site:krak.dk OR site:degulesider.dk "{self.name}" "{self.city}"'
        url = f"https://www.google.dk/search?q={urllib.parse.quote(query)}"
        
        try:
            driver.get(url)
            time.sleep(1.5)
            
            # Handle Google Consent
            try:
                consent = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='L2AGLb'] | //button[.//div[text()='Accepter alle']]"))
                )
                driver.execute_script("arguments[0].click();", consent)
                time.sleep(1)
            except Exception:
                pass

            # Parse SERP Elements
            elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
            for el in elements:
                text = el.text
                
                for phone in extract_danish_phones(text):
                    self.data["Telefonnumre"].add(f"{phone[:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]}")
                
                # Regex targetting standard Danish address format and Krak snippet structure
                match = re.search(r'([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\.\-]+?\s\d+[A-Z0-9a-z]*?)\s*,\s*(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\-]+)', text)
                if match and not self.data["Ejendom"].get("Vej"):
                    vej = match.group(1).strip()
                    if any(c.isdigit() for c in vej) and "område" not in vej.lower():
                        self.data["Ejendom"]["Vej"] = vej
                        self.data["Ejendom"]["Post"] = match.group(2).strip()
                        self.data["Ejendom"]["By"] = match.group(3).strip()
                        self._log(f"SERP Address Confirmed: {vej}, {match.group(2)}", C.GREEN)

        except Exception as e:
            self._log(f"Google SERP Strike encountered an error: {e}", C.RED)

    def _fallback_dorking(self, driver):
        """Fallback to core network omni_dork (DDG/Bing/Yahoo)"""
        dork = f'(site:krak.dk OR site:degulesider.dk) "{self.name}" "{self.city}"'
        hits = omni_dork_search(driver, dork, max_links=5)
        
        for hit in hits:
            full_text = f"{hit.get('title','')} {hit.get('snippet','')}"
            for p in extract_danish_phones(full_text):
                self.data["Telefonnumre"].add(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}")
            
            match = re.search(r'([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\.\-]+?\s\d+[A-Z0-9a-z]*?)\s*,\s*(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\-]+)', full_text)
            if match and not self.data["Ejendom"].get("Vej"):
                vej = match.group(1).strip()
                if any(c.isdigit() for c in vej) and "område" not in vej.lower():
                    self.data["Ejendom"]["Vej"] = vej
                    self.data["Ejendom"]["Post"] = match.group(2).strip()
                    self.data["Ejendom"]["By"] = match.group(3).strip()
                    self._log(f"Fallback Address Confirmed: {vej}, {match.group(2)}", C.GREEN)

    def _juggernaut_dingeo_engine(self, driver):
        """Modular data extraction from DinGeo"""
        vej_clean = self.data["Ejendom"]["Vej"].split(',')[0].strip()
        post = self.data["Ejendom"]["Post"]
        by_clean = self.data["Ejendom"]["By"].split(' ')[0].strip()
        
        slug_c = f"{post}-{by_clean}".lower().replace("æ","ae").replace("ø","oe").replace("å","aa")
        slug_v = vej_clean.lower().replace(" ","-").replace("æ","ae").replace("ø","oe").replace("å","aa").replace(".","")
        base = f"https://www.dingeo.dk/adresse/{slug_c}/{slug_v}"

        endpoints = {
            "BBR_Stamdata": "",
            "Skat": "/skat/",
            "Vurdering": "/vurdering/",
            "Infrastruktur": "/internet-mobil/",
            "Miljø_Risici": "/miljoe/",
            "Nabolag": "/nabolag/"
        }

        for key, path in endpoints.items():
            try:
                if safe_get_with_retry(driver, base + path, max_retries=1):
                    time.sleep(1.5)
                    
                    if "verify you are human" in driver.page_source.lower():
                        continue

                    lines = [l.strip() for l in driver.find_element(By.TAG_NAME, "body").text.split('\n') if l.strip()]
                    body_lower = driver.page_source.lower()
                    
                    if key == "BBR_Stamdata":
                        for i, l in enumerate(lines):
                            for k in ["Opførselsesår", "Antal værelser", "Etageareal", "Boligtype", "Varmeinstallation"]:
                                if l == k and i+1 < len(lines): self.data["DinGeo_Intelligence"][key][k] = lines[i+1]
                    
                    elif key == "Skat":
                        for i, l in enumerate(lines):
                            if "Boligskat 2024" in l: self.data["DinGeo_Intelligence"][key]["Skat_2024"] = lines[i+1]
                            if "Grundskyld" in l: self.data["DinGeo_Intelligence"][key]["Grundskyld"] = lines[i+1]
                            
                    elif key == "Vurdering":
                        for i, l in enumerate(lines):
                            if "Dingestimat" in l: self.data["DinGeo_Intelligence"][key]["Dingestimat"] = lines[i+1]
                            if "Seneste salgspris" in l: self.data["DinGeo_Intelligence"][key]["Seneste_Salg"] = lines[i+1]
                    
                    elif key == "Infrastruktur":
                        if "fibernet" in body_lower: self.data["DinGeo_Intelligence"][key]["Fiber"] = "Ja"
                        if "5g" in body_lower: self.data["DinGeo_Intelligence"][key]["5G"] = "Ja"
                        
                    elif key == "Miljø_Risici":
                        if "støj" in body_lower: self.data["DinGeo_Intelligence"][key]["Støj_Niveau"] = "Data registreret"
                        if "oversvømmelse" in body_lower: self.data["DinGeo_Intelligence"][key]["Oversvømmelse_Risiko"] = "Data registreret"

                    elif key == "Nabolag":
                        for i, l in enumerate(lines):
                            if "bor i" in l.lower() and "naboer" in body_lower:
                                self.data["DinGeo_Intelligence"]["Nabolag_Profil"]["Demografi"] = l + " " + (lines[i+1] if i+1 < len(lines) else "")

            except Exception:
                pass

    def _find_cohabitants(self, driver):
        vej = self.data["Ejendom"].get("Vej", "")
        if not vej: return
        addr = vej.split(',')[0].strip()
        
        for hit in omni_dork_search(driver, f'site:krak.dk "{addr}" "{self.data["Ejendom"]["Post"]}"', max_links=4):
            n = hit.get('title', '').split('-')[0].strip()
            if n and self.name.lower() not in n.lower() and "Krak" not in n:
                if n not in self.data["Bofæller_Netværk"]:
                    self.data["Bofæller_Netværk"].append(n)

    def _print_dashboard(self):
        print(f"\n{C.WHITE}[+] INTELLIGENCE SUMMARY: {self.name.upper()}{C.RESET}")
        
        t_list = ", ".join(self.data["Telefonnumre"]) if self.data["Telefonnumre"] else "INGEN FUNDET"
        print(f"    Telefoner: {C.GREEN}{t_list}{C.RESET}")
        
        addr = f"{self.data['Ejendom'].get('Vej', '')}, {self.data['Ejendom'].get('Post', '')} {self.data['Ejendom'].get('By', '')}".strip(" ,")
        print(f"    Adresse:   {C.GREEN}{addr if addr else 'INGEN FUNDET'}{C.RESET}")
        
        bbr = self.data["DinGeo_Intelligence"]["BBR_Stamdata"]
        if bbr:
            print(f"    BBR Data:  {C.CYAN}Opført {bbr.get('Opførselsesår', 'N/A')} | {bbr.get('Boligtype', 'N/A')} | {bbr.get('Etageareal', 'N/A')}{C.RESET}")
            print(f"    Vurdering: {C.CYAN}{self.data['DinGeo_Intelligence']['Vurdering'].get('Seneste_Salg', 'Ukendt')}{C.RESET}")
            
        if self.data["Bofæller_Netværk"]:
            print(f"    Netværk:   {C.MAGENTA}{', '.join(self.data['Bofæller_Netværk'])}{C.RESET}")

        print(f"{C.DIM}" + "-"*80 + f"{C.RESET}")

    def save(self):
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        path = f"{session.get('loot_folder', 'loot_evidence')}/01_DIRECTORY_{self.name.replace(' ', '_')}.json"
        
        try:
            if os.path.exists(path): os.remove(path)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
            self._log(f"Report securely archived: {path}", C.GREEN)
        except Exception as e:
            self._log(f"Failed to archive report: {e}", C.RED)

DirectoryIntelligenceHunter = DirectoryIntelligenceHunter
KrakIntelligenceAnalyst = DirectoryIntelligenceHunter