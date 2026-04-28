# -*- coding: utf-8 -*-
import undetected_chromedriver as uc
import random
import time
import os
import json
import re

from core.network import CONFIG
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.utils import C, session

# Udvidet pulje af moderne User-Agents for maksimal diversitet
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

def _get_fresh_options():
    """Hjælpe-funktion der sikrer vi altid får et ubrugt options-objekt"""
    from core.network import CONFIG
    import undetected_chromedriver as uc
    import random

    opt = uc.ChromeOptions()
    opt.add_argument("--headless=new") 
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1920,1080")
    opt.add_argument("--disable-notifications")
    opt.add_argument("--disable-popup-blocking")
    opt.add_argument("--lang=da-DK")
    
    # Stealth indstillinger
    opt.add_argument('--disable-blink-features=AutomationControlled')
    # Vi vælger en frisk UA her hver gang
    opt.add_argument(f'--user-agent={random.choice(UAS)}')
    
    if CONFIG.get("use_tor_proxy"):
        proxy = CONFIG.get("tor_proxy_url", "socks5://127.0.0.1:9050")
        opt.add_argument(f'--proxy-server={proxy}')
        
    return opt

def get_stealth_driver():
    """GOLIATH V9: Fikset 'cannot reuse' ved at kalde hjælpefunktion"""
    
    try:
        # Første forsøg: Vi beder om et friskt objekt
        driver = uc.Chrome(options=_get_fresh_options())
    except Exception:
        # Fallback: Vi beder om et HELT NYT objekt, da det første er 'brugt'
        driver = uc.Chrome(options=_get_fresh_options(), version_main=147)
    
    # CDP Anti-Bot Injektion (Bevaret 100%)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['da-DK', 'da']});
        '''
    })
    
    driver.implicitly_wait(7)
    driver.set_page_load_timeout(35)
    return driver

def zap_cookies(driver):
    """GOLIATH V9: Cookie-Zapper med udvidet dansk ordbog"""
    # Vi lader som om vi er en person der læser siden før vi klikker
    time.sleep(random.uniform(0.5, 1.2))
    
    terms = ['Accepter', 'OK', 'Godkend', 'Tillad', 'Accept all', 'Acceptér', 'Forstået', 'Tillad alle', 'Sæt i gang']
    try:
        xpath = "//button[" + " or ".join([f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{t.lower()}')" for t in terms]) + "]"
        btns = WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        if btns:
            # Scroll hen til knappen for at simulere visuel fokus
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btns[0])
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", btns[0])
            return True
    except Exception: pass
    
    # Shadow DOM Fallback (Vigtig for moderne Consent-managers)
    shadow_js = """
    let success = false;
    document.querySelectorAll('*').forEach(host => {
        if (host.shadowRoot) {
            host.shadowRoot.querySelectorAll('button').forEach(btn => {
                let txt = btn.innerText.toLowerCase();
                if (txt.includes('accepter') || txt.includes('tillad') || txt.includes('accept')) {
                    btn.click();
                    success = true;
                }
            });
        }
    });
    return success;
    """
    try:
        if driver.execute_script(shadow_js):
            return True
    except Exception: pass

    return False

def capture_evidence(driver, name):
    """GOLIATH V9: Full-Page Evidence Capture"""
    timestamp = datetime.now().strftime("%H%M%S")
    os.makedirs(session.get('loot_folder', './loot'), exist_ok=True)
    path = f"{session.get('loot_folder', './loot')}/SCREENSHOT_{name}_{timestamp}.png"
    
    try:
        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        driver.set_window_size(1920, total_height)
        time.sleep(0.8)
        driver.save_screenshot(path)
        print(f"{C.GREEN}    [📷] Bevismateriale sikret: {path}{C.RESET}")
    except Exception as e:
        print(f"{C.DIM}    [!] Screenshot fejlede: {e}{C.RESET}")

def human_typing(element, text):
    """Simulerer fejl og rettelser under skrivning (Meget stærkt mod Captcha)"""
    for char in text:
        # 5% chance for at skrive et forkert tegn og slette det igen
        if random.random() < 0.05:
            element.send_keys(random.choice('abcdefghijklmnopqrstuvwxyz'))
            time.sleep(random.uniform(0.1, 0.3))
            element.send_keys('\b') 
            
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def human_scroll(driver):
    """GOLIATH V9: Ujævn scrolling der efterligner menneskelig adfærd"""
    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_pos = 0
        while current_pos < total_height:
            step = random.randint(200, 500)
            current_pos += step
            driver.execute_script(f"window.scrollTo(0, {current_pos});")
            time.sleep(random.uniform(0.4, 1.1))
            
            # Chance for at scrolle lidt op igen (læse-adfærd)
            if random.random() < 0.15:
                driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 200)});")
                time.sleep(random.uniform(0.3, 0.6))
    except Exception: pass