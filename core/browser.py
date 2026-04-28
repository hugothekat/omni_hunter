# core/browser.py
import time
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import json
import re
from core.utils import C, session

def get_stealth_driver():
    """Undetected Chromedriver i HEADLESS mode (100% usynlig)"""
    from core.network import CONFIG 
    import undetected_chromedriver as uc
    
    options = uc.ChromeOptions()
    
    # 🚨 AKTIVERET: Gør browseren totalt usynlig
    options.add_argument("--headless=new") 
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Stealth indstillinger for at undgå detektering i headless mode
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    if CONFIG.get("use_tor_proxy"):
        proxy = CONFIG["tor_proxy_url"]
        options.add_argument(f'--proxy-server={proxy}')
    
    # Find linjen der starter uc.Chrome og tilføj version_main=147
    driver = uc.Chrome(options=options, version_main=147)
    
    
    driver.implicitly_wait(5)
    driver.set_page_load_timeout(30)
    return driver

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
    except Exception: pass
    
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
    except Exception: pass
    return False

def capture_evidence(driver, name):
    """Gemmer et screenshot af den nuværende side som bevismateriale."""
    timestamp = datetime.now().strftime("%H%M%S")
    path = f"{session['loot_folder']}/SCREENSHOT_{name}_{timestamp}.png"
    driver.save_screenshot(path)
    print(f"{C.YELLOW}    [📷] Bevis sikret: {path}{C.RESET}")

def safe_driver_action(driver, action_func, timeout=10, action_name=""):
    try:
        return action_func(driver)
    except (TimeoutException, NoSuchElementException, Exception):
        return None

def human_typing(element, text):
    """Simulerer menneskelig skrivehastighed med mikropauser"""
    for char in text:
        element.send_keys(char)
        # Tilføj en lille tilfældig pause mellem 0.05 og 0.2 sekunder
        time.sleep(random.uniform(0.05, 0.2))

def human_scroll(driver):
    """Simulerer at en rigtig person læser siden ved at scrolle ujævnt"""
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