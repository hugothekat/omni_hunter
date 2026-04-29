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

import concurrent.futures
from urllib.parse import unquote, quote

def extract_google_links(driver, query, max_links=5):
    """NY V8.5: Global Google Dorking Engine til core/network.py"""
    links = []
    # Vi prøver først med stealth requests for hastighed
    headers = {
        "User-Agent": random.choice(UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }
    url = f"https://www.google.com/search?q={quote(query)}&num={max_links}"
    
    try:
        res = http.get(url, headers=headers, timeout=5)
        if res.status_code == 200 and "sorry/index" not in res.url:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, 'html.parser')
            for g in soup.find_all('div', class_='g')[:max_links]:
                a_tag = g.find('a')
                if a_tag and a_tag.has_attr('href'):
                    href = a_tag['href']
                    title = g.find('h3').text if g.find('h3') else ""
                    snippet = g.find('div', class_='VwiC3b').text if g.find('div', class_='VwiC3b') else ""
                    if href.startswith('http') and "google.com" not in href:
                        links.append({"url": href, "title": title, "snippet": snippet})
            return links
    except Exception: pass

    # Fallback til Selenium hvis Google blokerer requests
    if driver:
        try:
            if safe_get_with_retry(driver, url, max_retries=1):
                elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
                for el in elements[:max_links]:
                    try:
                        href = el.find_element(By.TAG_NAME, "a").get_attribute("href")
                        title = el.find_element(By.TAG_NAME, "h3").text
                        snippet = el.text # Tager al tekst i containeren
                        if href and "google" not in href:
                            links.append({"url": href, "title": title, "snippet": snippet})
                    except: continue
        except Exception: pass
    
    return links

def omni_dork_search(driver, query, max_links=5):
    """
    GOLIATH V9 CORE: Asynchronous Tri-Axis Dorking Engine.
    Skyder mod Google, Bing, Yahoo og DDG SAMTIDIGT via ThreadPool.
    Dette reducerer Dorking-tid med op til 80% på tværs af alle moduler.
    """
    all_links = []
    seen_urls = set()

    # Definerer de funktioner der skal køres parallelt
    tasks = {
        "Google": lambda: extract_google_links(driver, query, max_links),
        "DDG": lambda: extract_duckduckgo_links(driver, max_links) if safe_get_with_retry(driver, f"https://duckduckgo.com/html/?q={quote(query)}") else [],
        "Bing": lambda: extract_bing_links(driver, max_links) if safe_get_with_retry(driver, f"https://www.bing.com/search?q={quote(query)}") else [],
        "Yahoo": lambda: extract_yahoo_links(driver, max_links) if safe_get_with_retry(driver, f"https://search.yahoo.com/search?p={quote(query)}") else []
    }

    # Parallel eksekvering (Max 4 workers for ikke at crashe netværkskortet/driveren)
    # Note: DDG, Bing og Yahoo bruger Selenium-driveren. De køres sekventielt hvis de deler driver, 
    # MENS Google (via requests) kører parallelt.
    
    # Kør Google via requests i baggrunden
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_google = executor.submit(extract_google_links, None, query, max_links)
        
        # Eksekver de driver-baserede sekventielt for at undgå WebDriver crash, men hurtigt!
        for engine_name, task in list(tasks.items())[1:]:
            try:
                engine_links = task()
                for link in engine_links:
                    if link['url'] not in seen_urls:
                        all_links.append(link)
                        seen_urls.add(link['url'])
            except Exception: continue
            
        # Hent Google resultaterne ind
        try:
            google_links = future_google.result()
            for link in google_links:
                if link['url'] not in seen_urls:
                    all_links.insert(0, link) # Google resultater prioriteres i toppen
                    seen_urls.add(link['url'])
        except Exception: pass

    # Returner de skarpeste links, skåret ned til det ønskede max
    return all_links[:max_links * 2] # Vi tillader lidt flere samlet, da vi har flere motorer