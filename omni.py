# ==========================================
# OMNI-HUNTER v51.0 - COMPLETE PROFESSIONAL OSINT SUITE
# ==========================================
# Advanced Digital Forensics & OSINT Platform
# Authorized for Law Enforcement Use Only
# ==========================================

import zipfile         
import glob            
import concurrent.futures 
import requests
import subprocess
import json
import urllib.parse
import time
import re
import sys
import os
import hashlib
import shutil
import random
import locale
import io                
import itertools       
import imaplib       
import email           
from email.header import decode_header
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps, ImageEnhance
from PIL.ExifTags import TAGS
import piexif

REGEX_EMAIL = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}\b')
REGEX_BANK = re.compile(r'(?:reg|regnr)[^\d]{0,10}(\d{4}).{0,40}?(?:konto|kontonr)[^\d]{0,10}(\d{7,10})', re.IGNORECASE)
REGEX_CPR = re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b')
REGEX_BTC = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
REGEX_ETH = re.compile(r'\b0x[a-fA-F0-9]{40}\b')

import logging
from logging.handlers import RotatingFileHandler

# Opsætning af professionel logning
log_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s | %(message)s')
log_file = "omni_audit_trail.log"

# Roterer loggen så den ikke fylder uendeligt (gemmer max 5x 10MB filer)
my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=10*1024*1024, backupCount=5, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)

logger = logging.getLogger('OMNI_HUNTER')
logger.setLevel(logging.DEBUG)
logger.addHandler(my_handler)

import argparse

# ==========================================
# CONFIGURATION LOADER
# ==========================================
def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        # Opretter en standard config-fil, hvis den ikke findes
        default_config = {
            "use_tor_proxy": False,
            "tor_proxy_url": "socks5://127.0.0.1:9050",
            "api_keys": {
                "shodan": "",
                "hunter_io": "",
                "virus_total": ""
            }
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(config_path, "r") as f:
        return json.load(f)

# Indlæs konfigurationen globalt, så alle moduler kan bruge den
CONFIG = load_config()

def setup_cli():
    parser = argparse.ArgumentParser(description="OMNI-HUNTER OSINT Framework")
    parser.add_argument("-t", "--target", help="Målets navn eller email")
    parser.add_argument("-m", "--module", help="Modulnummer (f.eks. 03 for Breach)", type=str)
    parser.add_argument("--headless", action="store_true", help="Kør uden menu")
    return parser.parse_args()

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_hunter_session():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    
    # --- NYT: PROXY / TOR ROUTING ---
    if CONFIG.get("use_tor_proxy"):
        print(f"{C.YELLOW}[*] Ruter netværkstrafik gennem Tor/Proxy...{C.RESET}")
        session.proxies = {
            'http': CONFIG["tor_proxy_url"],
            'https': CONFIG["tor_proxy_url"]
        }
    
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 429, 500, 502, 503, 504 ])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

http = get_hunter_session()
# Brug herefter `http.get(url)` i stedet for `requests.get(url)` overalt!

# Eksterne afhængigheder (Try/Except)
try:
    import magic
    import cv2
    import numpy as np
except ImportError:
    pass # Bliver grebet af check_dependencies() senere

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import fitz # PyMuPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict

# ==========================================
# TERMINAL COLORS
# ==========================================
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

# ==========================================
# SYSTEM CONFIGURATION
# ==========================================

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
try:
    locale.setlocale(locale.LC_ALL, 'da_DK.UTF-8')
except Exception:
    pass

# ==========================================
# GLOBAL SESSION STATE
# ==========================================

session = {
    "name": "", 
    "city": "", 
    "email": "", 
    "phone": "",
    "username": "",
    "found_links": [],
    "loot_folder": "loot_evidence"
}

# ==========================================
# CORE UTILS & ANTI-BAN ENGINE
# ==========================================

def capture_evidence(driver, name):
    """Gemmer et screenshot af den nuværende side som bevismateriale."""
    timestamp = datetime.now().strftime("%H%M%S")
    path = f"{session['loot_folder']}/SCREENSHOT_{name}_{timestamp}.png"
    driver.save_screenshot(path)
    print(f"{C.YELLOW}    [📷] Bevis sikret: {path}{C.RESET}")

# ==========================================
# OPTIMIZATION #1: SEARCH CACHE SYSTEM
# ==========================================

