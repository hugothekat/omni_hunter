# -*- coding: utf-8 -*-
"""
CORE BROWSER MODULE
Operativ Specifikation:
- Autonomous Stealth WebDriver Initialization
- Deep CDP Evasion (WebGL, Hardware, Navigator Spoofing)
- Algorithmic Human Emulation (Gaussian Delays)
- Zero-Noise Execution
"""

import os
import re
import time
import random
import logging
from datetime import datetime

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.utils import C, session
from core.network import CONFIG

# Slår unødvendig støj fra undetected_chromedriver fra
logging.getLogger('undetected_chromedriver').setLevel(logging.CRITICAL)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

def _generate_stealth_options():
    """Genererer et isoleret, støjfrit ChromeOptions objekt per instans."""
    opt = uc.ChromeOptions()
    opt.add_argument("--headless=new")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1920,1080")
    opt.add_argument("--disable-notifications")
    opt.add_argument("--disable-popup-blocking")
    opt.add_argument("--lang=da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7")
    
    # Silence Chrome output
    opt.add_argument("--log-level=3")
    opt.add_argument("--disable-crash-reporter")
    opt.add_argument("--disable-in-process-stack-traces")
    opt.add_argument("--disable-logging")
    
    # Evasion parameters
    opt.add_argument('--disable-blink-features=AutomationControlled')
    opt.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
    
    # Tor Proxy routing
    if isinstance(CONFIG, dict) and CONFIG.get("use_tor_proxy"):
        proxy = CONFIG.get("tor_proxy_url", "socks5://127.0.0.1:9050")
        opt.add_argument(f'--proxy-server={proxy}')
        
    return opt

def get_stealth_driver():
    """Initialiserer WebDriver med Deep CDP Spoofing og 3-trins fallback."""
    driver = None
    
    for attempt in range(1, 4):
        try:
            driver = uc.Chrome(options=_generate_stealth_options())
            break
        except Exception:
            if attempt == 3:
                raise RuntimeError("Kritisk Fejl: WebDriver kunne ikke initialiseres efter 3 forsøg.")
            time.sleep(2)
            
    # Deep CDP Evasion (Maskerer hardware og WebGL for at snyde Turnstile)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['da-DK', 'da', 'en-US', 'en']});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
            
            const getParameter = WebGLRenderingContext.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Open Source Technology Center';
                if (parameter === 37446) return 'Mesa DRI Intel(R) HD Graphics (Skylake)';
                return getParameter(parameter);
            };
        '''
    })
    
    driver.implicitly_wait(5)
    driver.set_page_load_timeout(30)
    return driver

def zap_cookies(driver):
    """Lydløs og aggressiv fjernelse af Cookie Consent-bannere."""
    time.sleep(random.gauss(0.8, 0.2))
    
    terms = ['Accepter', 'OK', 'Godkend', 'Tillad', 'Accept all', 'Acceptér', 'Forstået', 'Tillad alle']
    xpath = "//button[" + " or ".join([f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{t.lower()}')" for t in terms]) + "]"
    
    try:
        btns = WebDriverWait(driver, 1.5).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        if btns:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btns[0])
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", btns[0])
            return True
    except Exception:
        pass
    
    # Shadow DOM Traversal
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
        return bool(driver.execute_script(shadow_js))
    except Exception:
        return False

def capture_evidence(driver, name):
    """Sikrer fuldskærms-beviser til disk (KUN NÅR KALDT AF OPERATØREN)."""
    folder = session.get('loot_folder', './loot_evidence')
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    path = f"{folder}/EVIDENCE_{name}_{ts}.png"
    
    try:
        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        driver.set_window_size(1920, total_height)
        time.sleep(0.5)
        driver.save_screenshot(path)
    except Exception:
        pass

def human_typing(element, text):
    """Gaussian-fordelt tastatur-emulering med indbygget fejl-korrektion."""
    for char in text:
        if random.random() < 0.03:
            element.send_keys(random.choice('abcdefghijklmnopqrstuvwxyz'))
            time.sleep(random.gauss(0.15, 0.05))
            element.send_keys('\b') 
            
        element.send_keys(char)
        # Gaussian delay efterligner muskel-hukommelse bedre end uniform distribution
        time.sleep(max(0.05, random.gauss(0.1, 0.04)))

def human_scroll(driver):
    """Matematisk organisk page-scroll."""
    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_pos = 0
        
        while current_pos < total_height:
            step = int(random.gauss(300, 100))
            if step < 50: step = 50
            
            current_pos += step
            driver.execute_script(f"window.scrollTo(0, {current_pos});")
            time.sleep(max(0.2, random.gauss(0.6, 0.2)))
            
            # 10% chance for regression (læser noget igen)
            if random.random() < 0.10:
                back_step = int(random.gauss(150, 50))
                driver.execute_script(f"window.scrollBy(0, -{back_step});")
                time.sleep(max(0.3, random.gauss(0.5, 0.1)))
    except Exception:
        pass