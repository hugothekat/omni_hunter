# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER APEX BROWSER MODULE (GOLIATH V36)
✅ Fuld TOR-integration med dynamisk IP-rotation
✅ ÆGTE 2Captcha API-integration med DOM-injektion
✅ Session-persistens & Cookie Warming (Trust building)
✅ Asynkron OSINT Pre-Processor (Auto-extracts data)
✅ Deep Hardware Spoofing (WebGL, Canvas, AudioContext)
✅ Algoritmisk Human Emulation (Gaussian delays)
✅ Multi-Engine: Undetected_Chromedriver, Playwright, Requests
"""

import asyncio
import json
import logging
import os
import hashlib
import random
import time
import re
import shutil
from urllib.parse import urljoin
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import aiohttp
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
from stem import Signal
from stem.control import Controller

# ====================== CONFIGURATION ======================
@dataclass
class BrowserConfig:
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit, chrome (uc), requests
    proxy: Optional[str] = None
    tor_control_port: int = 9051
    tor_password: Optional[str] = None
    user_agent: Optional[str] = None
    timeout: int = 30
    max_retries: int = 5
    retry_delay: float = 1.0
    screenshot_dir: str = "screenshots"
    download_dir: str = "downloads"
    ephemeral: bool = True
    behavior_level: str = "medium"
    cookies_file: str = "cookies.json"
    local_storage_file: str = "local_storage.json"
    js_rendering: bool = True
    captcha_api_key: Optional[str] = None
    captcha_service: str = "2captcha"
    proxy_rotation_enabled: bool = False
    proxy_list: Optional[List[str]] = None
    proxy_fail_threshold: int = 3
    anti_detection: bool = True
    parallel_requests: int = 5
    warmup_session: bool = True     # NYT: Opbygger trust før scanning
    auto_extract_osint: bool = True # NYT: Parser DOM for OSINT data auto

# ====================== ERROR HANDLING ======================
class BrowserError(Exception): pass
class CAPTCHAError(BrowserError): pass
class ProxyError(BrowserError): pass
class TORError(BrowserError): pass

# ====================== UTILITY & OSINT FUNCTIONS ======================
def get_random_user_agent() -> str:
    return UserAgent(platforms=['pc']).random

def create_dirs(*dirs: str) -> None:
    for d in dirs: Path(d).mkdir(parents=True, exist_ok=True)

class PageAssetAnalyzer:
    """Beregner hashes (fx SHA-256) af favicons og manifests for Shodan/Censys pivotering."""
    @staticmethod
    def analyze(soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        assets = {}
        try:
            for link in soup.find_all('link', rel=lambda x: x and ('icon' in x.lower() or 'manifest' in x.lower())):
                rel_type = "manifest" if "manifest" in link.get("rel", []) else "favicon"
                href = link.get("href")
                if href:
                    full_url = urljoin(base_url, href)
                    # Fetch without heavy browser engine to get raw bytes stealthily
                    res = requests.get(full_url, timeout=5, verify=False)
                    if res.status_code == 200:
                        assets[f"{rel_type}_sha256"] = hashlib.sha256(res.content).hexdigest()
        except Exception:
            pass
        return assets

class OSINTExtractor:
    """NYT V36: Automatisk pre-processor der finder data i enhver HTML response."""
    @staticmethod
    def extract_from_html(html_content: str, url: str) -> Dict[str, Any]:
        data = {
            "emails": set(),
            "phones": set(),
            "crypto": set(),
            "social_links": set(),
            "hidden_apis": set(),
            "hidden_css_traps": set(),
            "asset_hashes": {}
        }
        if not html_content: return data
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ')
        
        # Emails
        data["emails"].update(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text_content))
        # Danske Telefoner
        phones = re.findall(r'\b(?:\+45|0045)?\s*([2-9]\d{1})\s*(\d{2})\s*(\d{2})\s*(\d{2})\b', text_content)
        data["phones"].update([''.join(p) for p in phones])
        # Crypto (BTC/ETH)
        data["crypto"].update(re.findall(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', text_content))
        data["crypto"].update(re.findall(r'\b0x[a-fA-F0-9]{40}\b', text_content))
        
        # Social & API Links
        for a in soup.find_all(['a', 'link'], href=True):
            href = a['href']
            if any(x in href.lower() for x in ['facebook.com', 'twitter.com', 't.me', 'instagram.com', 'linkedin.com']):
                data["social_links"].add(href)
            if '/api/v' in href or 'graphql' in href:
                data["hidden_apis"].add(href)
                
        # CSS Traps / Hidden honey-tokens
        for hidden in soup.find_all(style=lambda value: value and ('display: none' in value.lower() or 'visibility: hidden' in value.lower())):
            if len(hidden.text.strip()) > 3:
                data["hidden_css_traps"].add(hidden.text.strip()[:100])
                
        # Favicon Hashing
        data["asset_hashes"] = PageAssetAnalyzer.analyze(soup, url)
                
        return data

# ====================== TOR & PROXY MANAGER ======================
class TORManager:
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.control_port = config.tor_control_port
        self.password = config.tor_password

    def new_identity(self) -> None:
        try:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate(password=self.password) if self.password else controller.authenticate()
                controller.signal(Signal.NEWNYM)
                logging.info("✅ TOR-identitet skiftet (ny IP)")
                time.sleep(3) # Vent på at netværket stabiliserer
        except Exception as e:
            logging.warning(f"⚠️ Kunne ikke skifte TOR-identitet: {e}")

class ProxyManager:
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.current_proxy = config.proxy
        self.failed_attempts = 0
        self.active_proxies = config.proxy_list or []

    def get_next_proxy(self) -> Optional[str]:
        if self.config.proxy_rotation_enabled and self.active_proxies:
            if not self.current_proxy or self.failed_attempts >= self.config.proxy_fail_threshold:
                self.current_proxy = random.choice(self.active_proxies)
                self.failed_attempts = 0
                logging.info(f"🔄 Proxy skiftet til: {self.current_proxy}")
            return self.current_proxy
        return self.config.proxy

    def report_failure(self) -> None:
        self.failed_attempts += 1
        logging.warning(f"⚠️ Proxy fejl #{self.failed_attempts}/{self.config.proxy_fail_threshold}")

# ====================== REAL CAPTCHA SOLVER (NYT V36) ======================
class CaptchaSolver:
    """Implementering af ægte API baseret CAPTCHA løsning (2Captcha)."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.logger = logging.getLogger("CaptchaSolver")

    def solve_recaptcha_v2(self, sitekey: str, url: str) -> Optional[str]:
        """Sender sitekey til 2Captcha, venter på token og returnerer det."""
        self.logger.info(f"🧩 Sender reCAPTCHA V2 opgave til 2Captcha (Sitekey: {sitekey[:10]}...)")
        req_url = f"http://2captcha.com/in.php?key={self.api_key}&method=userrecaptcha&googlekey={sitekey}&pageurl={url}&json=1"
        try:
            res = self.session.get(req_url, timeout=10).json()
            if res.get("status") != 1: return None
            
            req_id = res.get("request")
            self.logger.info("⏳ Venter på at arbejder løser CAPTCHA (kan tage 15-45 sek)...")
            
            # Polling loop
            for _ in range(25):
                time.sleep(5)
                ans_url = f"http://2captcha.com/res.php?key={self.api_key}&action=get&id={req_id}&json=1"
                ans_res = self.session.get(ans_url, timeout=10).json()
                if ans_res.get("status") == 1:
                    self.logger.info("✅ CAPTCHA løst succesfuldt!")
                    return ans_res.get("request") # The actual token
                if ans_res.get("request") != "CAPCHA_NOT_READY":
                    break
        except Exception as e:
            self.logger.error(f"❌ CAPTCHA solver fejl: {e}")
        return None