class SearchCache:
    """Intelligent caching to prevent redundant API calls"""
    def __init__(self, loot_folder="loot_evidence"):
        self.cache_file = f"{loot_folder}/search_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cached data from disk"""
        if os.path.exists(self.cache_file):
            try:   
                return json.loads(Path(self.cache_file).read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}
    
    def get(self, module_type, query_value):
        """Retrieve cached result"""
        key = f"{module_type}:{query_value}"
        return self.cache.get(key)
    
    def set(self, module_type, query_value, result):
        """Store result in cache"""
        key = f"{module_type}:{query_value}"
        # Convert sets to lists for JSON serialization
        serialized = {}
        for k, v in result.items():
            if isinstance(v, set):
                serialized[k] = list(v)
            else:
                serialized[k] = v
        
        self.cache[key] = serialized
        try:
            Path(self.cache_file).write_text(
                json.dumps(self.cache, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception:
            pass
    
    def exists(self, module_type, query_value):
        """Check if query already cached"""
        return f"{module_type}:{query_value}" in self.cache
    
    def clear(self):
        """Reset cache"""
        self.cache = {}
        Path(self.cache_file).write_text("{}", encoding='utf-8')

search_cache = None

# ==========================================
# MODULE 01: Personregister-efterretning
# ==========================================
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
        print(f"\n{C.CYAN}{'='*60}\n[MODULE 01] Personregister-efterretning (Krak + DinGeo)\n{'='*60}{C.RESET}")
        
        # KRAK OPDATERING: Den nye URL struktur bruger '+' og fjerner '/søg/'
        query = f"{self.name} {self.city}".strip().replace(" ", "+").lower()
        krak_url = f"https://www.krak.dk/{query}/personer"
        
        if safe_get_with_retry(driver, krak_url):
            zap_cookies(driver)
            time.sleep(3)  # Ekstra tid til Krak's nye frontend
            
            try:
                # TRIN 1: Forsøg at læse data direkte fra søgesiden!
                # Som set på dit screenshot, viser Krak nu ofte resultatet direkte.
                found_direct_data = self._extract_profile_data(driver)
                
                # TRIN 2: Hvis forsiden ikke viste adressen åbent, leder vi efter links til profiler
                if not found_direct_data:
                    print(f"{C.YELLOW}[*] Data ikke åben på forsiden. Leder efter profil-links...{C.RESET}")
                    
                    # Undgår at matche selve søgesiden ("/personer")
                    elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/person/') and not(contains(@href, '/personer'))]")
                    
                    first_name = self.name.split()[0].lower()
                    unique_links = []
                    for el in elements:
                        href = el.get_attribute("href")
                        if href and first_name in href.lower() and href not in unique_links:
                            unique_links.append(href)
                    
                    target_url = None
                    if len(unique_links) > 1:
                        print(f"\n{C.YELLOW}[!] Fandt {len(unique_links)} mulige matches på Krak:{C.RESET}")
                        for i, link in enumerate(unique_links):
                            try:
                                clean_name = urllib.parse.unquote(link).split('krak.dk/')[1].split('/')[0].replace('+', ' ').title()
                            except Exception:
                                clean_name = link
                            print(f"{C.CYAN}[{i+1}]{C.RESET} {clean_name} -> {link}")
                        
                        val = input(f"\n{C.YELLOW}Hvilken profil er den rigtige? (Indtast nummer 1-{len(unique_links)}, eller 0 for at afbryde): {C.RESET}").strip()
                        if val.isdigit() and 0 < int(val) <= len(unique_links):
                            target_url = unique_links[int(val)-1]
                    elif len(unique_links) == 1:
                        target_url = unique_links[0]
                
                    if target_url:
                        print(f"{C.GREEN}\n    ✓ Graver dybere i valgt profil: {target_url}{C.RESET}")
                        driver.get(target_url)
                        time.sleep(3)
                        # Udtræk data fra den specifikke profilside
                        if not self._extract_profile_data(driver):
                            print(f"{C.YELLOW}    [-] Kunne ikke udtrække adressen fra profilen. Den er muligvis manuelt beskyttet.{C.RESET}")
                    else:
                        print(f"{C.RED}    [-] Ingen profil valgt eller fundet for {self.name}.{C.RESET}")

            except Exception as e:
                print(f"{C.RED}    [!] Fejl under Krak-søgning: {e}{C.RESET}")
        
        # Sender de fundne data retur til Main-menuen for Pivot muligheder
        self.save()
        return self.data

    def _extract_profile_data(self, driver):
        """Leder efter Telefon og Adresse på den aktuelle side (DOM-Bypass & Dynamic Wait)"""
        success = False
        
        # 1. DYNAMISK VENTETID: Tvinger scriptet til at vente på at Krak's API loader data ind!
        # Den kigger konstant i op til 8 sekunder efter et 4-cifret dansk postnummer (1000-9990)
        try:
            WebDriverWait(driver, 8).until(
                lambda d: re.search(r'\b[1-9]\d{3}\b', d.find_element(By.TAG_NAME, "body").text)
            )
        except Exception:
            print(f"{C.YELLOW}    [*] Advarsel: Siden loadede langsomt. Forsøger tvangsudtrækning...{C.RESET}")
            time.sleep(2)

        # 2. JS DOM BYPASS: Omgår Kraks "display:none" anti-bot CSS
        body_text = driver.execute_script("return document.body.innerText;")
        if not body_text or len(body_text) < 20:
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

        # --- ADRESSE (GOLIATH v6.0 - Linje-Scanner) ---
        if not self.data.get("Ejendom"):
            lines = body_text.split('\n')
            for line in lines:
                # Scenarie A: Matcher direkte "Lucernevej 3, 8920 Randers Nv"
                match_a = re.search(r'(.*?)[,\s]+([1-9]\d{3})\s+(.*)', line)
                if match_a and len(match_a.group(1)) > 3 and any(char.isdigit() for char in match_a.group(1)):
                    vej = match_a.group(1).strip()
                    post = match_a.group(2).strip()
                    by = match_a.group(3).strip().split()[0] # Fjerner "Ruteplan" knapper
                    
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
        
        if safe_get_with_retry(driver, dingeo_url):
            try:
                text = driver.find_element(By.TAG_NAME, "body").text
                if "BBR informationer" in text or "Salgshistorik" in text:
                    print(f"{C.GREEN}    ✓ DinGeo Data fundet!{C.RESET}")
                    self.data["DinGeo_Data"]["Link"] = dingeo_url
                    self.data["DinGeo_Data"]["Opsummering"] = text[:500] 
                else:
                    print(f"{C.YELLOW}    [-] Kunne ikke finde specifik bolig på DinGeo.{C.RESET}")
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
        self.last_saved_file = filename # GEMMER STIEN TIL PIVOTING
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 02: BUSINESS INTELLIGENCE (CVRAPI)
# ==========================================

class BusinessIntelligenceAnalyst:
    def __init__(self, name, city=""):
        self.name = name.strip()
        self.results = {"Mål": self.name, "Virksomheder": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver): # Driver beholdes for at matche main(), men bruges ikke her
        print(f"\n{C.CYAN}{'='*60}\n[02] Erhvervs-efterretning (CVRAPI)\n{'='*60}{C.RESET}")
        print(f"[*] Søger i CVR Registeret via API: {self.name}")
        
        headers = {"User-Agent": "OmniHunter-OSINT-Tool"}
        url = f"https://cvrapi.dk/api?search={urllib.parse.quote(self.name)}&country=dk"
        
        try:
            response = http.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and "error" not in response.text:
                data = response.json()
                print(f"{C.GREEN}    ✓ Virksomhed fundet: {data.get('name')} (CVR: {data.get('vat')}){C.RESET}")
                print(f"      -> Status: {data.get('status', 'Aktiv')}")
                print(f"      -> Adresse: {data.get('address')}, {data.get('zipcode')} {data.get('city')}")
                print(f"      -> Ansatte: {data.get('employees')}")
                self.results["Virksomheder"].append(data)
            else:
                print(f"{C.YELLOW}    [-] Ingen CVR matches fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] API Fejl: {e}{C.RESET}")
            
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/02_BUSINESS_{self.name.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 03: BREACH INTELLIGENCE ANALYST
# ==========================================
class BreachIntelligenceAnalyst:
    """Identifies email addresses in public data breaches and paste sites"""
    def __init__(self, email):
        self.email = email.strip()
        self.data = {"Email": self.email, "Paste_Sites": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[03] Lækage-analyse (Breach)\n{'='*60}{C.RESET}")
        print(f"Target Email: {self.email}\n")
        
        noise_filter = "-site:microsoft.com -site:wikihow.com -site:live.com"
        
        # 1. Standard Paste Sites
        print(f"{C.YELLOW}[*] Scanner Paste-sites og open dumps...{C.RESET}")
        for site in ["pastebin.com", "controlc.com", "throwbin.io", "ghostbin.co"]:
            dork = f'site:{site} "{self.email}" {noise_filter}'
            
            # NYT: Vi bruger den nye motor her!
            links = omni_dork_search(driver, dork, max_links=2)
            
            for link in links:
                if not any(x in link["url"].lower() for x in ["microsoft", "wikihow"]):
                    print(f"{C.GREEN}    ✓ PASTE FUNDET: {link['url'][:80]}{C.RESET}")
                    if link["url"] not in self.data["Paste_Sites"]:
                        self.data["Paste_Sites"].append(link["url"])
        
        # 2. Advanced Filetype Dorking
        print(f"\n{C.YELLOW}[*] Scanner ubeskyttede servere for database-filer...{C.RESET}")
        db_dorks = [
            f'"{self.email}" ext:sql OR ext:txt OR ext:log {noise_filter}',
            f'"{self.email}" intext:"password" OR intext:"hash" {noise_filter}'
        ]
        
        if "Database_Dumps" not in self.data: self.data["Database_Dumps"] = []
            
        for dork in db_dorks:
            # NYT: Vi bruger den nye motor her!
            links = omni_dork_search(driver, dork, max_links=3)
            
            for link in links:
                if not any(x in link["url"].lower() for x in ["microsoft", "wikihow"]):
                    print(f"{C.RED}    🔥 KRITISK FIL FUNDET: {link['url'][:80]}{C.RESET}")
                    if link["url"] not in self.data["Database_Dumps"]:
                        self.data["Database_Dumps"].append(link["url"])
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/03_BREACH_{self.email.replace('@', '_at_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 04: SOCIAL MEDIA PROFILER
# ==========================================
class SocialMediaProfiler:
    def __init__(self, username):
        self.username = username.strip()
        self.data = {"Brugernavn": self.username, "Direct_Hits": [], "Dork_Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[04] Social Media Profiler\n{'='*60}{C.RESET}")
        print(f"Username: {self.username}\n")
        
        # 1. Direkte hits
        for platform, url in {"GitHub": f"https://github.com/{self.username}", "TikTok": f"https://www.tiktok.com/@{self.username}"}.items():
            if safe_get_with_retry(driver, url) and "404" not in driver.title.lower():
                print(f"{C.GREEN}    ✓ {platform}: {url}{C.RESET}")
                self.data["Direct_Hits"].append(url)
        
        # 2. Dorking efter profiler (Nu med Anti-Ban)
        platforms = ["facebook.com", "instagram.com", "linkedin.com", "dba.dk", "twitter.com"]
        for site in platforms:
            dork = f'site:{site} "{self.username}"'
            # Vi bruger nu omni_dork_search i stedet for direkte DDG kald
            links = omni_dork_search(driver, dork, max_links=2)
            for link in links:
                if site in link['url']:
                    print(f"{C.GREEN}    ✓ FUNDET PÅ {site.upper()}: {link['url']}{C.RESET}")
                    self.data["Dork_Hits"].append(link['url'])
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/04_SOCIAL_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 05: OFFLINE DATABASE ANALYZER
# ==========================================
class OfflineDatabaseAnalyzer:
    """High-speed analysis of large local databases using Ripgrep (inkl. komprimerede .gz/.zip)"""
    def __init__(self, target, file_path):
        self.target = target.strip()
        self.file_path = file_path.strip()
        self.data = {"Mål": self.target, "Fil": self.file_path, "Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self):
        print(f"\n{C.CYAN}{'='*60}\n[05] Offline Database Analyse (Ripgrep Engine)\n{'='*60}{C.RESET}")
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Databasefil ikke fundet: {self.file_path}{C.RESET}"); return
            
        print(f"[*] Kører High-Speed scan på {os.path.basename(self.file_path)}...")
        try:
            # -z flaget tillader søgning direkte i komprimerede filer!
            result = subprocess.run(['rg', '-z', '-i', '-m', '50', self.target, self.file_path], capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"{C.GREEN}    🔥 HIT: {line.strip()[:150]}...{C.RESET}")
                        self.data["Hits"].append(line.strip())
                print(f"\n{C.YELLOW}[*] Fandt {len(self.data['Hits'])} matches.{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen matches i databasen.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}[!] Fejl: Ripgrep er ikke installeret. Kør 'sudo apt install ripgrep'.{C.RESET}")
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/05_OFFLINE_{self.target.replace('@','_').replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")

# ==========================================
# MODULE 06: EMAIL PATTERN GENERATOR
# Batch email pattern validation
# ==========================================

class EmailPatternGenerator:
    """Generates and validates email address patterns from name"""
    def __init__(self, name):
        parts = name.lower().split()
        self.first = parts[0] if len(parts) > 0 else ""
        self.last = parts[-1] if len(parts) > 1 else ""
        self.name = name
        self.data = {
            "Navn": name,
            "Generated_Emails": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[06] E-mail-mønster Validering\n{'='*60}{C.RESET}")
        print(f"Target: {self.name}\n")
        
        domains = ["gmail.com", "hotmail.com", "live.dk", "mail.dk", "outlook.dk"]
        patterns = [f"{self.first}.{self.last}", f"{self.first}{self.last}", f"{self.first[0]}{self.last}"]
        
        all_emails = [f"{p}@{d}" for p in patterns for d in domains]
        
        # Vi sender alle mønstre afsted i én stor "OR" søgning via Anti-Ban motoren
        batch_query = " OR ".join([f'"{e}"' for e in all_emails])
        links = omni_dork_search(driver, batch_query, max_links=15)
        
        found_emails = set()
        for link in links:
            text = link["text"].lower()
            for email in all_emails:
                if email in text:
                    found_emails.add(email)
                    print(f"{C.GREEN}    ✓ BEKRÆFTET MØNSTER: {email}{C.RESET}")
        
        self.data["Generated_Emails"] = list(found_emails)
        self.save()

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/05_EMAILGEN_{self.first}_{self.last}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n[✓] Report saved: {filename}")

# ==========================================
# MODULE 07: PHONE INTELLIGENCE HUNTER
# Web dorking for phone numbers
# ==========================================

class PhoneIntelligenceHunter:
    """Deep web search for phone number occurrences"""
    def __init__(self, phone):
        self.phone = phone.replace(" ", "").replace("+45", "")
        self.data = {
            "Nummer": f"+45 {self.phone}",
            "Web_Spor": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        """Execute phone search"""
        print(f"\n{'='*60}")
        print(f"[07] Telefon-efterretning")
        print(f"{'='*60}")
        print(f"Target: +45 {self.phone}\n")

        formats = [
            f'"{self.phone}"',
            f'"{self.phone[:2]} {self.phone[2:4]} {self.phone[4:6]} {self.phone[6:8]}"',
            f'"{self.phone[:4]} {self.phone[4:]}"'
        ]
        
        print("[*] Dorking formats...")
        for dork in formats:
            if safe_get_with_retry(driver, f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}"):
                links = extract_duckduckgo_links(driver, max_links=4)
                for link in links:
                    href = link["url"]
                    if "krak.dk" not in href:
                        print(f"    ✓ {href[:60]}")
                        if href not in self.data["Web_Spor"]:
                            self.data["Web_Spor"].append(href)
        
        self.save()

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/06_PHONE_{self.phone}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n[✓] Report saved: {filename}")

# ==========================================
# MODULE 08: DARK WEB INTELLIGENCE
# ==========================================
class DarkWebIntelligence:
    """Searches dark web (Tor/Onion) metadata via Ahmia (No-Browser API Method)"""
    def __init__(self, query):
        self.query = query.strip()
        self.data = {"Søgning": self.query, "Onion_Links": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver): # Vi beholder 'driver' som parameter så main() ikke crasher, men vi ignorerer den
        print(f"\n{C.CYAN}{'='*60}\n[08] Mørkenet-efterretning (Tor) (Ahmia)\n{'='*60}{C.RESET}")
        print(f"Query: {self.query}\n")
        
        url = f"https://ahmia.fi/search/?q={urllib.parse.quote(self.query)}"
        print(f"{C.YELLOW}[*] Sender lynhurtig request til Ahmia...{C.RESET}")
        
        try:
            # Drop Selenium, brug direkte requests!
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=10)
            
            # Find alle .onion links direkte i HTML'en via regex
            onions = set(re.findall(r'[a-z2-7]{16,56}\.onion', res.text))
            
            for o in list(onions)[:10]: # Vis top 10
                print(f"{C.GREEN}    ✓ ONION HIT: {o}{C.RESET}")
                self.data["Onion_Links"].append(o)
                
            if not onions:
                print(f"{C.YELLOW}    [-] Ingen nævneværdige .onion resultater fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] API Fejl ved Ahmia: {e}{C.RESET}")
        
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/08_DARKWEB_{self.query.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")

# ==========================================
# MODULE 09: EMAIL TRACKER
# Gravatar & Holehe checks
# ==========================================

class EmailTracker:
    """Gravatar & Holehe OSINT Checks (No-Browser Edition)"""
    def __init__(self, email):
        self.email = email.strip()
        self.data = {"Email": self.email, "Gravatar_Hash": hashlib.md5(self.email.lower().encode()).hexdigest(), "Gravatar_Data": {}, "Holehe_Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self, _=None): # Ignorerer driver fuldstændigt
        print(f"\n{C.CYAN}{'='*60}\n[09] E-mail Tracker (Gravatar & Holehe)\n{'='*60}{C.RESET}")
        
        # 1. Gravatar Tjek via lynhurtig API
        h = self.data["Gravatar_Hash"]
        print(f"{C.YELLOW}[*] Checker Gravatar API...{C.RESET}")
        try:
            res = requests.get(f"https://en.gravatar.com/{h}.json", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if res.status_code == 200:
                grav_json = res.json()
                if "entry" in grav_json and grav_json["entry"]:
                    entry = grav_json["entry"][0]
                    print(f"{C.GREEN}    ✓ Offentlig Gravatar Profil Fundet!{C.RESET}")
                    if "displayName" in entry:
                        self.data["Gravatar_Data"]["Navn"] = entry["displayName"]
                        print(f"      -> Navn: {entry['displayName']}")
        except Exception: pass

        # 2. Holehe Integration 
        print(f"\n{C.YELLOW}[*] Kører Holehe OSINT engine for at finde registrerede profiler (vent venligst)...{C.RESET}")
        try:
            result = subprocess.run(['holehe', self.email, '--only-used'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "[+]" in line:
                    site = line.split("]")[1].strip()
                    print(f"{C.GREEN}    ✓ Konto fundet på: {site}{C.RESET}")
                    self.data["Holehe_Hits"].append(site)
            if not self.data["Holehe_Hits"]:
                print(f"{C.DIM}    [-] Holehe fandt ingen åbne profiler.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}    [!] 'holehe' er ikke installeret. Kør 'pip install holehe'.{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/09_EMAILTRACK_{self.email.replace('@', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")

# ==========================================
# MODULE 10: IP NETWORK ANALYZER (Shodan Upgrade)
# ==========================================

class IPNetworkAnalyzer:
    """Geo, Shodan og AlienVault OTX Threat Intelligence"""
    def __init__(self, ip):
        self.ip = ip.strip()
        self.data = {"IP": self.ip, "GeoData": {}, "Shodan_Data": {}, "AlienVault_OTX": {}, "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[10] IP- & Threat Intel Analyse (Geo + Shodan + AlienVault)\n{'='*60}{C.RESET}")
        
        # 1. GeoIP
        try:
            res1 = requests.get(f"http://ip-api.com/json/{self.ip}?fields=status,country,city,isp,org,mobile,proxy,hosting").json()
            if res1.get("status") == "success":
                self.data["GeoData"] = res1
                print(f"{C.GREEN}    ✓ Lokation: {res1.get('city')}, {res1.get('country')} (ISP: {res1.get('isp')}){C.RESET}")
                if res1.get("proxy") or res1.get("hosting"):
                    print(f"{C.RED}      -> [!] ADVARSEL: IP er flaget som Datacenter/Proxy/VPN!{C.RESET}")
        except Exception: pass

        # 2. Shodan
        print(f"{C.YELLOW}[*] Scanner via Shodan InternetDB...{C.RESET}")
        try:
            shodan = requests.get(f"https://internetdb.shodan.io/{self.ip}", timeout=5).json()
            if "ports" in shodan:
                self.data["Shodan_Data"] = shodan
                print(f"{C.GREEN}    ✓ Åbne Porte: {', '.join(map(str, shodan.get('ports', [])))}{C.RESET}")
        except Exception: pass

        # 3. AlienVault OTX
        print(f"{C.YELLOW}[*] Checker IP mod AlienVault OTX Threat Pulses...{C.RESET}")
        try:
            otx = requests.get(f"https://otx.alienvault.com/api/v1/indicators/IPv4/{self.ip}/general", timeout=5).json()
            if "pulse_info" in otx and otx["pulse_info"]["count"] > 0:
                self.data["AlienVault_OTX"] = otx["pulse_info"]
                print(f"{C.RED}    🔥 KRITISK: IP optræder i {otx['pulse_info']['count']} AlienVault Threat Pulses (Kendt ondsindet aktivitet)!{C.RESET}")
            else:
                print(f"{C.GREEN}    ✓ IP'en er ren hos AlienVault.{C.RESET}")
        except Exception: pass

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/10_IP_{self.ip.replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")

# ==========================================
# MODULE 11: DIGITAL FORENSICS EXAMINER
# File metadata and EXIF analysis
# ==========================================

class DigitalForensicsExaminer:
    """Advanced file forensics with metadata extraction"""
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {
            "Fil": os.path.basename(file_path),
            "Sti": file_path,
            "Filstørrelse": 0,
            "Filtype": "",
            "GPS_Koordinater": None,
            "GPS_Maps_Link": "",
            "Temporal_Data": {
                "Oprettet": None,
                "Ændret": None,
                "Manipuleret": False
            },
            "Enheds_Info": {},
            "EXIF_Data": {},
            "Integritetstjek": {
                "Bevis": "",
                "Modsigende_Felter": []
            },
            "Timestamp": datetime.now().isoformat()
        }
    
    def run(self):
        """Execute forensics analysis"""
        print(f"\n{'='*60}")
        print(f"[11] Udtræk ALT data fra billeder")
        print(f"{'='*60}")
        print(f"File: {os.path.basename(self.file_path)}\n")
        
        if not os.path.exists(self.file_path):
            print(f"[!] File not found")
            return
        
        self._extract_basic_info()
        if self.data["Filtype"].lower() in ['jpg', 'jpeg', 'png', 'gif']:
            self._extract_exif_data()
            self._extract_gps_data()
        self._temporal_analysis()
        self._device_profiling()
        self._integrity_check()
        self.save()
    
    def _extract_basic_info(self):
        """Extract basic file information and Cryptographic Hashes"""
        try:
            stat_info = os.stat(self.file_path)
            self.data["Filstørrelse"] = stat_info.st_size
            self.data["Filtype"] = os.path.splitext(self.file_path)[1][1:].upper()
            
            # --- NYT: Kryptografisk Bevis-sikring (Chain of Custody) ---
            print(f"[*] Beregner kryptografiske fingeraftryk...")
            with open(self.file_path, "rb") as f:
                file_bytes = f.read()
                self.data["Kryptografi"] = {
                    "MD5": hashlib.md5(file_bytes).hexdigest(),
                    "SHA-256": hashlib.sha256(file_bytes).hexdigest()
                }
            
            print(f"[*] File Type: {self.data['Filtype']}")
            print(f"[*] Size: {self.data['Filstørrelse']} bytes")
            print(f"[*] SHA-256: {self.data['Kryptografi']['SHA-256'][:15]}...")
        except Exception as e:
            print(f"[!] Error: {str(e)}")
    
    def _extract_exif_data(self):
        """Extract EXIF metadata"""
        try:
            img = Image.open(self.file_path)
            exif_dict = piexif.load(self.file_path)
            for ifd_name in ("0th", "Exif", "GPS", "1st"):
                ifd = exif_dict[ifd_name]
                for tag in ifd:
                    tag_name = piexif.TAGS[ifd_name][tag]["name"]
                    tag_value = ifd[tag]
                    try:
                        if isinstance(tag_value, bytes):
                            tag_value = tag_value.decode('utf-8', errors='ignore')
                        self.data["EXIF_Data"][tag_name] = str(tag_value)[:500]
                    except Exception:
                        pass
            print(f"[*] EXIF Fields: {len(self.data['EXIF_Data'])}")
        except Exception:
            print(f"[*] No EXIF data")
    
    def _extract_gps_data(self):
        """Extract GPS coordinates"""
        try:
            img = Image.open(self.file_path)
            exif_data = img._getexif()
            if exif_data is None:
                return
            
            gps_ifd = exif_data.get(34853)
            if gps_ifd is None:
                return
            
            lat = self._convert_to_degrees(gps_ifd[2])
            lon = self._convert_to_degrees(gps_ifd[4])
            lat_ref = gps_ifd[1].decode('utf-8', errors='ignore')
            lon_ref = gps_ifd[3].decode('utf-8', errors='ignore')
            
            if lat_ref == 'S':
                lat = -lat
            if lon_ref == 'W':
                lon = -lon
            
            self.data["GPS_Koordinater"] = {"Breddegrad": lat, "Længdegrad": lon}
            self.data["GPS_Maps_Link"] = f"https://www.google.com/maps/?q={lat},{lon}"
            
            print(f"[✓] GPS: {lat:.6f}, {lon:.6f}")
        except Exception:
            pass
    
    def _convert_to_degrees(self, value):
        """Convert GPS data to degrees"""
        try:
            d, m, s = value
            return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
        except Exception:
            return None
    
    def _temporal_analysis(self):
        """Analyze file timestamps"""
        try:
            stat_info = os.stat(self.file_path)
            created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            self.data["Temporal_Data"]["Oprettet"] = created
            self.data["Temporal_Data"]["Ændret"] = modified
            
            if created != modified:
                self.data["Temporal_Data"]["Manipuleret"] = True
                print(f"[!] MANIPULATION DETECTED")
            
            print(f"[*] Created: {created}")
            print(f"[*] Modified: {modified}")
        except Exception:
            pass
    
    def _device_profiling(self):
        """Extract device information"""
        try:
            img = Image.open(self.file_path)
            exif_data = img._getexif()
            if exif_data is None:
                return
            
            important_tags = {271: "Fabrikant", 272: "Kameramodel", 305: "Software"}
            
            for tag_id, tag_name in important_tags.items():
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='ignore')
                    self.data["Enheds_Info"][tag_name] = str(value)
                    print(f"[*] {tag_name}: {value}")
        except Exception:
            pass
    
    def _integrity_check(self):
        """Check file integrity"""
        print(f"\n[*] Integrity Check...")
        modsigende = []
        
        if (self.data["Temporal_Data"]["Oprettet"] and self.data["Temporal_Data"]["Ændret"]):
            if self.data["Temporal_Data"]["Oprettet"] != self.data["Temporal_Data"]["Ændret"]:
                modsigende.append("Timestamps differ")
        
        self.data["Integritetstjek"]["Modsigende_Felter"] = modsigende
        
        if modsigende:
            print(f"[!] ANOMALIES DETECTED")
            self.data["Integritetstjek"]["Bevis"] = "CRITICAL"
        else:
            print(f"[✓] Clean")
            self.data["Integritetstjek"]["Bevis"] = "OK"
    
    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/10_FORENSIK_{os.path.basename(self.file_path).replace('.', '_')}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"\n[✓] Report saved: {filename}")

# ==========================================
# MODULE 12: REVERSE PHONE INTELLIGENCE
# ==========================================
class ReversePhoneIntelligence:
    """True Reverse lookup med Kontekst-Injektion og Data-Fletning"""
    def __init__(self, phone, context_data=None, save_path=None):
        self.raw_phone = phone.replace(" ", "").replace("+45", "").replace("-", "")
        self.save_path = save_path
        
        # Hvis vi pivoterer fra et andet modul, overtager vi deres JSON-data
        self.data = context_data if context_data else {
            "Telefon": f"+45 {self.raw_phone}",
            "Identificeret_Navn": "Ukendt",
            "Lokation": "Ukendt",
            "Timestamp": datetime.now().isoformat()
        }
        
        # Opretter en dedikeret sektion i JSON-filen til telefon-efterretning
        if "Telefon_Efterretning" not in self.data:
            self.data["Telefon_Efterretning"] = {"Kilder": [], "SoMe_Spor": []}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[12] Find ejer af ukendt telefonnummer\n{'='*60}{C.RESET}")
        print(f"Søger på: +45 {self.raw_phone}\n")
        
        # Tjekker om vi allerede kender identiteten (F.eks. fra Modul 01)
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
                        print(f"{C.YELLOW}    [-] Intet match på Krak (Muligvis hemmeligt nummer){C.RESET}")
                except Exception: pass

        # 2. Advanced Dorking & SoMe Spor
        print(f"\n{C.YELLOW}[*] Graver efter sociale netværk og MobilePay links...{C.RESET}")
        
        wa_url = f"https://wa.me/45{self.raw_phone}"
        mp_url = f"https://box.mobilepay.dk/pay?phone={self.raw_phone}"
        
        print(f"    -> WhatsApp Direct: {wa_url} (Tjek profilbillede manuelt)")
        print(f"    -> MobilePay Check: {mp_url} (Brug app for at bekræfte navn)")
        
        self.data["Telefon_Efterretning"]["SoMe_Spor"].extend([wa_url, mp_url])
        
        # TrueCaller Dorking for at fange spam/hemmelige numre
        dork = f'"{self.raw_phone}" OR "+45 {self.raw_phone}" site:truecaller.com OR site:sync.me'
        if safe_get_with_retry(driver, f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}"):
            links = extract_duckduckgo_links(driver, max_links=2)
            for link in links:
                print(f"{C.GREEN}    ✓ Databasedump fundet: {link['url']}{C.RESET}")
                self.data["Telefon_Efterretning"]["Kilder"].append(link['url'])

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        # Hvis vi fik en sti fra et tidligere modul, overskriver vi den (Fletning). Ellers laver vi ny.
        filename = self.save_path if self.save_path else f"{session['loot_folder']}/12_REVERSE_PHONE_{self.raw_phone}.json"
        
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding='utf-8')
        print(f"\n{C.GREEN}[✓] Data flettet og gemt i sagmappe: {filename}{C.RESET}")

# ==========================================
# MODULE 13: REVERSE IMAGE INTELLIGENCE
# ==========================================
class ReverseImageIntelligence:
    def __init__(self, image_path):
        self.image_path = image_path.strip()
        self.data = {
            "Billede": os.path.basename(image_path),
            "Yandex_URL": "",
            "Google_Klar": False,
            "Bing_Klar": False,
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[13] Omvendt Billedsøgning (Yandex + Google + Bing)\n{'='*60}{C.RESET}")
        
        if not os.path.exists(self.image_path):
            print(f"{C.RED}[!] Billede ikke fundet: {self.image_path}{C.RESET}")
            return
            
        self._analyze_authenticity()
        self._check_google_bing(driver)
        self._yandex_auto_upload(driver)
        self.save()

    def _check_google_bing(self, driver):
        """Tjekker om portalerne er tilgængelige for manuel søgning"""
        print(f"\n{C.YELLOW}[*] Checker adgang til Google Lens og Bing Visual...{C.RESET}")
        try:
            if safe_get_with_retry(driver, "https://www.google.com/imghp"):
                print(f"{C.GREEN}    ✓ Google Images er tilgængelig{C.RESET}")
                self.data["Google_Klar"] = True
            if safe_get_with_retry(driver, "https://www.bing.com/images"):
                print(f"{C.GREEN}    ✓ Bing Images er tilgængelig{C.RESET}")
                self.data["Bing_Klar"] = True
        except Exception: pass

    def _yandex_auto_upload(self, driver):
        """Udfører den automatiske ansigts/billede søgning på Yandex"""
        print(f"\n{C.YELLOW}[*] Auto-uploader {os.path.basename(self.image_path)} til Yandex...{C.RESET}")
        try:
            driver.get("https://yandex.com/images/")
            time.sleep(2)
            cam_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Image search'], button[title='Image search']")
            if cam_btn: cam_btn[0].click()
            else: driver.get("https://yandex.com/images/search?rpt=imageview")
            
            time.sleep(2)
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(self.image_path))
            
            print(f"{C.CYAN}    [*] Uploader billede og analyserer...{C.RESET}")
            # Vi venter max 20 sek på at url'en skifter væk fra upload-siden ELLER et resultat popper op
            WebDriverWait(driver, 20).until(
                lambda d: "rpt=imageview" not in d.current_url or len(d.find_elements(By.CSS_SELECTOR, ".CbirItem")) > 0
            )
            
            self.data["Yandex_URL"] = driver.current_url
            print(f"{C.GREEN}    ✓ Yandex Analyse færdig!{C.RESET}")
            print(f"{C.CYAN}    -> RESULTAT LINK: {self.data['Yandex_URL'][:80]}...{C.RESET}")
            
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved Yandex upload: {e}{C.RESET}")

    def _analyze_authenticity(self):
        """Dit originale integritets-tjek"""
        print(f"{C.YELLOW}[*] Lokal Authenticity Analysis{C.RESET}")
        try:
            img = Image.open(self.image_path)
            score = 0
            if hasattr(img, '_getexif') and img._getexif(): score += 20
            if img.size[0] > 1920: score += 15
            print(f"{C.GREEN}    ✓ Metadata og Opløsning analyseret. Score: {score}{C.RESET}")
        except Exception: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/13_REVERSE_IMAGE_{os.path.basename(self.image_path).replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# OPTIMIZATION #2: SAFE DRIVER ACTION
# ==========================================

def safe_driver_action(driver, action_func, timeout=10, action_name=""):
    """Wrapper for Selenium operations with error handling"""
    try:
        return action_func(driver)
    except TimeoutException:
        return None
    except NoSuchElementException:
        return None
    except Exception:
        return None

# ==========================================
# OPTIMIZATION #3: RETRY LOGIC
# ==========================================

def safe_get_with_retry(driver, url, max_retries=2, backoff_base=3):
    """Retry logic optimized for Tor network"""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return True
        except TimeoutException:
            if attempt < max_retries - 1:
                wait_time = backoff_base ** (attempt + 1) + random.uniform(2, 5)
                time.sleep(wait_time)
        except Exception:
            pass
    return False

# ==========================================
# OPTIMIZATION #4: PHONE EXTRACTION
# ==========================================

def extract_danish_phones(text):
    """Extract Danish phone numbers from text"""
    pattern = r'(?:^|\s)(\d{2})\s*(\d{2})\s*(\d{2})\s*(\d{2})(?:\s|$|[^\d])'
    matches = re.findall(pattern, text, re.MULTILINE)
    phones = set()
    for match in matches:
        phone = ''.join(match)
        if phone.isdigit() and len(phone) == 8:
            phones.add(phone)
    return phones

# ==========================================
# OPTIMIZATION #5: LINK EXTRACTION
# ==========================================

def extract_duckduckgo_links(driver, max_links=5):
    """Extract links from DuckDuckGo search results"""
    links = []
    selectors = [".result__a", "a.result__title", "a[href*='uddg=']", ".result"]
    
    for selector in selectors:
        try:
            elements = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            if elements:
                for el in elements[:max_links]:
                    try:
                        href = el.get_attribute("href")
                        if href:
                            if "uddg=" in href:
                                href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                            if href.startswith(('http://', 'https://')):
                                links.append({"url": href, "text": el.text.strip()})
                    except Exception as e:
                        print(f"{C.DIM}    [Debug] Kunne ikke parse link: {str(e)[:50]}{C.RESET}")
                        continue
            if links:
                    return links
        except Exception:
            continue
    return links

# ==========================================
# OPTIMIZATION #6: STEALTH DRIVER
# ==========================================

# ==========================================
# OPTIMIZATION #5.5: OMNI SEARCH ENGINE (ANTI-BAN)
# ==========================================
def omni_dork_search(driver, query, max_links=5):
    """Kører OSINT dorks. Skifter auto-magisk til Bing, hvis DuckDuckGo blokerer."""
    links = []
    
    # FORSØG 1: DuckDuckGo (HTML)
    ddg_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, ddg_url, max_retries=1):
        links = extract_duckduckgo_links(driver, max_links)
        if links: return links # Succes!
        
        # Hvis siden loader, men der ingen links er, kan det være en "Redirect/Bot" blokering.
        if "Redirecting" in driver.title or "Robot" in driver.title:
            print(f"{C.DIM}    [*] DDG Blokeret. Skifter til Bing Fallback...{C.RESET}")
    
    # FORSØG 2: Bing (Fallback)
    bing_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, bing_url, max_retries=2):
        zap_cookies(driver) # Bing har ofte cookie-popups
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
            for el in elements[:max_links]:
                href = el.get_attribute("href")
                if href and "microsoft.com" not in href and "bing.com" not in href:
                    links.append({"url": href, "text": el.text.strip()})
            return links
        except Exception: pass
        
    return links

def get_stealth_driver():
    """Undetected Chromedriver der bypasser Cloudflare og bot-beskyttelse"""
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # --- NYT: PROXY / TOR ROUTING FOR CHROME ---
    if CONFIG.get("use_tor_proxy"):
        proxy = CONFIG["tor_proxy_url"]
        options.add_argument(f'--proxy-server={proxy}')
    
    # uc.Chrome håndterer automatisk at fjerne "webdriver" flaget
    driver = uc.Chrome(options=options)
    
    driver.implicitly_wait(3)
    driver.set_page_load_timeout(15)
    return driver

# ==========================================
# OPTIMIZATION #7: COOKIE HANDLING
# ==========================================

def zap_cookies(driver):
    """Accept cookies automatically"""
    terms = ['Accepter', 'OK', 'Godkend', 'Tillad', 'Accept all']
    
    try:
        xpath = "//button[" + " or ".join([f"contains(., '{t}')" for t in terms]) + "]"
        btns = WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        if btns:
            btns[0].click()
            time.sleep(0.5)
            return True
    except Exception:
        pass
    
    try:
        selectors = ["button.cookie-accept", "button[class*='cookie']", "button[class*='consent']"]
        for selector in selectors:
            try:
                btn = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                btn.click()
                time.sleep(0.5)
                return True
            except Exception:
                continue
    except Exception:
        pass
    
    return False

# ==========================================
# MAIN MENU
# ==========================================

def get_input(prompt_text, session_key):
    """Henter input og foreslår den tidligere værdi fra sessionen"""
    default = session.get(session_key, "")
    if default:
        val = input(f"{C.CYAN}{prompt_text} [{default}]: {C.RESET}").strip()
        if not val:  # Hvis brugeren bare trykker ENTER
            return default
    else:
        val = input(f"{C.CYAN}{prompt_text}: {C.RESET}").strip()
    
    session[session_key] = val
    return val

class AutomatedCaseReporter:
    """Genererer en professionel rapport over alle fundne beviser"""
    def __init__(self):
        self.loot_dir = session["loot_folder"]
        self.report_file = f"REPORT_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

    def generate(self):
        files = list(Path(self.loot_dir).glob("*.json"))
        report_path = f"FINAL_REPORT_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        report = [f"# OSINT INTELLIGENCE MISSION REPORT\n**Sag:** {session.get('name', 'Ukendt')}\n**Dato:** {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"]
        
        # 1. HIGH PRIORITY SUMMARY (Gennemsøger alle JSON filer for guld)
        report.append("## 🚨 KRITISKE FUND (Opsummering)")
        all_cpr, all_bank, all_crypto = set(), set(), set()
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                # Leder efter data i TITAN format
                if "Case_Intelligence" in data:
                    intel = data["Case_Intelligence"]
                    all_cpr.update(intel.get("ID_Documents", {}).get("CPR_Numre", []))
                    all_bank.update(intel.get("Financial_Leads", {}).get("Bankkonti", []))
                # Leder efter crypto
                if "crypto" in data:
                    for c in data["crypto"]: all_crypto.add(c['val'])
            except Exception: continue
            
        report.append(f"* **CPR-numre identificeret:** {len(all_cpr)}")
        for c in all_cpr: report.append(f"  - {c}")
        report.append(f"* **Bankkonti fundet:** {len(all_bank)}")
        report.append(f"* **Kryptovaluta adresser:** {len(all_crypto)}")
        report.append("\n---\n## 🔗 Alle fundne links\n")
        
        # Tilføjer alle links fundet i sessionen
        for link in set(session.get("found_links", [])):
            report.append(f"* {link}")

        Path(report_path).write_text("\n".join(report), encoding='utf-8')
        print(f"{C.GREEN}[✓] TOTAL-RAPPORT GENERERET: {report_path}{C.RESET}")

# ==========================================
# MODULE 16: GOLIATH TITAN (THE ULTIMATE FORENSIC SUITE)
# ==========================================

class AutoForensicMassScanner:
    """TITAN Orchestrator: Den mest komplette kombination af OSINT og digital forensik."""
    def _convert_to_degrees(self, value):
        """Hjælpefunktion til at konvertere EXIF GPS til decimaler."""
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    
    def __init__(self, folder_path):
        self.folder_path = folder_path.strip()
        self.start_time = time.time()
        
        self.master_data = {
            "Meta": {"Sagsmappe": self.folder_path, "Timestamp": datetime.now().isoformat(), "Filer_Behandlet": 0},
            "Case_Intelligence": {
                "Verified_Identities": {}, # Navne med confidence score og kilde
                "Digital_Footprint": {"Emails": {}, "Social_Handles": set(), "IP_Adresser": set()},
                "Financial_Leads": {"Bankkonti": set(), "Crypto_Seeds": [], "Keys_Secrets": [], "CVR": set()},
                "Physical_Leads": {"Adresser": set(), "Nummerplader": set(), "GPS_Data": []},
                "ID_Documents": {"MRZ_Koder": [], "CPR_Numre": set(), "Pasnumre": set()},
                "Timeline": {"Datoer_Fundet": set()}
            },
            "Metadata_Report": {}, # EXIF data (GPS/Tid)
            "Source_Map": {},      # Relation mellem data og filnavn
            "File_Integrity_Alerts": [], # Magic byte mismatches
            "Berigelse_Resultater": {"Phone_Data": [], "Breach_Reports": []},
            "Raw_Text_Archive": {} # ALT tekst gemmes ordret her
        }
        self.noise_list = ["Matas", "Apple", "Google", "Lunar", "Faktura", "Store", "Support", "Maria Casino", "Gældsstyrelsen", "Danske Spil", "Danske Inkasso"]

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[16] GOLIATH TITAN: FULL SPECTRUM FORENSICS\n{'='*60}{C.RESET}")
        if not os.path.exists(self.folder_path): 
            print(f"{C.RED}[!] Fejl: Stien findes ikke.{C.RESET}"); return
        
        # 1. DEEP UNPACKING
        self._unpack_archives()

        # 2. PARALLEL TITAN ENGINE (8 tråde for max speed)
        files = [f for f in glob.glob(f"{self.folder_path}/**/*", recursive=True) if os.path.isfile(f)]
        self.master_data["Meta"]["Filer_Behandlet"] = len(files)

        print(f"[*] Starter synkroniseret analyse af {len(files)} enheder via 8 CPU-processer...")
        completed = 0
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._titan_process_file, f): f for f in files}
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                self._print_progress(completed, len(files))
                try:
                    res = future.result()
                    if res: self._ingest_results(res)
                except Exception as e:
                    print(f"\n{C.RED} [!] TITAN Crash i fil: {e}{C.RESET}")
        
        print(f"\n{C.GREEN}[✓] Forensic Pipeline komplet. Starter automatisk berigelse...{C.RESET}")
        self._auto_pivot_engine(driver)
        self._save_master_file()
        # Terminal Summary for analytikeren
        print(f"\n{C.CYAN}--- TITAN MISSION SUMMARY ---{C.RESET}")
        print(f"Emails fundet: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['Emails'])}")
        print(f"Bankkonti fundet: {len(self.master_data['Case_Intelligence']['Financial_Leads']['Bankkonti'])}")
        print(f"CPR numre fundet: {len(self.master_data['Case_Intelligence']['ID_Documents']['CPR_Numre'])}")
        
        if "Devices" in self.master_data["Case_Intelligence"]:
            print(f"Identificerede Enheder: {', '.join(self.master_data['Case_Intelligence']['Devices'].keys())}")
        print(f"{C.CYAN}----------------------------{C.RESET}")

    def _titan_process_file(self, f_path):
        fname = os.path.basename(f_path)
        res = {"file": fname, "path": f_path, "text": "", "meta": {}, "mime": "unknown", "entities": {}}
        
        # Da _unpack_archives() allerede HAR pakket indholdet ud,
        # ignorerer vi bare selve .zip filen for at spare massiv CPU-tid!
        if f_path.lower().endswith('.zip'):
            return res

        try:
            res["mime"] = magic.from_file(f_path, mime=True)

            if "image" in res["mime"]:
                # ... resten af din kode forsætter herfra ...
                res["meta"] = self._extract_exif(f_path)
                if HAS_OCR: res["text"] = self._ocr_pro(f_path)
                
            elif "pdf" in res["mime"] and HAS_PDF:
                doc = fitz.open(f_path)
                text_parts = []
                for page in doc:
                    # Hent den indlejrede tekst
                    text_parts.append(page.get_text())
                    
                    # NYT: Træk skjulte billeder/scanninger ud og OCR dem!
                    if HAS_OCR:
                        for img_idx, img in enumerate(page.get_images(full=True)):
                            try:
                                base_image = doc.extract_image(img[0])
                                tmp_img = f"/tmp/pdf_tmp_{time.time()}_{img[0]}.png"
                                with open(tmp_img, "wb") as f: f.write(base_image["image"])
                                text_parts.append(self._ocr_pro(tmp_img))
                                os.remove(tmp_img)
                            except Exception: pass
                
                res["text"] = "\n".join(text_parts)
                doc.close()
                
            elif any(x in res["mime"] for x in ["text", "json", "csv", "plain"]):
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f: res["text"] = f.read()

            if res["text"]:
                res["entities"] = self._scrub_all(res["text"])
                res["secrets"] = self._find_secrets(res["text"])
                
                # --- NYT: AI Berigelse af dokumentet ---
                if len(res["text"]) > 50:
                    ai = TitanAIEnrichment()
                    ai_data = ai.analyze_text(res["text"])
                    if ai_data:
                        res["ai_context"] = ai_data
                        print(f"\n{C.GREEN}    🧠 AI Fandt Kontekst i {fname}: {ai_data.get('navne', [])}{C.RESET}")
        except Exception: pass
        return res

    def _ocr_pro(self, path):
        """OpenCV Pre-processing med MAX opløsning for memory-sikkerhed."""
        try:
            img = cv2.imread(path)
            if img is None: return ""
            
            # OPTIMERING: Tving max bredde på 2500px, bevar aspect ratio
            height, width = img.shape[:2]
            max_dimension = 2500
            if width > max_dimension or height > max_dimension:
                scaling_factor = max_dimension / float(max(width, height))
                img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            text = pytesseract.image_to_string(thresh, config='--psm 3 --oem 3')
            
            if "<" in text or "PAS" in text.upper() or "DANMARK" in text.upper():
                text += "\n" + pytesseract.image_to_string(thresh, config='--psm 11')
            return text
        except Exception as e: return ""

    def _scrub_all(self, text):
        e = {"emails": [], "bank": [], "cpr": [], "mrz": [], "secrets": [], "crypto": []}
        
        for mail in REGEX_EMAIL.findall(text):
            e["emails"].append({"val": mail.lower(), "score": 100})
            
        e["bank"] = REGEX_BANK.findall(text)
        e["cpr"] = REGEX_CPR.findall(text)
        
        for m in REGEX_BTC.findall(text): e["crypto"].append({"type": "Bitcoin_Addr", "val": m})
        for m in REGEX_ETH.findall(text): e["crypto"].append({"type": "Ethereum_Addr", "val": m})
        
        # ... fortsæt logik
        return e

    def _sanitize_email(self, email):
        """Retter gængse OCR-fejl i domænenavne for at undgå 'hotmail.cona'."""
        replacements = {
            ".cona": ".com", ".con": ".com", "hotmell": "hotmail",
            "hotmall": "hotmail", "gmaill": "gmail", "gmall": "gmail",
            "outloook": "outlook", "live.dkk": "live.dk"
        }
        for fault, fix in replacements.items():
            email = email.replace(fault, fix)
        return email

    def _find_secrets(self, text):
        """Leder efter Crypto Seeds og Keys (GitHub Intelligence)."""
        secrets = []
        mnemonic = re.findall(r'\b(?:[a-z]{3,12}\s){11,23}[a-z]{3,12}\b', text.lower())
        if mnemonic: secrets.append({"type": "Crypto_Mnemonic", "val": mnemonic})
        keys = re.findall(r'\b(?:AIza[0-9A-Za-z-_]{35}|[0-9a-f]{64})\b', text)
        if keys: secrets.append({"type": "API_Key_or_Hash", "val": keys})
        return secrets

    def _auto_pivot_engine(self, driver):
        """Intelligent Orchestrator: Beriger automatisk de fundne spor."""
        intel = self.master_data["Case_Intelligence"]
        print(f"\n{C.CYAN}{'='*60}\nBERIGELSE: GOLIATH TITAN ORCHESTRATOR\n{'='*60}{C.RESET}")

        emails = [e for e, data in sorted(intel["Digital_Footprint"]["Emails"].items(), key=lambda x: x[1]['score'], reverse=True)[:5]]
        for email in emails:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] {C.YELLOW}[*] Deep-Scan: Email {email}...{C.RESET}")
            mod = BreachIntelligenceAnalyst(email); mod.save = lambda: None
            try: 
                mod.run(driver)
                self.master_data["Berigelse_Resultater"]["Breach_Reports"].append(mod.data)
            except Exception: pass
            time.sleep(random.uniform(3, 6))

    def _ingest_results(self, res):
        intel = self.master_data["Case_Intelligence"]
        # Din eksisterende ingest logik her...
        
        # NYT: Saml statistik over enheder (iPhone, Samsung, etc.)
        if res.get("meta") and "Make" in res["meta"]:
            device = f"{res['meta'].get('Make')} {res['meta'].get('Model')}"
            if "Devices" not in intel: 
                intel["Devices"] = {}
            # Tæller hvor mange gange hver enhed optræder
            intel["Devices"][device] = intel["Devices"].get(device, 0) + 1

    def _extract_exif(self, path):
        meta = {}
        try:
            with Image.open(path) as img:
                info = img._getexif()
                if info:
                    for tag, value in info.items():
                        decoded = TAGS.get(tag, tag)
                        
                        # --- NY GPS LOGIK ---
                        if decoded == 'GPSInfo':
                            gps_link = self._get_gps_link(value)
                            if gps_link:
                                meta['GPS_Link'] = gps_link
                                print(f"{C.YELLOW}    📍 GPS FUNDET: {gps_link}{C.RESET}")
                        elif decoded in ['DateTime', 'Make', 'Model']: 
                            meta[decoded] = str(value)
        except Exception as e: 
            print(f"{C.DIM}    [Debug] EXIF Fejl: {e}{C.RESET}")
        return meta

    def _print_progress(self, current, total):
        pct = int((current / total) * 100)
        bar = "█" * (pct // 2) + "-" * (50 - (pct // 2))
        print(f"\r{C.YELLOW}[*] TITAN-SCAN: |{bar}| {pct}% ({current}/{total}){C.RESET}", end="", flush=True)

    def _save_master_file(self):
        """Gemmer rapporten og sikrer at ALLE 'sets' konverteres til lister for at undgå crash."""
        def convert_sets(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: convert_sets(v) for k, v in obj.items()}
            if isinstance(obj, list): return [convert_sets(i) for i in obj]
            return obj

        self.master_data["Case_Intelligence"] = convert_sets(self.master_data["Case_Intelligence"])
        
        mappe_navn = os.path.basename(os.path.normpath(self.folder_path))
        path = f"{session['loot_folder']}/16_TITAN_REPORT_{mappe_navn}_{datetime.now().strftime('%H%M%S')}.json"
        
        try:
            Path(path).write_text(json.dumps(self.master_data, indent=4, ensure_ascii=False), encoding="utf-8")
            print(f"\n{C.GREEN}[✓✓✓] TITAN MISSION FULDFØRT! FIL GEMT: {path}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Fejl under gemning: {e}{C.RESET}")

    def _unpack_archives(self):
        for zf in glob.glob(f"{self.folder_path}/**/*.zip", recursive=True):
            extract_dir = os.path.join(self.folder_path, f"_extracted_{os.path.basename(zf)[:-4]}")
            if not os.path.exists(extract_dir):
                try:
                    with zipfile.ZipFile(zf, 'r') as zip_ref: zip_ref.extractall(extract_dir)
                except Exception: pass

    # Tilføj denne hjælpefunktion i bunden af TITAN klassen
    def _get_gps_link(self, gps_info):
        try:
            if gps_info:
                def to_dec(val): 
                    return float(val[0]) + float(val[1])/60 + float(val[2])/3600
                lat = to_dec(gps_info[2]) * (-1 if gps_info[1] == 'S' else 1)
                lon = to_dec(gps_info[4]) * (-1 if gps_info[3] == 'W' else 1)
                return f"https://www.google.com/maps?q={lat},{lon}"
        except Exception: return None
        return None

# ==========================================
# MODULE 17: GOLIATH SNIPER (SURGICAL BRUTEFORCE)
# ==========================================

class GoliathSniperEngine:
    """Universal og interaktiv wordlist generator med avanceret mangling."""
    def __init__(self, name, city, cpr, clues, json_folder=None):
        self.target_name = name.strip()
        self.city = city.strip()
        self.cpr = cpr.replace("-", "").strip()
        self.clues = [c.strip() for c in clues.split(",") if c.strip()]
        self.json_folder = json_folder
        self.wordlist = set()
        
        self.name_parts = self.target_name.split()
        self.dates = self._extract_dates()
        self.seeds = set(self.name_parts + [self.city] + self.clues)
        
        if self.json_folder:
            self._ingest_json_data()

    def _extract_dates(self):
        if len(self.cpr) < 6: return ["2024", "2025", "24"]
        ddmm, yy = self.cpr[:4], self.cpr[4:6]
        yyyy = ("19" if int(yy) > 25 else "20") + yy
        return [ddmm, yy, yyyy, "2024", "24"]

    def _leetspeak(self, word):
        subs = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        res = word.lower()
        for char, repl in subs.items(): res = res.replace(char, repl)
        return res

    def _ingest_secrets(self):
        """Henter fundne passwords fra TITAN rapporter til at forbedre wordlisten."""
        for f_path in glob.glob(os.path.join(self.json_folder, "16_TITAN_*.json")):
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    secrets = data.get("Case_Intelligence", {}).get("secrets", [])
                    for s in secrets:
                        if s.get("type") == "Generic_Secret":
                            self.seeds.add(s.get("val"))
                            print(f"{C.GREEN}    [+] Sniper genbruger fundet secret: {s.get('val')[:5]}...{C.RESET}")
            except Exception: continue

    def generate(self):
        print(f"\n{C.CYAN}[17] STARTER SNIPER-ENGINE FOR: {self.target_name.upper()}{C.RESET}")
        suffixes = ["!", "123", "!", "#", "_", ".", "2024"]
        
        print("[*] Skaber avancerede ord-kombinationer...")
        for combo in itertools.permutations(list(self.seeds), 2):
            self.wordlist.add(f"{combo[0].capitalize()}{combo[1].lower()}")
            self.wordlist.add(f"{combo[0].lower()}{combo[1].lower()}")

        for base in self.seeds:
            for d in self.dates:
                for s in suffixes:
                    for m in [base.lower(), base.capitalize(), self._leetspeak(base)]:
                        self.wordlist.add(f"{m}{d}")
                        self.wordlist.add(f"{m}{d}{s}")
                        self.wordlist.add(f"{m}{s}{d}")
        self._save()

    def _save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        path = os.path.join(session["loot_folder"], f"17_SNIPER_{self.target_name.replace(' ', '_')}.txt")
        final = sorted(list(self.wordlist), key=lambda x: (not any(c in x for c in self.clues), len(x)))
        with open(path, "w", encoding="utf-8") as f:
            for w in final:
                if 6 <= len(w) <= 20: f.write(f"{w}\n")
        print(f"{C.GREEN}[✓] WORDLIST KLAR: {path} ({len(final)} ord){C.RESET}")


# ==========================================
# MODULE 18: GOLIATH MAIL-RIPPER (DIRECT IMAP)
# ==========================================

class GoliathMailRipper:
    """Tømmer mailkontoen hurtigt og gemmer alt lokalt (inkl. attachments)."""
    def __init__(self, user, app_password):
        self.user = user
        self.pwd = app_password.replace(" ", "")
        self.host = "imap-mail.outlook.com"
        self.save_dir = os.path.join("loot", f"RIP_{user.split('@')[0]}")

    def run(self):
        print(f"\n{C.CYAN}[18] FORBINDER TIL {self.user}...{C.RESET}")
        try:
            mail = imaplib.IMAP4_SSL(self.host)
            mail.login(self.user, self.pwd)
            
            _, folders = mail.list()
            for f in folders:
                f_name = f.decode().split(' "/" ')[-1].strip('"')
                print(f"[*] Ripper mappe: {f_name}")
                self._rip_folder(mail, f_name)
                
            mail.logout()
            print(f"\n{C.GREEN}[✓] RIP COMPLETE. Data gemt i: {self.save_dir}{C.RESET}")
        except Exception as e:
            if "BasicAuthBlocked" in str(e):
                print(f"{C.RED}[!] FEJL: Microsoft blokerer. Du SKAL bruge 'App Password'.{C.RESET}")
            else:
                print(f"{C.RED}[!] Systemfejl: {e}{C.RESET}")

    # I stedet for at hente 'ALL', beder vi serveren om kun at returnere 
    # mails der indeholder "password", "kode", "lunar" osv.
    def _rip_folder_smart(self, mail, folder):
        mail.select(f'"{folder}"')
        
        # Server-side søgning (Meget hurtigere, sparer båndbredde)
        search_criteria = '(OR OR BODY "password" BODY "kode" BODY "lunar")'
        status, messages = mail.search(None, search_criteria)
        
        if status == 'OK' and messages[0]:
            mail_ids = messages[0].split()
            print(f"[*] Fandt {len(mail_ids)} høj-værdi mails i {folder}. Downloader...")
            for num in mail_ids:
                # Her henter den faktisk mailen og sender den til save_content
                _, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                self._save_content(msg, folder, num.decode())

    def _save_content(self, msg, folder, mid):
        # Dette er koden du manglede, som faktisk downloader og gemmer mails!
        subject, encoding = decode_header(msg.get("Subject", "Ingen emne"))[0]
        if isinstance(subject, bytes): subject = subject.decode(encoding or "utf-8", errors="ignore")
        
        safe_subject = "".join([c for c in str(subject) if c.isalnum() or c in (' ', '_')]).rstrip()
        folder_path = os.path.join(self.save_dir, folder.replace("/", "_"))
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, f"{mid}_{safe_subject[:50]}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Fra: {msg.get('From')}\nEmne: {subject}\n{'-'*50}\n")
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        f.write(part.get_payload(decode=True).decode(errors="ignore"))
                    elif part.get_filename(): # Gemmer vedhæftede filer (PDF, billeder etc)
                        attach_dir = os.path.join(folder_path, "attachments")
                        os.makedirs(attach_dir, exist_ok=True)
                        with open(os.path.join(attach_dir, f"{mid}_{part.get_filename()}"), "wb") as af:
                            af.write(part.get_payload(decode=True))
            else:
                f.write(msg.get_payload(decode=True).decode(errors="ignore"))

# ==========================================
# MODULE 19: BLOCKCHAIN LEDGER ANALYZER (FOLLOW THE MONEY)
# ==========================================
class CryptoLedgerAnalyzer:
    def __init__(self, address):
        self.address = address.strip()
        self.data = {"Adresse": self.address, "Valuta": "Ukendt", "Balance": 0, "Total_Modtaget": 0, "Transaktioner": 0, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[19] Blockchain Efterretning (Crypto-Sporing)\n{'='*60}{C.RESET}")
        print(f"[*] Analyserer krypto-adresse: {self.address}")

        if self.address.startswith("1") or self.address.startswith("3") or self.address.startswith("bc1"):
            self.data["Valuta"] = "Bitcoin (BTC)"
            self._trace_btc()
        elif self.address.startswith("0x"):
            self.data["Valuta"] = "Ethereum (ETH)"
            self._trace_eth()
        else:
            print(f"{C.RED}[!] Ukendt kæde-format. Understøtter BTC og ETH.{C.RESET}")

        self.save()

    def _trace_btc(self):
        try:
            print(f"{C.YELLOW}[*] Forbinder til Bitcoin Blockchain API...{C.RESET}")
            res = requests.get(f"https://blockchain.info/rawaddr/{self.address}", timeout=10).json()
            self.data["Balance"] = res.get("final_balance", 0) / 100000000
            self.data["Total_Modtaget"] = res.get("total_received", 0) / 100000000
            self.data["Transaktioner"] = res.get("n_tx", 0)

            print(f"{C.GREEN}    ✓ Netværk: Bitcoin{C.RESET}")
            print(f"{C.GREEN}    ✓ Aktuel Balance: {self.data['Balance']} BTC{C.RESET}")
            print(f"{C.GREEN}    ✓ Total Modtaget: {self.data['Total_Modtaget']} BTC{C.RESET}")
            print(f"{C.GREEN}    ✓ Antal Transaktioner: {self.data['Transaktioner']}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [-] Fejl ved BTC opslag: Kunne ikke finde adresse.{C.RESET}")

    def _trace_eth(self):
        try:
            print(f"{C.YELLOW}[*] Forbinder til Etherscan API...{C.RESET}")
            res = requests.get(f"https://api.etherscan.io/api?module=account&action=balance&address={self.address}&tag=latest", timeout=10).json()
            if res.get("status") == "1":
                bal = int(res.get("result", 0)) / 10**18
                self.data["Balance"] = bal
                print(f"{C.GREEN}    ✓ Netværk: Ethereum{C.RESET}")
                print(f"{C.GREEN}    ✓ Aktuel Balance: {bal:.4f} ETH{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen data fundet på Etherscan.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [-] Fejl ved ETH opslag: {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/19_CRYPTO_{self.address[:10]}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 20: VEHICLE INTELLIGENCE (NUMMERPLADE-OSINT)
# ==========================================
class VehicleIntelligence:
    def __init__(self, reg_nr):
        self.reg = reg_nr.upper().replace(" ", "").replace("-", "")
        self.data = {"RegNr": self.reg, "Mærke_Model": "", "Stelnummer": "", "Status": "", "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[20] Køretøjs-Efterretning (Nummerpladeopslag)\n{'='*60}{C.RESET}")
        print(f"[*] Slår nummerplade op: {self.reg}")

        url = f"https://www.tjekbil.dk/nummerplade/{self.reg}/overblik"
        if safe_get_with_retry(driver, url):
            zap_cookies(driver)
            time.sleep(2)
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                stel_match = re.search(r'(?i)(?:stelnummer|vin)[:\s]+([A-Z0-9]{17})', body_text)
                if stel_match:
                    self.data["Stelnummer"] = stel_match.group(1)
                    print(f"{C.GREEN}    ✓ Stelnummer (VIN) fundet: {self.data['Stelnummer']}{C.RESET}")

                try:
                    h1 = driver.find_element(By.TAG_NAME, "h1").text
                    self.data["Mærke_Model"] = h1.replace("Tjekbil", "").strip()
                    print(f"{C.GREEN}    ✓ Køretøj: {self.data['Mærke_Model']}{C.RESET}")
                except Exception: pass

                if "Afgemeldt" in body_text or "Afmeldt" in body_text:
                    self.data["Status"] = "Afmeldt"
                else:
                    self.data["Status"] = "Aktiv"
                print(f"{C.GREEN}    ✓ Status: {self.data['Status']}{C.RESET}")

            except Exception as e:
                print(f"{C.YELLOW}    [-] Kunne ikke udtrække alt data automatisk. Tjek manuelt: {url}{C.RESET}")
        else:
            print(f"{C.RED}    [-] Kunne ikke forbinde til motor-registret.{C.RESET}")
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/20_VEHICLE_{self.reg}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 21: BSSID GEOFENCER (WIFI LOKATIONS-SPORING)
# ==========================================
class BSSIDGeofencer:
    def __init__(self, bssid):
        self.bssid = bssid.strip().replace("-", ":").lower()
        self.data = {"BSSID": self.bssid, "Fundet": False, "Lat": None, "Lon": None, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[21] BSSID Geofencer (MAC Lokations-sporing)\n{'='*60}{C.RESET}")
        print(f"[*] Søger efter router MAC i global database: {self.bssid}")

        # Bruger Mylnikov Open Wifi API (Åben database)
        url = f"https://api.mylnikov.org/geolocation/wifi?v=1.1&data={self.bssid}"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("result") == 200:
                self.data["Fundet"] = True
                self.data["Lat"] = res["data"]["lat"]
                self.data["Lon"] = res["data"]["lon"]

                maps_url = f"https://www.google.com/maps?q={self.data['Lat']},{self.data['Lon']}"

                print(f"{C.GREEN}    🔥 BINGO! Fysisk lokation fastslået!{C.RESET}")
                print(f"{C.GREEN}    ✓ Breddegrad: {self.data['Lat']}{C.RESET}")
                print(f"{C.GREEN}    ✓ Længdegrad: {self.data['Lon']}{C.RESET}")
                print(f"{C.CYAN}    -> Google Maps: {maps_url}{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Routeren findes ikke i de åbne databaser.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved API opslag: {e}{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/21_BSSID_{self.bssid.replace(':', '')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 22: TELEGRAM & DISCORD INTELLIGENCE
# ==========================================
class ChatAppIntelligence:
    """Specialiseret søgning i lukkede økosystemer (Telegram, Discord, Signal)"""
    def __init__(self, query):
        self.query = query.strip()
        self.data = {"Søgeord": self.query, "Telegram_Hits": [], "Discord_Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[22] Chat App Intelligence (Telegram & Discord)\n{'='*60}{C.RESET}")
        print(f"[*] Afdækker lukkede netværk for: {self.query}")

        # Telegram Dorking (Leder efter t.me links og telegra.ph)
        print(f"{C.YELLOW}[*] Scanner Telegram økosystemet...{C.RESET}")
        tg_dork = f'"{self.query}" site:t.me OR site:telegra.ph'
        tg_links = omni_dork_search(driver, tg_dork, max_links=5)
        for link in tg_links:
            print(f"{C.GREEN}    ✓ TELEGRAM SPOR: {link['url']}{C.RESET}")
            self.data["Telegram_Hits"].append(link['url'])

        # Discord Dorking (Leder efter invite links og server logs)
        print(f"\n{C.YELLOW}[*] Scanner Discord servere...{C.RESET}")
        dc_dork = f'"{self.query}" site:discord.com/invite OR site:discord.gg'
        dc_links = omni_dork_search(driver, dc_dork, max_links=5)
        for link in dc_links:
            print(f"{C.GREEN}    ✓ DISCORD INVITE: {link['url']}{C.RESET}")
            self.data["Discord_Hits"].append(link['url'])

        if not tg_links and not dc_links:
            print(f"{C.DIM}    [-] Ingen offentlige chat-spor fundet.{C.RESET}")
            
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/22_CHATAPP_{self.query.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 23: GLOBAL USERNAME MATRIX (SHERLOCK)
# ==========================================
class UsernameMatrixAnalyzer:
    """Scanner +300 platforme for et specifikt brugernavn via Sherlock"""
    def __init__(self, username):
        self.username = username.strip()
        self.data = {"Brugernavn": self.username, "Platforme": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[23] Global Username Matrix (Sherlock)\n{'='*60}{C.RESET}")
        print(f"[*] Scanner 300+ platforme for brugernavnet: {self.username} (Dette kan tage et par minutter)...")
        
        try:
            # Kræver at 'sherlock' er installeret via pip (pip install sherlock-project)
            result = subprocess.run(['sherlock', self.username, '--timeout', '5', '--print-found'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "[+]" in line:
                    site_url = line.split("[+]")[1].strip()
                    print(f"{C.GREEN}    🔥 PROFIL FUNDET: {site_url}{C.RESET}")
                    self.data["Platforme"].append(site_url)
                    
            if not self.data["Platforme"]:
                print(f"{C.YELLOW}    [-] Ingen profiler fundet for {self.username}.{C.RESET}")
        except FileNotFoundError:
            print(f"{C.RED}    [!] 'sherlock' er ikke installeret. Kør 'pip install sherlock-project'.{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/23_MATRIX_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")

# ==========================================
# MODULE 24: OPSEC METADATA SANITIZER
# ==========================================
class OpsecSanitizer:
    """Fjerner al EXIF og metadata fra filer, inden de deles eller uploades"""
    def __init__(self, file_path):
        self.file_path = file_path.strip()
        
    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[24] OPSEC Sanitizer (Fjern Metadata)\n{'='*60}{C.RESET}")
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Filen findes ikke.{C.RESET}"); return
            
        try:
            img = Image.open(self.file_path)
            # Kopierer kun pixels, ingen metadata
            clean_data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(clean_data)
            
            clean_path = self.file_path.rsplit('.', 1)[0] + "_CLEANED." + self.file_path.rsplit('.', 1)[1]
            clean_img.save(clean_path)
            
            print(f"{C.GREEN}    ✓ Bevis renset for metadata!{C.RESET}")
            print(f"{C.GREEN}    ✓ Sikker kopi gemt: {clean_path}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Kunne ikke rense filen (Understøtter kun billeder pt.): {e}{C.RESET}")

# ==========================================
# MODULE 25: WAYBACK MACHINE INTELLIGENCE
# ==========================================
class WaybackMachineIntelligence:
    """Tjekker Internet Archive for slettede versioner af et link/domæne"""
    def __init__(self, url):
        self.url = url.strip()
        self.data = {"Mål": self.url, "Arkiveret_Link": None, "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[25] Wayback Machine Intelligence\n{'='*60}{C.RESET}")
        print(f"[*] Søger i arkivet efter: {self.url}")
        try:
            res = requests.get(f"http://archive.org/wayback/available?url={self.url}", timeout=10).json()
            if "closest" in res.get("archived_snapshots", {}):
                hit = res["archived_snapshots"]["closest"]["url"]
                self.data["Arkiveret_Link"] = hit
                print(f"{C.GREEN}    🔥 ARKIVERET VERSION FUNDET: {hit}{C.RESET}")
            else:
                print(f"{C.YELLOW}    [-] Ingen arkiveret version fundet.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved arkiv-søgning: {e}{C.RESET}")
        
        # Gem logik
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/25_WAYBACK_{self.url.replace('/', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4), encoding="utf-8")

# ==========================================
# MODULE 26: VIRUSTOTAL THREAT INTEL
# ==========================================
class VirusTotalAnalyzer:
    def __init__(self, hash_or_ip):
        self.target = hash_or_ip.strip()
        self.api_key = CONFIG["api_keys"].get("virus_total", "")
        self.data = {"Target": self.target, "Malicious": 0, "Undetected": 0, "Details": {}}

    def run(self, driver=None):
        print(f"\n{C.CYAN}[26] VirusTotal Threat Intelligence{C.RESET}")
        if not self.api_key:
            print(f"{C.RED}[!] VirusTotal API-nøgle mangler i config.json{C.RESET}")
            return
            
        headers = {"x-apikey": self.api_key}
        # Auto-detekter om det er IP eller File Hash
        if "." in self.target and len(self.target) < 16:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{self.target}"
        else:
            url = f"https://www.virustotal.com/api/v3/files/{self.target}"

        try:
            res = requests.get(url, headers=headers).json()
            stats = res['data']['attributes']['last_analysis_stats']
            print(f"{C.RED}    🔥 Malicious Hits: {stats['malicious']}{C.RESET}")
            print(f"{C.GREEN}    ✓ Rene Scans: {stats['undetected']}{C.RESET}")
            self.data["Malicious"] = stats['malicious']
            # Gem logik her...
        except Exception as e:
            print(f"{C.RED}[!] Fejl ved VT API: {e}{C.RESET}")

# ==========================================
# MODULE 27: TITAN AI ENRICHMENT (LOCAL LLM)
# ==========================================
class TitanAIEnrichment:
    """Kører rå tekst gennem en lokal LLM (Ollama) for at finde skjult kontekst."""
    def __init__(self, model="llama3"):
        self.model = model
        self.api_url = "http://localhost:11434/api/generate"

    def analyze_text(self, text):
        if not text or len(text) < 20:
            return {}

        # Vi begrænser teksten for at undgå at overbelaste den lokale model
        safe_text = text[:4000] 

        prompt = """
        Du er en cyber-efterforsker. Analyser følgende tekst og uddrag de vigtigste entiteter.
        Returner KUN et validt JSON-objekt med følgende nøgler: 'navne' (liste), 'adresser' (liste), 
        'organisationer' (liste), og 'mistænkelig_adfærd' (kort string opsummering).
        Tekst:
        """ + safe_text

        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False
        }

        try:
            res = requests.post(self.api_url, json=payload, timeout=60).json()
            return json.loads(res.get("response", "{}"))
        except requests.exceptions.ConnectionError:
            print(f"{C.DIM}    [AI Offline] Ollama kører ikke på localhost:11434{C.RESET}")
            return {}
        except Exception as e:
            print(f"{C.DIM}    [AI Fejl] {e}{C.RESET}")
            return {}



# ==========================================
# MAIN MENU (PETFE Edition)
# ==========================================
def check_dependencies():
    """Tjekker om de nødvendige eksterne værktøjer og Python pakker er installeret."""
    print(f"{C.CYAN}[*] Udfører system-tjek for OMNI-HUNTER v52.0...{C.RESET}")
    
    tools = {
        "rg": "Ripgrep (Nødvendig for Modul 05)",
        "tesseract": "Tesseract OCR (Nødvendig for Modul 16)",
        "holehe": "Holehe Tracker (Nødvendig for Modul 09)"
    }
    for tool, desc in tools.items():
        if shutil.which(tool) is None:
            print(f"{C.RED}    [!] ADVARSEL: {desc} mangler på systemet!{C.RESET}")
        else:
            print(f"{C.GREEN}    [✓] System-Værktøj OK: {tool}{C.RESET}")

def main():
    global search_cache
    os.makedirs(session["loot_folder"], exist_ok=True)
    
    check_dependencies()
    search_cache = SearchCache(session["loot_folder"])
    
    first_run = True  
    w = 35 
    
    # 1. VIGTIGT: Definer browseren UDEN FOR loopet!
    stealth_browser_instance = None 
    
    while True:
        print(f"{C.CYAN}{'='*70}{C.RESET}")
        print(f"  {C.YELLOW}OSINT Final - Suite for OSINT{C.RESET}")
        print(f"  {C.RED}PETFE // Politi - Efterretningsværktøj{C.RESET}")
        print(f"{C.CYAN}{'='*70}{C.RESET}")

        line1 = f"{C.CYAN}[01]{C.RESET} Personregister (Krak/Geo)"
        print(f"{line1:<{w + 9}}{C.CYAN}[02]{C.RESET} Erhverv (CVR API)")

        line2 = f"{C.CYAN}[03]{C.RESET} Lækage-analyse (Breach)"
        print(f"{line2:<{w + 9}}{C.CYAN}[04]{C.RESET} Social Media Profiler")

        line3 = f"{C.CYAN}[05]{C.RESET} Offline DB (Ripgrep)"
        print(f"{line3:<{w + 9}}{C.CYAN}[06]{C.RESET} E-mail Mønstre")

        line4 = f"{C.CYAN}[07]{C.RESET} Telefon-efterretning"
        print(f"{line4:<{w + 9}}{C.CYAN}[08]{C.RESET} Mørkenet (Ahmia)")

        line5 = f"{C.CYAN}[09]{C.RESET} E-mail Tracker (Dyb)"
        print(f"{line5:<{w + 9}}{C.CYAN}[10]{C.RESET} IP/Netværk (API)")

        line6 = f"{C.CYAN}[11]{C.RESET} Udtræk ALT data fra billeder"
        print(f"{line6:<{w + 9}}{C.CYAN}[12]{C.RESET} Omvendt Telefonopslag")

        line7 = f"{C.CYAN}[13]{C.RESET} Omvendt Billedsøgning"
        print(f"{line7:<{w + 9}}{C.CYAN}[16]{C.RESET} Auto-Forensisk Scanner (TITAN)")

        line8 = f"{C.CYAN}[17]{C.RESET} Goliath Final Strike (Wordlist)"
        print(f"{line8:<{w + 9}}{C.CYAN}[18]{C.RESET} Mail-Ripper (IMAP)")

        line9 = f"{C.CYAN}[19]{C.RESET} Crypto Ledger Tracker (BTC/ETH)"
        print(f"{line9:<{w + 9}}{C.CYAN}[20]{C.RESET} Køretøjs-OSINT (TjekBil)")

        print(f"{C.CYAN}[21]{C.RESET} BSSID Geofencer (MAC -> GPS)")
        print(f"{C.CYAN}[22]{C.RESET} Chat App Intelligence (Telegram/Discord)")
        print(f"{C.CYAN}[23]{C.RESET} Global Username Matrix (Sherlock)")
        print(f"{C.CYAN}[24]{C.RESET} OPSEC Sanitizer (Fjern Metadata)")
        
        print(f"{C.CYAN}{'-' * 70}{C.RESET}")
        
        line_final = f"{C.GREEN}[14]{C.RESET} Generer Sagsmappe (.md)"
        print(f"{line_final:<{w + 9}}{C.RED}[15]{C.RESET} Afslut Session")
        
        print(f"{C.CYAN}{'='*70}{C.RESET}")
        
        choice = input(f"\n{C.YELLOW}Vælg Modul [01-24]: {C.RESET}").strip()
        
        if choice == "15": 
            print(f"\n{C.RED}[*] Session afsluttet. God jagt.{C.RESET}")
            if stealth_browser_instance:
                try: stealth_browser_instance.quit()
                except Exception: pass
            break
            
        if choice == "14": 
            AutomatedCaseReporter().generate()
            continue

        # ====================================================
        # KATEGORI A: Moduler der IKKE kræver Selenium Browser
        # ====================================================
        if choice in ["02", "05", "08", "09", "10", "11", "17", "18", "19", "21", "23", "24"]:
            try:
                if choice == "02":
                    BusinessIntelligenceAnalyst(get_input("Navn/Firma", "name")).run(None)
                elif choice == "05":
                    OfflineDatabaseAnalyzer(get_input("Søgeord (Navn/Email)", "db_target"), get_input("Sti til .txt dump", "db_path")).run()
                elif choice == "08":
                    DarkWebIntelligence(get_input("Søgeord", "dark_query")).run(None)
                elif choice == "09":
                    EmailTracker(get_input("Email", "email")).run(None)
                elif choice == "10":
                    IPNetworkAnalyzer(get_input("IP Adresse", "ip")).run(None)
                elif choice == "11":
                    DigitalForensicsExaminer(get_input("Sti til billede/fil", "file_path")).run()
                elif choice == "17":
                    print(f"\n{C.YELLOW}--- GOLIATH SNIPER: KONFIGURATION ---{C.RESET}")
                    name = get_input("Målets fulde navn", "name")
                    city = get_input("By", "city")
                    cpr = get_input("CPR (DDMMYY-XXXX)", "cpr") if input(f"{C.CYAN}Brug CPR? (j/n): {C.RESET}").lower() == 'j' else ""
                    clues = get_input("Clues (f.eks. hund, børn)", "clues")
                    GoliathSniperEngine(name, city, cpr, clues, session["loot_folder"]).generate()
                elif choice == "18":
                    print(f"\n{C.YELLOW}--- GOLIATH MAIL-RIPPER ---{C.RESET}")
                    email_addr = get_input("Email", "email")
                    pwd = get_input("App Password", "password")
                    GoliathMailRipper(email_addr, pwd).run()
                elif choice == "19":
                    CryptoLedgerAnalyzer(get_input("Krypto Adresse (BTC/ETH)", "crypto")).run(None)
                elif choice == "21":
                    BSSIDGeofencer(get_input("MAC Adresse / BSSID (xx:xx:xx:xx:xx)", "bssid")).run(None)
                elif choice == "23":
                    UsernameMatrixAnalyzer(get_input("Brugernavn", "username")).run(None)
                elif choice == "24":
                    OpsecSanitizer(get_input("Sti til fil", "file_path")).run(None)
            except Exception as e:
                print(f"\n{C.RED}[!] Systemfejl: {e}{C.RESET}")
            continue

        # ====================================================
        # KATEGORI B: Moduler der KRÆVER Selenium Browser
        # ====================================================
        driver = None
        try:
            if choice in ["01", "03", "04", "06", "07", "12", "13", "16", "20", "22"]:
                
                # Boot kun, hvis den ikke allerede er startet
                if stealth_browser_instance is None:
                    print(f"{C.CYAN}[*] Starter sikker browser-session (Genbruges resten af sessionen)...{C.RESET}")
                    stealth_browser_instance = get_stealth_driver()
                
                driver = stealth_browser_instance # Giv modulet adgang til den åbne browser

                if choice == "01":
                    hunter = DirectoryIntelligenceHunter(get_input("Navn", "name"), get_input("By", "city"))
                    mod_data = hunter.run(driver)
                    
                    # Indbygget Pivot til Modul 12 (Reverse Phone)
                    if mod_data.get("Telefonnumre"):
                        valg = input(f"\n{C.YELLOW}[?] Fandt telefonnummer. Vil du køre Reverse-opslag (Modul 12)? (j/n): {C.RESET}").lower()
                        if valg == 'j':
                            phone = mod_data["Telefonnumre"][0]
                            session["phone"] = phone
                            save_file = getattr(hunter, "last_saved_file", None)
                            ReversePhoneIntelligence(phone, context_data=mod_data, save_path=save_file).run(driver)

                elif choice == "03":
                    BreachIntelligenceAnalyst(get_input("Email", "email")).run(driver)
                elif choice == "04":
                    SocialMediaProfiler(get_input("Brugernavn", "username")).run(driver)
                elif choice == "06":
                    EmailPatternGenerator(get_input("Navn", "name")).run(driver)
                elif choice == "07":
                    PhoneIntelligenceHunter(get_input("Telefon (uden +45)", "phone")).run(driver)
                elif choice == "12":
                    ReversePhoneIntelligence(get_input("Ukendt Telefon (uden +45)", "phone")).run(driver)
                elif choice == "13":
                    ReverseImageIntelligence(get_input("Sti til billede", "image_path")).run(driver)
                elif choice == "16":
                    mappe = get_input("Sti til Mappe (f.eks. /home/user/leaks)", "dump_folder")
                    AutoForensicMassScanner(mappe).run(driver)
                elif choice == "20":
                    VehicleIntelligence(get_input("Nummerplade (f.eks. AB12345)", "regnr")).run(driver)
                elif choice == "22":
                    ChatAppIntelligence(get_input("Søgeord/Brugernavn", "chat_query")).run(driver)
                    
        except Exception as e:
            print(f"\n{C.RED}[!] Systemfejl under browser-session: {str(e)[:150]}{C.RESET}")

def run_module_headless(module_id, target):
    """Håndterer kørsel fra kommandolinjen uden menu"""
    logger.info(f"Starter HEADLESS kørsel: Modul {module_id} -> Mål: {target}")
    
    # Kategori A (Uden browser)
    if module_id == "02":
        BusinessIntelligenceAnalyst(target).run(None)
    elif module_id == "08":
        DarkWebIntelligence(target).run(None)
    elif module_id == "09":
        EmailTracker(target).run(None)
    elif module_id == "10":
        IPNetworkAnalyzer(target).run(None)
    else:
        print(f"{C.RED}[!] Headless opsætning mangler for modul {module_id}{C.RESET}")

if __name__ == "__main__":
    args = setup_cli()
    
    if args.headless and args.target and args.module:
        # Kører KUN modulet i baggrunden uden at åbne menuen
        run_module_headless(args.module, args.target)
    else:
        # Starter den interaktive menu, hvis ingen CLI argumenter er givet
        main()