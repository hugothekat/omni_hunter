# -*- coding: utf-8 -*-

import sys
import time
import json
import os
import re
import random
import urllib.parse
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from core.utils import C, session, extract_danish_phones
from core.network import safe_get_with_retry

class DirectoryIntelligenceHunter:
    
    def __init__(self, name, city=""):
        self.name = name.strip()
        self.city = city.strip()
        
        self.data = {
            "Identitet": self.name,
            "Lokation": self.city,
            "Telefonnumre": set(),
            "Ejendom": {"Vej": "", "Post": "", "By": "", "Koordinater": ""},
            "DinGeo_Intelligence": {
                "BBR_Stamdata": {},
                "Vurdering": {},
                "Skat": {},
                "Dokumenter": {},
                "Infrastruktur": {}
            },
            "Bofæller_Netværk": [],
            "Screenshots": []
        }

    def _print(self, msg, color=C.CYAN):
        print(f"{C.DIM}[{datetime.now().strftime('%H:%M:%S')}]{C.RESET} {color}{msg}{C.RESET}")

    def run(self, driver):
        from core.browser import zap_cookies
        
        self._print(f"Starter directory scan: {self.name}, {self.city}")
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)

        self._scan_directory(driver, zap_cookies)

        if self.data["Ejendom"].get("Vej"):
            self._scan_dingeo(driver)
            self._find_cohabitants(driver)
        else:
            self._print("Ingen adresse lokaliseret. Springer DinGeo over.", C.RED)

        self.data["Telefonnumre"] = list(self.data["Telefonnumre"])
        self.save()
        return self.data

    def _bypass_cloudflare(self, driver):
        if not any(kw in driver.page_source.lower() for kw in ["cloudflare", "challenges", "turnstile"]):
            return

        self._print("Løser Cloudflare Turnstile...", C.YELLOW)
        time.sleep(3)
        
        try:
            iframe = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'challenges')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", iframe)
            time.sleep(1.5)
            
            x_off = random.randint(5, 20)
            y_off = random.randint(5, 20)
            ActionChains(driver).move_to_element_with_offset(iframe, x_off, y_off).click().perform()
            time.sleep(6)
            
            if "challenges" in driver.page_source.lower():
                driver.switch_to.frame(iframe)
                cb = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                cb.click()
                driver.switch_to.default_content()
                time.sleep(5)
        except Exception as e:
            driver.switch_to.default_content()

    def _scan_directory(self, driver, zap_cookies):
        q = urllib.parse.quote(f"{self.name} {self.city}")
        targets = {
            "Krak": f"https://www.krak.dk/{q}/personer",
            "DGS": f"https://www.degulesider.dk/{q}/personer"
        }

        for source, url in targets.items():
            self._print(f"Scanner {source}...")
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Referer': 'https://www.google.dk/'}})
            
            try:
                driver.get(url)
                self._bypass_cloudflare(driver)
                zap_cookies(driver)
                time.sleep(2)
                
                self._extract_data(driver)
                
                target_url = None
                for a in driver.find_elements(By.TAG_NAME, "a"):
                    href = a.get_attribute("href")
                    if href and re.search(r'/\d+/person/?$', href):
                        target_url = href
                        break
                        
                if target_url:
                    driver.get(target_url)
                    self._bypass_cloudflare(driver)
                    time.sleep(2)
                    self._extract_data(driver)
                    
                shot = f"{session.get('loot_folder', 'loot')}/01_{source}_{self.name.replace(' ', '_')}.png"
                driver.save_screenshot(shot)
                self.data["Screenshots"].append(shot)
                
            except Exception as e:
                self._print(f"Fejl på {source}: {e}", C.RED)

    def _extract_data(self, driver):
        try:
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                if "vis" in btn.text.lower() or any(c.isdigit() for c in btn.text):
                    driver.execute_script("arguments[0].click();", btn)
        except: pass
        
        time.sleep(1)
        body = driver.find_element(By.TAG_NAME, "body").text
        
        for p in extract_danish_phones(body):
            self.data["Telefonnumre"].add(f"{p[:2]} {p[2:4]} {p[4:6]} {p[6:8]}")
            
        if not self.data["Ejendom"]["Vej"]:
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                zip_match = re.search(r'^(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\-]+)$', line)
                if zip_match and i > 0:
                    vej = lines[i-1].split(',')[-1].strip()
                    if any(c.isdigit() for c in vej):
                        self.data["Ejendom"]["Vej"] = vej
                        self.data["Ejendom"]["Post"] = zip_match.group(1)
                        self.data["Ejendom"]["By"] = zip_match.group(2)
                        break
                        
        gps_m = re.search(r'(\d+\.\d+,\s*\d+\.\d+)', body)
        if gps_m: self.data["Ejendom"]["Koordinater"] = gps_m.group(1)

    def _scan_dingeo(self, driver):
        v = self.data["Ejendom"]["Vej"].split(',')[0].strip()
        p = self.data["Ejendom"]["Post"]
        b = self.data["Ejendom"]["By"].split(' ')[0].strip()
        
        slug_c = f"{p}-{b}".lower().replace("æ","ae").replace("ø","oe").replace("å","aa")
        slug_v = v.lower().replace(" ","-").replace("æ","ae").replace("ø","oe").replace("å","aa").replace(".","")
        base = f"https://www.dingeo.dk/adresse/{slug_c}/{slug_v}"

        endpoints = {
            "BBR_Stamdata": "",
            "Skat": "/skat/",
            "Vurdering": "/vurdering/",
            "Infrastruktur": "/internet-mobil/",
            "Dokumenter": "/dokument/"
        }

        for key, path in endpoints.items():
            self._print(f"Henter DinGeo: {key}...")
            try:
                driver.get(base + path)
                self._bypass_cloudflare(driver)
                time.sleep(2)
                
                lines = [l.strip() for l in driver.find_element(By.TAG_NAME, "body").text.split('\n') if l.strip()]
                
                if key == "BBR_Stamdata":
                    for i, l in enumerate(lines):
                        for k in ["Opførselsesår", "Antal værelser", "Etageareal", "Boligtype"]:
                            if l == k and i+1 < len(lines): self.data["DinGeo_Intelligence"][key][k] = lines[i+1]
                
                elif key == "Skat":
                    for i, l in enumerate(lines):
                        if "Boligskat 2024" in l: self.data["DinGeo_Intelligence"][key]["Skat_2024"] = lines[i+1]
                        if "Grundskyld" in l: self.data["DinGeo_Intelligence"][key]["Grundskyld"] = lines[i+1]
                        
                elif key == "Vurdering":
                    for i, l in enumerate(lines):
                        if "Dingestimat" in l: self.data["DinGeo_Intelligence"][key]["Dingestimat"] = lines[i+1]
                        if "Seneste salgspris" in l: self.data["DinGeo_Intelligence"][key]["Seneste_Salg"] = lines[i+1]
                        
            except Exception as e:
                pass

    def _find_cohabitants(self, driver):
        v = self.data["Ejendom"].get("Vej", "")
        if not v: return
        addr = v.split(',')[0].strip()
        
        for hit in omni_dork_search(driver, f'site:krak.dk "{addr}" "{self.data["Ejendom"]["Post"]}"', max_links=3):
            n = hit.get('title', '').split('-')[0].strip()
            if n and self.name.lower() not in n.lower() and "Krak" not in n:
                if n not in self.data["Bofæller_Netværk"]:
                    self.data["Bofæller_Netværk"].append(n)

    def save(self):
        f = session.get("loot_folder", "loot_evidence")
        path = f"{f}/01_DIRECTORY_{self.name.replace(' ', '_')}.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)
        self._print(f"Rapport gemt: {path}", C.GREEN)

KrakIntelligenceAnalyst = DirectoryIntelligenceHunter