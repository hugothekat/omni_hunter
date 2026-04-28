# -*- coding: utf-8 -*-
import sys
import time
import json
import os
import re
import urllib.parse
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from core.utils import C, session
from core.network import safe_get_with_retry, omni_dork_search

class KrakIntelligenceAnalyst: # Omdøbt for at matche Pivot-import i Modul 02
    def __init__(self, name, city=""):
        self.name = name.strip()
        self.city = city.strip()
        self.data = {
            "Identitet": self.name, 
            "Lokation": self.city, 
            "Telefonnumre": [], 
            "Ejendom": {},
            "GPS_Koordinater": "",
            "DinGeo_Intelligence": {}, 
            "Bofæller_Netværk": [], 
            "Erhvervs_Netværk_CVR": [], # NY V8 TILFØJELSE: CVR ejerskab
            "Maps_Links": [],       
            "Screenshots": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        from core.browser import zap_cookies 
        print(f"\n{C.CYAN}{'='*60}\n[01] Intelligence-Scanner (Krak, DGS, 118, OIS & DinGeo V8)\n{'='*60}{C.RESET}")
        
        # --- USYNLIGHEDS-TRICKET ---
        try:
            driver.set_window_position(-2000, 0)
        except:
            pass

        query = f"{self.name} {self.city}".strip().replace(" ", "+").lower()
        providers = {
            "Krak": f"https://www.krak.dk/{query}/personer",
            "De Gule Sider": f"https://www.degulesider.dk/{query}/personer"
        }

        os.makedirs(session["loot_folder"], exist_ok=True)

        for provider_name, url in providers.items():
            print(f"\n{C.YELLOW}[*] Forbinder til {provider_name}: {url}{C.RESET}")
            if safe_get_with_retry(driver, url):
                zap_cookies(driver)
                time.sleep(3)
                
                try:
                    search_img = f"{session['loot_folder']}/01_{provider_name}_Search_{self.name.replace(' ', '_')}.png"
                    driver.save_screenshot(search_img)
                    self.data["Screenshots"].append(search_img)
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    current_url = driver.current_url
                    
                    target_url = None
                    if re.search(r'/\d+/person/?$', current_url):
                        target_url = current_url
                    else:
                        links = driver.find_elements(By.TAG_NAME, "a")
                        base_domain = "krak.dk" if provider_name == "Krak" else "degulesider.dk"
                        pattern = rf'^https://www\.{base_domain}/([^/]+)/\d+/person$'
                        for link in links:
                            href = link.get_attribute("href")
                            if href and re.match(pattern, href):
                                target_url = href
                                break
                    
                    if target_url:
                        driver.get(target_url)
                        time.sleep(3)
                        self._extract_profile_data(driver, provider_name)
                except Exception as e:
                    print(f"{C.RED}    [!] Fejl: {e}{C.RESET}")

        # --- NY V8: Udfør 118.dk Fallback Dorking ---
        if not self.data["Telefonnumre"] and not self.data.get("Ejendom"):
            self._fallback_118_dork(driver)

        # --- NY V8: Udfør Erhvervs-tjek på personen (Ownr / Proff) ---
        self._check_business_ownership(driver)

        # --- EKSISTERENDE V7: Udfør Bofælle-søgning og Map-Links ---
        if self.data.get("Ejendom"):
            self._find_cohabitants(driver)
            self._generate_map_links()

        # --- SMART CLEANUP ---
        if self.data["Telefonnumre"] or self.data.get("Ejendom") or self.data.get("Erhvervs_Netværk_CVR"):
            final_screenshots = []
            for img in self.data["Screenshots"]:
                if "DinGeo" not in img:
                    try: os.remove(img)
                    except: pass
                else: final_screenshots.append(img)
            self.data["Screenshots"] = final_screenshots

        print(f"\n{C.GREEN}[✓] Intelligence opslag 100% færdig.{C.RESET}")
        self.save()
        return self.data

    def _fallback_118_dork(self, driver):
        """NY V8 TILFØJELSE: Hvis Krak fejler, dorker vi 118.dk direkte (Ofte gemmer de numre Krak sletter)"""
        print(f"\n{C.YELLOW}[*] Krak fejlede - Udfører Fallback Dork mod 118.dk...{C.RESET}")
        search_query = f'"{self.name}" {self.city}'.strip()
        dork = f'site:118.dk {search_query}'
        links = omni_dork_search(driver, dork, max_links=3)
        if links:
            for link in links:
                snippet = link.get('snippet', '')
                phones = re.findall(r'\b(?:[2-9]\d{7}|[2-9]\d{1}\s\d{2}\s\d{2}\s\d{2})\b', snippet)
                for ph in set(phones):
                    clean_ph = ph.replace(" ", "")
                    if len(clean_ph) == 8 and clean_ph not in self.data["Telefonnumre"]:
                        self.data["Telefonnumre"].append(clean_ph)
                        print(f"{C.GREEN}      🔥 Telefon fundet via 118.dk Fallback: {clean_ph}{C.RESET}")

    def _check_business_ownership(self, driver):
        """NY V8 TILFØJELSE: Tjekker om personen ejer et firma"""
        print(f"\n{C.YELLOW}[*] Scanner Proff.dk / Ownr.dk for skjulte virksomheds-ejerskaber...{C.RESET}")
        search_query = f'"{self.name}" {self.city}'.strip()
        dork = f'(site:ownr.dk OR site:proff.dk) {search_query}'
        links = omni_dork_search(driver, dork, max_links=3)
        if links:
            for link in links:
                snippet = link.get('snippet', '')
                cvr_matches = re.findall(r'\b(?:CVR|cvr)[\s:-]*(\d{8})\b', snippet)
                for cvr in cvr_matches:
                    if cvr not in self.data["Erhvervs_Netværk_CVR"]:
                        self.data["Erhvervs_Netværk_CVR"].append(cvr)
                        print(f"{C.MAGENTA}      🔥 Målet er tilknyttet en virksomhed! CVR: {cvr}{C.RESET}")

    def _extract_profile_data(self, driver, provider_name):
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(1)
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "vis" in btn.text.lower() or "nummer" in btn.text.lower():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
        except: pass

        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in body_text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            # 1. TELEFON
            if line == "Telefonnummer" and i + 1 < len(lines):
                p = lines[i+1].replace(" ", "")
                if len(p) == 8:
                    fmt = f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}"
                    if fmt not in self.data["Telefonnumre"]: self.data["Telefonnumre"].append(fmt)

            # 2. ADRESSE TOP
            if line == "Adresse" and i + 2 < len(lines) and not self.data.get("Ejendom"):
                vej, post_by = lines[i+1], lines[i+2]
                match = re.search(r'^([1-9]\d{3})\s+(.*)', post_by)
                if match:
                    post, by = match.group(1), match.group(2)
                    self.data["Ejendom"] = {"Vej": vej, "Post": post, "By": by}
                    self._scrape_dingeo_deep(driver, vej, post, by)

            # 3. ADRESSE BACKUP (Tabel) 
            if line == "Vejnavn" and i + 1 < len(lines) and not self.data.get("Ejendom"):
                vej = lines[i+1]
                post, by = "", ""
                for j in range(i, min(i+10, len(lines))):
                    if lines[j] == "Postnummer" and j + 1 < len(lines):
                        post = lines[j+1]
                    if lines[j] == "Bynavn" and j + 1 < len(lines):
                        by = lines[j+1]
                
                if vej and post and by:
                    self.data["Ejendom"] = {"Vej": vej, "Post": post, "By": by}
                    self._scrape_dingeo_deep(driver, vej, post, by)

            # 4. GPS
            if line == "Koordinater" and i + 1 < len(lines):
                self.data["GPS_Koordinater"] = lines[i+1]
        return True

    def _scrape_dingeo_deep(self, driver, vej, post, by):
        print(f"{C.CYAN}      [*] Dybde-analyserer ejendommen på DinGeo...{C.RESET}")
        
        city_slug = f"{post}-{by}".lower().replace(" ", "-").replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
        vej_slug = vej.lower().replace(" ", "-").replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
        base_url = f"https://www.dingeo.dk/adresse/{city_slug}/{vej_slug}"
        
        paths = {
            "Profil": "",
            "Dokumenter": "/dokument/",
            "Vurdering": "/vurdering/",
            "Boligskat": "/skat/",
            "Net_Mobil": "/internet-mobil/"
        }

        for category, path in paths.items():
            target = base_url + path
            if safe_get_with_retry(driver, target, max_retries=1):
                time.sleep(2)
                # Cookie Killer
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["tillad", "accepter", "forstået"]):
                            driver.execute_script("arguments[0].click();", btn)
                            break
                except: pass

                text = driver.find_element(By.TAG_NAME, "body").text
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                if category == "Profil":
                    # Screenshot af selve huset
                    img = f"{session['loot_folder']}/01_DinGeo_Hus_{self.name.replace(' ', '_')}.png"
                    driver.save_screenshot(img)
                    if img not in self.data["Screenshots"]:
                        self.data["Screenshots"].append(img)
                    
                    intel = {}
                    keys = ["Opførselsesår", "Antal værelser", "Anvendelse", "Varmeinstallation", "Boligtype", "Ydervægsmateriale", "Tagmateriale"]
                    for i, l in enumerate(lines):
                        for k in keys:
                            if l == k and i+1 < len(lines): intel[k] = lines[i+1]
                        if "bor i" in l and "nærmeste naboer" in text:
                            intel["Nabolag"] = l + " " + lines[i+1] if i+1 < len(lines) else l
                    self.data["DinGeo_Intelligence"]["BBR"] = intel

                elif category == "Dokumenter":
                    docs = {"Servitutter": "0", "Byggesager": "Ingen fundet"}
                    match = re.search(r'der (\w+) servitutter', text.lower())
                    if match: docs["Servitutter"] = match.group(1).capitalize()
                    if "ingen historiske byggesager" not in text.lower(): docs["Byggesager"] = "Fundet (Tjek link)"
                    self.data["DinGeo_Intelligence"]["Dokument_Status"] = docs

                elif category == "Vurdering":
                    vurdering = {}
                    for i, l in enumerate(lines):
                        if "Dingestimat" in l and i+1 < len(lines):
                            vurdering["Dingestimat"] = lines[i+1]
                        if "Seneste salgspris" in l and i+1 < len(lines):
                            vurdering["Seneste_Salg"] = lines[i+1] + " (" + (lines[i+2] if i+2 < len(lines) else "") + ")"
                    if vurdering:
                        self.data["DinGeo_Intelligence"]["Vurdering"] = vurdering

                elif category == "Boligskat":
                    skat = {}
                    for i, l in enumerate(lines):
                        if "Boligskat 2024" in l and i+1 < len(lines):
                            skat["Total_2024"] = lines[i+1]
                    if skat:
                        self.data["DinGeo_Intelligence"]["Skat"] = skat

                elif category == "Net_Mobil":
                    net = {"Fiber": "Nej", "5G": "Nej", "Mobil": "Ukendt"}
                    if "Fibernet" in text: net["Fiber"] = "Ja"
                    if "5G-internet" in text: net["5G"] = "Ja"
                    if "god mobildækning" in text: net["Mobil"] = "God"
                    self.data["DinGeo_Intelligence"]["Infrastruktur"] = net

    def _find_cohabitants(self, driver):
        """NY V7: Dorker selve adressen for at finde andre personer (Familie/Medstiftere)"""
        print(f"\n{C.YELLOW}[*] Deep OSINT: Scanner efter bofæller på adressen...{C.RESET}")
        vej = self.data["Ejendom"].get("Vej", "")
        if not vej: return

        # Splitter vejnavnet fra for at fjerne etage/dør (Krak dorker bedst på ren adresse)
        clean_addr = vej.split(',')[0].strip()
        dork = f'site:krak.dk OR site:118.dk "{clean_addr}"'
        
        links = omni_dork_search(driver, dork, max_links=3)
        for link in links:
            title = link.get('title', '')
            pot_navn = title.split('-')[0].strip()
            # Sikrer at vi ikke bare fanger vores eget mål igen
            if pot_navn and self.name.lower() not in pot_navn.lower() and "Krak" not in pot_navn:
                if pot_navn not in self.data["Bofæller_Netværk"]:
                    self.data["Bofæller_Netværk"].append(pot_navn)
                    print(f"{C.MAGENTA}      -> Mulig bofælle/netværk fundet: {pot_navn}{C.RESET}")

    def _generate_map_links(self):
        """NY V7: Bygger direkte links til Satellit og Street View ud fra adressen"""
        vej = self.data["Ejendom"].get("Vej", "")
        by = self.data["Ejendom"].get("By", "")
        if vej and by:
            fuld_adresse = f"{vej}, {by}"
            encoded_addr = urllib.parse.quote(fuld_adresse)
            # Standard Maps og StreetView API links (virker uden API nøgle)
            maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_addr}"
            self.data["Maps_Links"].append(maps_url)
            print(f"{C.CYAN}      -> Google Maps Link genereret.{C.RESET}")

    def save(self):
        has_data = bool(self.data.get("Telefonnumre")) or bool(self.data.get("Ejendom")) or bool(self.data.get("DinGeo_Intelligence")) or bool(self.data.get("Erhvervs_Netværk_CVR"))
        if not has_data:
            gem = input(f"\n{C.YELLOW}[?] Intet fundet. Vil du gemme en tom rapport? (j/n): {C.RESET}").strip().lower()
            if gem != 'j':
                print(f"{C.DIM}[*] Rapport kasseret.{C.RESET}")
                return

        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/01_DIRECTORY_{self.name.replace(' ', '_')}.json"
        
        # Slet gammel fil for skrivesikkerhed
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass
            
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

KrakIntelligenceAnalyst = DirectoryIntelligenceHunter