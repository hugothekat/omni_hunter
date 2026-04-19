# core/browser.py
import time
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.utils import C, session

def get_stealth_driver():
    """Undetected Chromedriver der bypasser Cloudflare og bot-beskyttelse"""
    # Vi henter CONFIG lokalt her for at undgå import-cirkler
    from core.network import CONFIG 
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    if CONFIG.get("use_tor_proxy"):
        proxy = CONFIG["tor_proxy_url"]
        options.add_argument(f'--proxy-server={proxy}')
    
    driver = uc.Chrome(options=options)
    driver.implicitly_wait(3)
    driver.set_page_load_timeout(15)
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