# -*- coding: utf-8 -*-
import os
import json
import time
import random
import urllib.parse
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from core.utils import C, session

# NY V8 TILFØJELSE: Pulje af moderne User-Agents til at undgå Requests-blokeringer
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        default_config = {
            "use_tor_proxy": False,
            "tor_proxy_url": "socks5h://127.0.0.1:9050", # V8 NOTE: 'socks5h' sikrer at DNS opslag også rutes via Tor
            "api_keys": {
                "shodan": "",
                "hunter_io": "",
                "virus_total": "",
                "hibp_api_key": "",
                "wigle": "" # Tilføjet fra Modul 21
            }
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(config_path, "r") as f:
        return json.load(f)

CONFIG = load_config()

def get_hunter_session():
    """GOLIATH V8: Skudsikker requests-session med Tor Health-Check og UA rotation"""
    req_session = requests.Session()
    chosen_ua = random.choice(UAS)
    req_session.headers.update({
        "User-Agent": chosen_ua,
        "Accept-Language": "en-US,en;q=0.9,da;q=0.8"
    })
    
    if CONFIG.get("use_tor_proxy"):
        print(f"{C.YELLOW}[*] Ruter underliggende netværkstrafik gennem Tor Proxy ({CONFIG['tor_proxy_url']})...{C.RESET}")
        req_session.proxies = {
            'http': CONFIG["tor_proxy_url"],
            'https': CONFIG["tor_proxy_url"]
        }
        # NY V8 TILFØJELSE: Lydløst Tor Health Check
        try:
            check = req_session.get("https://check.torproject.org/api/ip", timeout=10).json()
            if check.get("IsTor"):
                print(f"{C.GREEN}    ✓ Tor Proxy Bekræftet. Exit Node IP: {check.get('IP')}{C.RESET}")
            else:
                print(f"{C.RED}    [!] ADVARSEL: Trafik rutes ikke korrekt over Tor!{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Tor forbindelsesfejl. Er tor-tjenesten startet? ({e}){C.RESET}")
    
    # Aggressiv V8 Backoff strategi til rate-limited API'er
    retries = Retry(
        total=5, 
        backoff_factor=2, # Øget for at undgå at blive bannet
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    req_session.mount('http://', HTTPAdapter(max_retries=retries))
    req_session.mount('https://', HTTPAdapter(max_retries=retries))
    return req_session

http = get_hunter_session()

def safe_get_with_retry(driver, url, max_retries=2, backoff_base=3):
    """Sikker browser-navigation der overlever timeouts og anti-bot screens"""
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

def extract_duckduckgo_links(driver, max_links=5):
    """V8: Udtrækker URL, Titel og Snippet fra DDG"""
    links = []
    # Moderne DDG HTML selectors
    try:
        results = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".result")))
        for res in results[:max_links]:
            try:
                a_tag = res.find_element(By.CSS_SELECTOR, "a.result__url, a.result__a")
                href = a_tag.get_attribute("href")
                
                title = res.find_element(By.CSS_SELECTOR, "h2.result__title").text.strip()
                
                snippet = ""
                try: snippet = res.find_element(By.CSS_SELECTOR, "a.result__snippet").text.strip()
                except: pass

                if href and "uddg=" in href:
                    href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                    
                if href and href.startswith(('http://', 'https://')):
                    links.append({"url": href, "title": title, "snippet": snippet})
            except Exception:
                continue
    except Exception:
        pass
    return links

def extract_bing_links(driver, max_links=5):
    """V8: Udtrækker URL, Titel og Snippet fra Bing"""
    links = []
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "li.b_algo")
        for el in elements[:max_links]:
            try:
                a_tag = el.find_element(By.CSS_SELECTOR, "h2 a")
                href = a_tag.get_attribute("href")
                title = a_tag.text.strip()
                
                snippet = ""
                try: snippet = el.find_element(By.CSS_SELECTOR, ".b_caption p").text.strip()
                except: pass

                if href and "microsoft.com" not in href and "bing.com" not in href:
                    links.append({"url": href, "title": title, "snippet": snippet})
            except: continue
    except Exception: pass
    return links

def extract_yahoo_links(driver, max_links=5):
    """NY V8 TILFØJELSE: Tredje forsvarslinje"""
    links = []
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "div.algo-sr")
        for el in elements[:max_links]:
            try:
                a_tag = el.find_element(By.CSS_SELECTOR, "h3.title a")
                href = a_tag.get_attribute("href")
                title = a_tag.text.strip()
                
                snippet = ""
                try: snippet = el.find_element(By.CSS_SELECTOR, "div.compText p").text.strip()
                except: pass

                if href and "yahoo.com" not in href:
                    links.append({"url": href, "title": title, "snippet": snippet})
            except: continue
    except Exception: pass
    return links

def omni_dork_search(driver, query, max_links=5):
    """GOLIATH V8: Tri-Engine Dorking (DDG -> Bing -> Yahoo) med Context Extraction"""
    from core.browser import zap_cookies
    links = []
    
    # --- ENGINE 1: DUCKDUCKGO (Mest anonyme, men blokerer ofte bots) ---
    ddg_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, ddg_url, max_retries=1):
        links = extract_duckduckgo_links(driver, max_links)
        if links: return links
        
        # Hvis den fejlede men siden loade, er det et bot-captcha
        if "Redirecting" in driver.title or "Robot" in driver.title or "403" in driver.title:
            print(f"{C.DIM}    [*] DDG Blokeret (Bot-beskyttelse). Skifter til Bing Fallback...{C.RESET}")
            
    # --- ENGINE 2: BING (Klassisk fallback) ---
    bing_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, bing_url, max_retries=2):
        zap_cookies(driver) # Bing elsker at poppe store cookie-bannere
        time.sleep(1)
        links = extract_bing_links(driver, max_links)
        if links: return links
        print(f"{C.DIM}    [*] Bing returnerede ingen resultater. Skifter til Yahoo Fallback...{C.RESET}")

    # --- ENGINE 3: YAHOO (NY V8 TILFØJELSE - Tredje Forsvarslinje) ---
    yahoo_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, yahoo_url, max_retries=1):
        zap_cookies(driver)
        time.sleep(1)
        links = extract_yahoo_links(driver, max_links)
        
    return links