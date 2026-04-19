# core/network.py
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

def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        default_config = {
            "use_tor_proxy": False,
            "tor_proxy_url": "socks5://127.0.0.1:9050",
            "api_keys": {
                "shodan": "",
                "hunter_io": "",
                "virus_total": "",
                "hibp_api_key": ""
            }
        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(config_path, "r") as f:
        return json.load(f)

CONFIG = load_config()

def get_hunter_session():
    req_session = requests.Session()
    req_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    
    if CONFIG.get("use_tor_proxy"):
        print(f"{C.YELLOW}[*] Ruter netværkstrafik gennem Tor/Proxy...{C.RESET}")
        req_session.proxies = {
            'http': CONFIG["tor_proxy_url"],
            'https': CONFIG["tor_proxy_url"]
        }
    
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 429, 500, 502, 503, 504 ])
    req_session.mount('http://', HTTPAdapter(max_retries=retries))
    req_session.mount('https://', HTTPAdapter(max_retries=retries))
    return req_session

http = get_hunter_session()

def safe_get_with_retry(driver, url, max_retries=2, backoff_base=3):
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
    links = []
    selectors = [".result__a", "a.result__title", "a[href*='uddg=']", ".result"]
    for selector in selectors:
        try:
            elements = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
            if elements:
                for el in elements[:max_links]:
                    try:
                        href = el.get_attribute("href")
                        if href:
                            if "uddg=" in href:
                                href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                            if href.startswith(('http://', 'https://')):
                                links.append({"url": href, "text": el.text.strip()})
                    except Exception:
                        continue
            if links:
                return links
        except Exception:
            continue
    return links

def omni_dork_search(driver, query, max_links=5):
    from core.browser import zap_cookies
    links = []
    ddg_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, ddg_url, max_retries=1):
        links = extract_duckduckgo_links(driver, max_links)
        if links: return links
        if "Redirecting" in driver.title or "Robot" in driver.title:
            print(f"{C.DIM}    [*] DDG Blokeret. Skifter til Bing Fallback...{C.RESET}")
            
    bing_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    if safe_get_with_retry(driver, bing_url, max_retries=2):
        zap_cookies(driver)
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
            for el in elements[:max_links]:
                href = el.get_attribute("href")
                if href and "microsoft.com" not in href and "bing.com" not in href:
                    links.append({"url": href, "text": el.text.strip()})
            return links
        except Exception: pass
    return links