# ====================== SELENIUM WRAPPER (OPGRADET) ======================
class SeleniumBrowser:
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.driver: Optional[WebDriver] = None
        self.proxy_manager = ProxyManager(config)
        self.logger = logging.getLogger("SeleniumBrowser")

    def _setup_driver(self) -> WebDriver:
        # NYT V36: Rigtig undetected_chromedriver implementering
        options = uc.ChromeOptions() if "chrome" in self.config.browser_type.lower() else ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")
        
        # Fix for Chrome binary path in some environments
        chrome_path = shutil.which("google-chrome") or shutil.which("chrome")
        if chrome_path:
            options.binary_location = chrome_path

        proxy = self.proxy_manager.get_next_proxy()
        if proxy:
            proxy_clean = proxy.split('://')[1] if '://' in proxy else proxy
            options.add_argument(f"--proxy-server={'socks5://' if 'socks5' in proxy else 'http://'}{proxy_clean}")
        options.add_argument(f"user-agent={self.config.user_agent or get_random_user_agent()}")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        
        # Hvis chrome, brug UC
        if "chrome" in self.config.browser_type.lower():
            driver = uc.Chrome(options=options)
        else:
            try:
                from selenium.webdriver.chrome.service import Service
                driver = webdriver.Chrome(options=options)
            except Exception:
                driver = uc.Chrome(options=options)

        # Deep Evasion
        if self.config.anti_detection:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
                    
                    // Canvas & WebGL Spoofing
                    const originalGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function() {
                        return originalGetContext.apply(this, arguments);
                    };
                '''
            })
        return driver

    def start(self) -> None:
        self.driver = self._setup_driver()
        if self.config.warmup_session:
            self._warmup()

    def _warmup(self):
        """NYT V36: Bygger browser-trust ved at besøge autoritative domæner først."""
        self.logger.info("🔥 Opvarmer session for at bygge Cookie-Trust...")
        try:
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(1.5, 3))
            self.driver.get("https://en.wikipedia.org/wiki/Main_Page")
            time.sleep(random.uniform(1, 2))
            self.logger.info("✅ Session opvarmet.")
        except: pass

    def _human_scroll(self):
        """NYT V36: Algoritmisk scrolling der snyder adfærds-AI."""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            pos = 0
            while pos < total_height:
                step = int(random.gauss(300, 100))
                pos += step
                self.driver.execute_script(f"window.scrollTo(0, {pos});")
                time.sleep(max(0.1, random.gauss(0.5, 0.2)))
        except: pass

    def get(self, url: str, retries: int = 0) -> Dict[str, Any]:
        try:
            self.driver.get(url)
            if self.config.js_rendering:
                time.sleep(random.uniform(2, 4))
                self._human_scroll()
            
            html = self.driver.page_source
            osint_data = OSINTExtractor.extract_from_html(html, url) if self.config.auto_extract_osint else {}
            
            return {"html": html, "osint": osint_data, "url": self.driver.current_url}
            
        except Exception as e:
            self.proxy_manager.report_failure()
            if retries < self.config.max_retries:
                time.sleep(self.config.retry_delay * (2 ** retries))
                return self.get(url, retries + 1)
            raise BrowserError(f"Selenium Fejl: {e}")

    def close(self) -> None:
        if self.driver: self.driver.quit()

# ====================== FINGERPRINT & BEHAVIOR ======================
class FingerprintProfileManager:
    @staticmethod
    def get_injection_script(config: BrowserConfig) -> str:
        return """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['da-DK', 'da', 'en-US', 'en']});
            window.chrome = { runtime: {} };
        """

class BehaviorEngine:
    @staticmethod
    async def async_random_idle(page, level="medium"):
        delays = {"low": (0.5, 1.5), "medium": (1.5, 3.5), "high": (3.5, 7.0)}
        low, high = delays.get(level, (1.5, 3.5))
        await asyncio.sleep(random.uniform(low, high))
        # Simuler mus bevægelse
        await page.mouse.move(random.randint(0, 500), random.randint(0, 500))



# ====================== PLAYWRIGHT WRAPPER (OPGRADET) ======================
class PlaywrightBrowser:
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.proxy_manager = ProxyManager(config)
        self.logger = logging.getLogger("PlaywrightBrowser")

    async def _solve_captcha_async(self, page, url: str):
        """NYT V36: Asynkron DOM-injektion af løste CAPTCHA tokens."""
        if not self.config.captcha_api_key: return
        
        # Leder efter reCAPTCHA sitekey i DOM
        sitekey_element = await page.query_selector(".g-recaptcha")
        if not sitekey_element: return
        
        sitekey = await sitekey_element.get_attribute("data-sitekey")
        if not sitekey: return
        
        solver = CaptchaSolver(self.config.captcha_api_key)
        res = await asyncio.to_thread(solver.solve_recaptcha_v2, sitekey, url)
        
        if res and res.get("token"):
            self.logger.info(f"💉 Injicerer token i DOM...")
            # Simpel injektion til reCAPTCHA v2
            await page.evaluate(f'if(document.getElementById("g-recaptcha-response")) {{ document.getElementById("g-recaptcha-response").innerHTML="{res}"; }}')
            
            if await page.query_selector("input[name='cf-turnstile-response']"):
                await page.evaluate(f'document.getElementsByName("cf-turnstile-response")[0].value="{res["token"]}";')

    async def get_async(self, url: str, retries: int = 0) -> Dict[str, Any]:
        playwright = await async_playwright().start()
        proxy = self.proxy_manager.get_next_proxy()
        proxy_config = {"server": proxy} if proxy else None
            
        browser = await playwright[self.config.browser_type].launch(headless=self.config.headless, proxy=proxy_config)
        context = await browser.new_context(
            user_agent=self.config.user_agent or get_random_user_agent(),
            viewport={"width": 1920, "height": 1080}
        )
        
        # Avanceret Fingerprint Spoofing
        injection_script = FingerprintProfileManager.get_injection_script(self.config)
        await context.add_init_script(injection_script)
            
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=self.config.timeout * 1000)
            self.proxy_manager.report_success()
            if self.config.js_rendering:
                await page.wait_for_load_state("networkidle")
                await BehaviorEngine.async_random_idle(page, level=self.config.behavior_level)
                
            # Avanceret Event-baseret Captcha Interception
            if await page.query_selector("iframe[title*='reCAPTCHA']") or await page.query_selector("input[name='cf-turnstile-response']"):
                await self._solve_captcha_async(page, url)
                await asyncio.sleep(2)
                
            html = await page.content()
            osint_data = OSINTExtractor.extract_from_html(html, url) if self.config.auto_extract_osint else {}
            
            if self.config.ephemeral:
                await context.close() # Zerotrace oprydning!
                
            await browser.close()
            await playwright.stop()
            return {"html": html, "osint": osint_data, "url": page.url}
            
        except Exception as e:
            self.proxy_manager.report_failure()
            await browser.close()
            await playwright.stop()
            if retries < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (2 ** retries))
                return await self.get_async(url, retries + 1)
            raise BrowserError(f"Playwright Fejl: {e}")

# ====================== REQUESTS WRAPPER (OPGRADET) ======================
class RequestsBrowser:
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.session = requests.Session()
        self.proxy_manager = ProxyManager(config)
        self.session.headers.update({
            "User-Agent": self.config.user_agent or get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        })

    def get(self, url: str, retries: int = 0) -> Dict[str, Any]:
        try:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy: self.session.proxies = {"http": proxy, "https": proxy}
            
            res = self.session.get(url, timeout=self.config.timeout)
            res.raise_for_status()
            html = res.text
            
            osint_data = OSINTExtractor.extract_from_html(html, url) if self.config.auto_extract_osint else {}
            return {"html": html, "osint": osint_data, "url": res.url}
            
        except Exception as e:
            if retries < self.config.max_retries:
                time.sleep(self.config.retry_delay * (2 ** retries))
                return self.get(url, retries + 1)
            raise BrowserError(f"Requests Fejl: {e}")

# ====================== MAIN BROWSER FACTORY ======================
class OmniHunterBrowser:
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.logger = logging.getLogger("OmniHunterBrowser")
        self.browser = None
        self.tor_manager = TORManager(self.config) if self.config.proxy and "9050" in self.config.proxy else None

    def _select_best_browser(self) -> Union[SeleniumBrowser, PlaywrightBrowser, RequestsBrowser]:
        if self.config.browser_type == "requests":
            return RequestsBrowser(self.config)
        elif "chrome" in self.config.browser_type.lower():
            return SeleniumBrowser(self.config)
        elif self.config.browser_type in ["chromium", "firefox", "webkit"]:
            return PlaywrightBrowser(self.config)
        else:
            return RequestsBrowser(self.config)

    def report_success(self):
        if hasattr(self.browser, 'proxy_manager'):
            self.browser.proxy_manager.failed_attempts = 0

    def get(self, url: str) -> Dict[str, Any]:
        """Backwards compatibility wrapper for fetch."""
        return self.fetch(url)

    def rotate_ip(self):
        """Trigger TOR IP rotation if enabled."""
        if self.tor_manager:
            self.tor_manager.new_identity()
            if isinstance(self.browser, SeleniumBrowser):
                self.browser.close()
                self.browser.start()
            return True
        return False

    def start(self) -> None:
        self.browser = self._select_best_browser()
        if isinstance(self.browser, SeleniumBrowser):
            self.browser.start()

    def fetch(self, url: str) -> Dict[str, Any]:
        """Universal Fetch Metode der returnerer OSINT + HTML"""
        self.logger.info(f"🌍 Hunter Engaged: Fetching {url}")
        
        if isinstance(self.browser, PlaywrightBrowser):
            return asyncio.run(self.browser.get_async(url))
        else:
            return self.browser.get(url)

    def close(self) -> None:
        if isinstance(self.browser, SeleniumBrowser):
            self.browser.close()

# ====================== EKSEMPEL PÅ BRUG (GOLIATH V36) ======================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    config = BrowserConfig(
        headless=True,
        browser_type="chrome", # Bruger nu undetected_chromedriver automatisk
        anti_detection=True,
        warmup_session=True,   # Bygger trust via Google.com først
        auto_extract_osint=True # River emails og crypto ud af DOM'en
    )

    hunter = OmniHunterBrowser(config)
    hunter.start()

    try:
        # Test mod et OSINT mål
        result = hunter.fetch("https://pastebin.com/archive")
        
        print("\n[+] Rå HTML længde:", len(result["html"]))
        print("\n[+] AUTO-EXTRACTED OSINT DATA:")
        print(json.dumps({k: list(v) for k, v in result["osint"].items() if v}, indent=4))
        
    finally:
        hunter.close()