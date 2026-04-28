# -*- coding: utf-8 -*-

import sys
import time
import json
import os
import re
import random
import urllib.parse
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from core.utils import C, session, extract_danish_phones
from core.network import safe_get_with_retry, omni_dork_search

class DirectoryIntelligenceHunter:
    
    def __init__(self, name, city=""):
        self.name = name.strip()
        self.city = city.strip()
        self.start_time = datetime.now()
        self.keep_screenshots = False 
        self.operator_id = os.getlogin() if hasattr(os, 'getlogin') else "Hugo"
        
        self.data = {
            "Identitet": self.name,
            "Lokation": self.city,
            "Telefonnumre": set(),
            "Ejendom": {
                "Vej": "",
                "Post": "",
                "By": "",
                "Type": "Ukendt",
                "Koordinater": "",
                "BBR_ID": "",
                "Etage_Dør": ""
            },
            "DinGeo_Intelligence": {
                "BBR_Stamdata": {},
                "Vurdering": {
                    "Dingestimat": "Ikke fundet", 
                    "Seneste_Salg": "Ukendt",
                    "Salgs_Historik": [],
                    "Kvadratmeterpris": ""
                },
                "Skat": {
                    "Ejendomsskat": "Ukendt", 
                    "Grundskyld": "Ukendt", 
                    "Skat_2024": "",
                    "Skat_2025_Est": ""
                },
                "Dokumenter": {
                    "Byggesager": "Ingen fundet", 
                    "Servitutter": "0", 
                    "Energimærke": "Ukendt",
                    "BBR_Meddelelse": "Link mangler"
                },
                "Infrastruktur": {
                    "Fiber": "Nej", 
                    "5G": "Nej", 
                    "Internet_Udbydere": [],
                    "Mobil_Dækning": "Ukendt"
                },
                "Miljø_Risici": {
                    "Støj_Niveau": "Ukendt",
                    "Oversvømmelse_Risiko": "Ukendt",
                    "Radon_Risiko": "Ukendt",
                    "Indbruds_Statistik": "Ukendt"
                },
                "Nabolag_Profil": {
                    "Demografi": "Ukendt",
                    "Uddannelses_Niveau": "Ukendt",
                    "Indkomst_Gennemsnit": "Ukendt"
                }
            },
            "Bofæller_Netværk": [],
            "Maps_Links": [],
            "Screenshots": [],
            "Metadata": {
                "Timestamp": self.start_time.isoformat(),
                "Software": "GOLIATH V25 OMEGA SPECTRE",
                "Operatør": self.operator_id,
                "Confidence_Score": 0,
                "Shadow_Bypass_Active": False
            }
        }

    def _log(self, message, color=C.CYAN):
        """Taktisk logging med høj præcision."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{C.DIM}[{ts}]{C.RESET} {color}{message}{C.RESET}")

    def _update_progress(self, pct, message):
        """Visuel status-opdatering for operatøren."""
        sys.stdout.write("\r" + " " * 115 + "\r")
        sys.stdout.write(f"{C.MAGENTA}    [SPECTRE-V25] {message}... {C.BOLD}{pct}%{C.RESET}")
        sys.stdout.flush()

    def _operator_clearance(self):
        """Håndterer operatør-godkendelser før start."""
        print(f"\n{C.YELLOW}[!] KRÆVER OPERATØR-GODKENDELSE ( {self.operator_id} ){C.RESET}")
        choice = input(f"{C.CYAN}    > Skal systemet sikre screenshots som bevismateriale? (j/n): {C.RESET}").lower()
        self.keep_screenshots = True if choice == 'j' else False
        self._log(f"Visual Evidence Capture: {'ENABLED' if self.keep_screenshots else 'DISABLED'}", C.DIM)

    def run(self, driver):
        """Hovedoperationens eksekverings-logik."""
        from core.browser import zap_cookies, human_scroll
        
        print(f"\n{C.BG_RED}{C.WHITE} {'='*110} {C.RESET}")
        print(f"{C.BG_RED}{C.WHITE} ) {'='*47} {C.RESET}")
        self._log(f"Infiltration initieret på: {self.name} i {self.city}", C.YELLOW)

        # 1. INITIAL CLEARANCE
        self._operator_clearance()

        try:
            driver.set_window_position(-2000, 0)
            os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        except: pass

        # --- FASE 1: GHOST ENGINE SNIPING (Pre-emptive Strike) ---
        self._update_progress(10, "Aktiverer DuckDuckGo Ghost Engine")
        self._shadow_serp_sniper_ddg(driver)

        self._update_progress(25, "Scanner Google/Bing Snippet Cache")
        self._stealth_snippet_engine(driver)

        # --- FASE 2: DIREKTE INFILTRATION (Krak/DGS) ---
        self._update_progress(45, "Forsøger Direkte Sitet-Infiltration (Krak/DGS)")
        self._perform_direct_infiltration(driver, zap_cookies)

        # --- FASE 3: DINGEO JUGGERNAUT (Deep Real Estate Audit) ---
        if self.data["Ejendom"].get("Vej"):
            self._update_progress(70, f"Deep-Scanning Ejendom: {self.data['Ejendom']['Vej']}")
            self._juggernaut_dingeo_engine(driver)
            
            self._update_progress(90, "Kortlægger Sociale Netværks-relationer")
            self._discover_cohabitants(driver)
            self._generate_map_links()
        else:
            self._log("Ingen adresse fundet. DinGeo Deep-Audit deaktiveret.", C.RED)

        # 4. OPERATIONEL OPSAMLING & ARKIVERING
        self._update_progress(100, "Infiltration Fuldført")
        self.data["Telefonnumre"] = list(self.data["Telefonnumre"])
        self._calculate_confidence()
        
        print(f"\n{C.CYAN}--- OPERATIONEL RAPPORT: {self.name} ---{C.RESET}")
        print(f"    [+] Telefoner: {len(self.data['Telefonnumre'])}")
        print(f"    [+] Adresse:   {self.data['Ejendom'].get('Vej', 'IKKE FUNDET')}")
        print(f"    [+] BBR-Data:  {'KOMPLET' if self.data['DinGeo_Intelligence']['BBR_Stamdata'] else 'MANGELDE'}")
        print(f"    [+] Sikkerhed: {self.data['Metadata']['Confidence_Score']}%")
        
        save_choice = input(f"\n{C.GREEN}[?] Skal denne rapport arkiveres i loot-mappen? (j/n): {C.RESET}").lower()
        if save_choice == 'j':
            self.save()
        else:
            self._log("Operatør valgte at kassere rapport. Rydder op...", C.RED)
            if self.keep_screenshots:
                for s in self.data["Screenshots"]:
                    try: os.remove(s)
                    except: pass
        
        print(f"\n{C.GREEN}[✓] Operatør {self.operator_id} afsluttede missionen succesfuldt.{C.RESET}\n")
        return self.data

    def _shadow_serp_sniper_ddg(self, driver):
        """DuckDuckGo Shadow Sniper: Trækker data udenom Cloudflare."""
        search_query = f'"{self.name}" {self.city} site:krak.dk'
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(search_query)}&ia=web"
        
        if safe_get_with_retry(driver, url):
            time.sleep(random.uniform(2, 3))
            try:
                results = driver.find_elements(By.CSS_SELECTOR, "li[data-layout='organic']")
                for res in results:
                    txt = res.text
                    for phone in extract_danish_phones(txt):
                        self.data["Telefonnumre"].add(f"{phone[:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]}")
                    
                    if not self.data["Ejendom"].get("Vej"):
                        m = re.search(r'([A-Zæøåa-z\s\-]+\s\d+[A-Z0-9]*),\s*(\d{4})', txt)
                        if m:
                            self.data["Ejendom"]["Vej"] = m.group(1).strip()
                            self.data["Ejendom"]["Post"] = m.group(2).strip()
                            self.data["Ejendom"]["By"] = self.city
                            self._log(f"Shadow Sniper (DDG) verificerede adresse: {self.data['Ejendom']['Vej']}", C.GREEN)
                            self.data["Metadata"]["Shadow_Bypass_Active"] = True
            except: pass

    def _stealth_snippet_engine(self, driver):
        """Mining af Google/Bing cacher via dorking."""
        dork = f'(site:krak.dk OR site:degulesider.dk) "{self.name}" {self.city}'
        hits = omni_dork_search(driver, dork, max_links=5)
        for hit in hits:
            full_txt = f"{hit.get('title','')} {hit.get('snippet','')}"
            for p in extract_danish_phones(full_txt):
                self.data["Telefonnumre"].add(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}")
            
            if " - " in hit.get('title', ''):
                parts = hit['title'].split(" - ")
                addr_p = parts[-1]
                m = re.search(r'(.*?),\s*(\d{4})\s*(.*)', addr_p)
                if m and not self.data["Ejendom"].get("Vej"):
                    self.data["Ejendom"]["Vej"] = m.group(1).strip()
                    self.data["Ejendom"]["Post"] = m.group(2).strip()
                    self.data["Ejendom"]["By"] = m.group(3).strip()

    def _perform_direct_infiltration(self, driver, zap_cookies):
        """Direkte adgang til Krak/DGS med Victoria-Sniper DOM-targeting."""
        q = f"{self.name} {self.city}".strip().replace(" ", "+").lower()
        targets = {
            "Krak": f"https://www.krak.dk/{q}/personer",
            "DGS": f"https://www.degulesider.dk/{q}/personer"
        }

        for p_name, url in targets.items():
            self._log(f"Forbinder til {p_name} med Referer-Spoofing...", C.DIM)
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Referer': 'https://www.google.dk/'}})
            
            if safe_get_with_retry(driver, url):
                zap_cookies(driver)
                time.sleep(random.uniform(3, 5))
                
                if "security verification" in driver.page_source.lower() or "cloudflare" in driver.page_source.lower():
                    self._log(f"Cloudflare blokerer {p_name}! Springer til næste lag.", C.RED)
                    continue

                try:
                    self._parse_result_cards_precisely(driver)
                    
                    links = driver.find_elements(By.TAG_NAME, "a")
                    target_url = None
                    pattern = rf'https://www\.(?:krak|degulesider)\.dk/.*/\d+/person'
                    
                    for link in links:
                        href = link.get_attribute("href")
                        if href and re.search(pattern, href):
                            target_url = href; break
                    
                    if target_url:
                        self._log(f"Eksklusiv profil-node fundet: {target_url}", C.DIM)
                        driver.get(target_url)
                        time.sleep(random.uniform(3, 5))
                        self._extract_profile_data_deep(driver)
                        
                    if self.keep_screenshots:
                        path = f"{session['loot_folder']}/01_{p_name}_{self.name.replace(' ', '_')}.png"
                        driver.save_screenshot(path); self.data["Screenshots"].append(path)
                        
                except Exception as e:
                    self._log(f"Infiltrations-fejl på {p_name}: {e}", C.RED)

    def _parse_result_cards_precisely(self, driver):
        """Victoria-Sniper 5.5: DOM-Container målrettet data-fangst."""
        try:
            containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'ResultsCard')] | //article")
            for card in containers:
                text = card.text
                if self.name.split(' ')[0].lower() in text.lower():
                    addr_match = re.search(r'([A-Zæøåa-z\s\.\-]+?\s\d+[A-Z0-9a-z\s,]*),\s*(\d{4})\s+([A-Zæøåa-z\s\-]+)', text)
                    if addr_match and not self.data["Ejendom"].get("Vej"):
                        raw_v = addr_match.group(1).strip()
                        self.data["Ejendom"]["Vej"] = raw_v.split('\n')[-1].strip().strip(',')
                        self.data["Ejendom"]["Post"] = addr_match.group(2).strip()
                        self.data["Ejendom"]["By"] = addr_match.group(3).strip()
                        self._log(f"DOM-Sniper fangede adresse: {self.data['Ejendom']['Vej']}", C.GREEN)

                    try:
                        btns = card.find_elements(By.TAG_NAME, "button")
                        for b in btns:
                            if "vis" in b.text.lower() or any(c.isdigit() for c in b.text):
                                driver.execute_script("arguments[0].click();", b)
                                time.sleep(0.5)
                    except: pass
            
            body_txt = driver.find_element(By.TAG_NAME, "body").text
            for p in extract_danish_phones(body_txt):
                self.data["Telefonnumre"].add(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}")
        except: pass

    def _extract_profile_data_deep(self, driver):
        """Udtrækker alt fra selve /person/ dybdeprofilen."""
        try:
            body = driver.find_element(By.TAG_NAME, "body").text
            for p in extract_danish_phones(body):
                self.data["Telefonnumre"].add(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}")
                
            gps_match = re.search(r'(\d+\.\d+,\s*\d+\.\d+)', body)
            if gps_match: self.data["Ejendom"]["Koordinater"] = gps_match.group(1)
            
            if "villa" in body.lower() or "parcelhus" in body.lower(): self.data["Ejendom"]["Type"] = "Villa"
            elif "lejlighed" in body.lower(): self.data["Ejendom"]["Type"] = "Lejlighed"
        except: pass

    def _juggernaut_dingeo_engine(self, driver):
        """DinGeo Juggernaut: Den ultimative ejendomsanalyse."""
        vej = self.data["Ejendom"]["Vej"]
        post = self.data["Ejendom"]["Post"]
        by_clean = self.data["Ejendom"]["By"].split(' ')[0].strip()
        
        city_slug = f"{post}-{by_clean}".lower().replace("æ","ae").replace("ø","oe").replace("å","aa")
        vej_slug = vej.lower().replace(" ","-").replace("æ","ae").replace("ø","oe").replace("å","aa").replace(".","")
        base_url = f"https://www.dingeo.dk/adresse/{city_slug}/{vej_slug}"

        scan_modules = {
            "STAMDATA": {"path": "", "parser": self._parse_dingeo_bbr},
            "SKAT": {"path": "/skat/", "parser": self._parse_dingeo_tax},
            "VURDERING": {"path": "/vurdering/", "parser": self._parse_dingeo_value},
            "INTERNET": {"path": "/internet-mobil/", "parser": self._parse_dingeo_tech},
            "MILJØ": {"path": "/miljoe/", "parser": self._parse_dingeo_env},
            "DOKUMENTER": {"path": "/dokument/", "parser": self._parse_dingeo_docs},
            "NABOLAG": {"path": "/nabolag/", "parser": self._parse_dingeo_neighborhood}
        }

        for mod_name, mod_info in scan_modules.items():
            target = base_url + mod_info["path"]
            self._log(f"Auditerer modul: {mod_name}...", C.DIM)
            
            if safe_get_with_retry(driver, target, max_retries=1):
                time.sleep(random.uniform(2, 4))
                if "verify you are human" in driver.page_source.lower():
                    self._log(f"DinGeo-WAF blokerer {mod_name}. Forsøger næste modul.", C.RED)
                    continue

                source_text = driver.find_element(By.TAG_NAME, "body").text
                lines = [l.strip() for l in source_text.split('\n') if l.strip()]
                mod_info["parser"](source_text, lines, driver)

    def _parse_dingeo_bbr(self, source, lines, driver):
        """Parser BBR stamdata."""
        intel = {}
        target_keys = ["Opførselsesår", "Antal værelser", "Boligtype", "Etageareal", "Ydervæg", "Tagmateriale", "Anvendelse"]
        for i, l in enumerate(lines):
            for k in target_keys:
                if l == k and i+1 < len(lines): intel[k] = lines[i+1]
        self.data["DinGeo_Intelligence"]["BBR_Stamdata"] = intel
        if self.keep_screenshots:
            p = f"{session['loot_folder']}/01_DinGeo_Hus_{self.name.replace(' ', '_')}.png"
            driver.save_screenshot(p); self.data["Screenshots"].append(p)

    def _parse_dingeo_tax(self, source, lines, driver):
        """Parser ejendomsskat og grundskyld."""
        tax = self.data["DinGeo_Intelligence"]["Skat"]
        for i, l in enumerate(lines):
            if "Boligskat 2024" in l: tax["Skat_2024"] = lines[i+1]
            if "Boligskat 2025" in l: tax["Skat_2025_Est"] = lines[i+1]
            if "Grundskyld" in l: tax["Grundskyld"] = lines[i+1]

    def _parse_dingeo_value(self, source, lines, driver):
        """Parser ejendomsvurdering og salgshistorik."""
        val = self.data["DinGeo_Intelligence"]["Vurdering"]
        for i, l in enumerate(lines):
            if "Dingestimat" in l: val["Dingestimat"] = lines[i+1]
            if "Seneste salgspris" in l: val["Seneste_Salg"] = f"{lines[i+1]} ({lines[i+2] if i+2 < len(lines) else ''})"
            if "Kvadratmeterpris" in l: val["Kvadratmeterpris"] = lines[i+1]

    def _parse_dingeo_tech(self, source, lines, driver):
        """Parser internet og mobildækning."""
        tech = self.data["DinGeo_Intelligence"]["Infrastruktur"]
        if "Fibernet" in source: tech["Fiber"] = "Ja"
        if "5G" in source: tech["5G"] = "Ja"
        for i, l in enumerate(lines):
            if "Mobildækning" in l: tech["Mobil_Dækning"] = lines[i+1]

    def _parse_dingeo_env(self, source, lines, driver):
        """Parser miljørisici (Støj, Radon, Oversvømmelse)."""
        env = self.data["DinGeo_Intelligence"]["Miljø_Risici"]
        if "støj" in source.lower(): env["Støj_Niveau"] = "Data indhentet"
        if "oversvømmelse" in source.lower(): env["Oversvømmelse_Risiko"] = "Tjek rapport"
        if "radon" in source.lower(): env["Radon_Risiko"] = "Tjek rapport"

    def _parse_dingeo_docs(self, source, lines, driver):
        """Parser offentlige dokumenter og energimærke."""
        docs = self.data["DinGeo_Intelligence"]["Dokumenter"]
        if "energimærke" in source.lower():
            for i, l in enumerate(lines):
                if "Energimærke" in l: docs["Energimærke"] = lines[i+1]
        if "servitutter" in source.lower(): docs["Servitutter"] = "Fundet"

    def _parse_dingeo_neighborhood(self, source, lines, driver):
        """Parser demografiske data om nabolaget."""
        nb = self.data["DinGeo_Intelligence"]["Nabolag_Profil"]
        for i, l in enumerate(lines):
            if "bor i" in l and "naboer" in source:
                nb["Demografi"] = l + " " + (lines[i+1] if i+1 < len(lines) else "")

    def _discover_cohabitants(self, driver):
        """Kortlægger andre beboere på samme adresse."""
        v = self.data["Ejendom"].get("Vej", "")
        if not v: return
        clean_addr = v.split(',')[0].strip()
        dork = f'site:krak.dk "{clean_addr}" "{self.data["Ejendom"]["Post"]}"'
        for hit in omni_dork_search(driver, dork, max_links=3):
            title = hit.get('title', '')
            pot_name = title.split('-')[0].strip()
            if pot_name and self.name.lower() not in pot_name.lower() and "Krak" not in pot_name:
                if pot_name not in self.data["Bofæller_Netværk"]:
                    self.data["Bofæller_Netværk"].append(pot_name)
                    self._log(f"Relation identificeret: {pot_name}", C.MAGENTA)

    def _generate_map_links(self):
        """Skaber direkte efterretnings-links til Google Maps og StreetView."""
        v = self.data["Ejendom"].get("Vej")
        b = self.data["Ejendom"].get("By")
        if v and b:
            full_addr = f"{v}, {b}"
            enc_addr = urllib.parse.quote(full_addr)
            self.data["Maps_Links"] = [
                f"https://www.google.com/maps/search/{enc_addr}",
                f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={enc_addr}"
            ]

    def _calculate_confidence(self):
        """Beregner den overordnede Confidence Score for dataen."""
        score = 0
        if self.data["Telefonnumre"]: score += 40
        if self.data["Ejendom"].get("Vej"): score += 40
        if self.data["DinGeo_Intelligence"]["BBR_Stamdata"]: score += 20
        self.data["Metadata"]["Confidence_Score"] = score

    def save(self):
        """Arkiverer intelligence-rapporten i JSON format."""
        fld = session.get("loot_folder", "loot_evidence")
        fname = f"{fld}/01_DIRECTORY_{self.name.replace(' ', '_')}.json"
        if isinstance(self.data["Telefonnumre"], set):
            self.data["Telefonnumre"] = list(self.data["Telefonnumre"])
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        self._log(f"Intelligence-rapport arkiveret: {fname}", C.GREEN)

# SYSTEM EKSPORTERING
KrakIntelligenceAnalyst = DirectoryIntelligenceHunter
DirectoryIntelligenceHunter = DirectoryIntelligenceHunter