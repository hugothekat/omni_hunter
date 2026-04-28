# -*- coding: utf-8 -*-
import time
import os
import json
import re
import random # NY V8 FIX: Nødvendig for human_typing og human_scroll
from datetime import datetime

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.utils import C, session

# NY V8 TILFØJELSE: Pulje af moderne, valide User-Agents til at undgå fingerprinting
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

def get_stealth_driver():
    """GOLIATH V8: Undetected Chromedriver i HEADLESS mode med CDP Anti-Bot Masking"""
    from core.network import CONFIG 
    
    options = uc.ChromeOptions()
    
    # 🚨 AKTIVERET: Gør browseren totalt usynlig
    options.add_argument("--headless=new") 
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Stealth indstillinger for at undgå detektering i headless mode
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'--user-agent={random.choice(UAS)}') # NY V8: Roterende UA
    
    if CONFIG.get("use_tor_proxy"):
        proxy = CONFIG.get("tor_proxy_url", "socks5://127.0.0.1:9050")
        options.add_argument(f'--proxy-server={proxy}')
    
    # V8 NOTE: Hvis version_main=147 crasher i fremtiden (fordi Chrome opdaterer sig selv på din PC), 
    # kan du prøve at fjerne ', version_main=147' parameteren, så UC selv finder versionen.
    try:
        driver = uc.Chrome(options=options, version_main=147)
    except Exception as e:
        print(f"{C.YELLOW}[!] Fejl med fastlåst Chrome version. Forsøger auto-detektion...{C.RESET}")
        driver = uc.Chrome(options=options)
    
    # --- NY V8 TILFØJELSE: CDP (Chrome DevTools Protocol) Anti-Bot Injektion ---
    # Fjerner navigator.webdriver flaget, før nogen hjemmeside når at læse det
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['da-DK', 'da', 'en-US', 'en']});
        '''
    })
    
    driver.implicitly_wait(5)
    driver.set_page_load_timeout(30)
    return driver

def zap_cookies(driver):
    """GOLIATH V8: Advanced Cookie Zapper (XPath, CSS & Shadow DOM Piercing)"""
    # 1. Standard Selenium XPath clicker
    terms = ['Accepter', 'OK', 'Godkend', 'Tillad', 'Accept all', 'Acceptér', 'Forstået', 'Tillad alle']
    try:
        xpath = "//button[" + " or ".join([f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{t.lower()}')" for t in terms]) + "]"
        btns = WebDriverWait(driver, 1.5).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        if btns:
            driver.execute_script("arguments[0].click();", btns[0]) # Mere pålidelig end .click() hvis elementet er dækket
            time.sleep(0.5)
            return True
    except Exception: pass
    
    # 2. CSS Selectors fallback
    try:
        selectors = ["button.cookie-accept", "button[class*='cookie']", "button[class*='consent']", "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]
        for selector in selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                return True
            except Exception:
                continue
    except Exception: pass

    # 3. NY V8 TILFØJELSE: Shadow DOM Piercing via JavaScript (Dræber Usercentrics m.fl.)
    shadow_js = """
    try {
        let hosts = document.querySelectorAll('*');
        for (let host of hosts) {
            if (host.shadowRoot) {
                let btns = host.shadowRoot.querySelectorAll('button');
                for (let btn of btns) {
                    let txt = btn.innerText.toLowerCase();
                    if (txt.includes('accept') || txt.includes('tillad') || txt.includes('godkend')) {
                        btn.click();
                        return true;
                    }
                }
            }
        }
    } catch(e) {}
    return false;
    """
    try:
        if driver.execute_script(shadow_js):
            time.sleep(0.5)
            return True
    except Exception: pass

    return False

def capture_evidence(driver, name):
    """GOLIATH V8: Sikrer bevismateriale lokalt."""
    timestamp = datetime.now().strftime("%H%M%S")
    os.makedirs(session.get('loot_folder', './loot'), exist_ok=True)
    path = f"{session.get('loot_folder', './loot')}/SCREENSHOT_{name}_{timestamp}.png"
    
    try:
        # NY V8 TILFØJELSE: Forsøger at fange fuld skærmhøjde for at få alt med
        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        driver.set_window_size(1920, total_height)
        time.sleep(0.5)
        
        driver.save_screenshot(path)
        print(f"{C.GREEN}    [📷] Bevismateriale sikret lokalt: {path}{C.RESET}")
    except Exception as e:
        print(f"{C.DIM}    [!] Fejl ved bevissikring: {e}{C.RESET}")

def safe_driver_action(driver, action_func, timeout=10, action_name=""):
    """Sikker wrapper til ustabile DOM elementer"""
    try:
        return action_func(driver)
    except (TimeoutException, NoSuchElementException, Exception) as e:
        # Skjuler unødvendigt støj, returnerer None så modulet kan håndtere fejlen elegant
        return None

def human_typing(element, text):
    """Simulerer menneskelig skrivehastighed med mikropauser"""
    for char in text:
        element.send_keys(char)
        # Tilføj en lille tilfældig pause mellem 0.05 og 0.2 sekunder
        time.sleep(random.uniform(0.05, 0.2))

def human_scroll(driver):
    """Simulerer at en rigtig person læser siden ved at scrolle ujævnt"""
    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        
        while current_position < total_height:
            # Scroll et tilfældigt antal pixels ned
            scroll_step = random.randint(150, 400)
            current_position += scroll_step
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            # Vent som om vi kigger på indholdet
            time.sleep(random.uniform(0.5, 1.5))
            
            # 10% chance for at vi "fortryder" og scroller lidt op igen
            if random.random() < 0.10:
                driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
                time.sleep(random.uniform(0.3, 0.8))
                
            # Break hvis vi utilsigtet rammer et uendeligt scroll loop (fx på Twitter/SoMe sider)
            if current_position > 15000: 
                break
    except Exception:
        pass # Hvis DOM'en ændrer sig imens vi scroller, fejler vi bare stille