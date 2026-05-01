# -*- coding: utf-8 -*-
import re
import asyncio
import aiohttp
import socket
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, Optional, List, Set
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake, ThreatIntelExtractor
from core.network import AsyncTurnstileSolver, omni_dork_search, http
from core.config_vault import vault
try:
    from core.nexus import nexus, EntityType
except ImportError:
    nexus = None

class AbyssDarkwebSpider(BaseModule):
    """
    GOLIATH V42: THE ABYSS DARKWEB SPIDER (FUSION AF MODUL 05, 22 OG 37)
    Asynkron Level-2 Spider der crawler dybt i .onion sider, omgår Turnstile/Captchas 
    via DOM-injektion, høster Threat Intel (XMPP, PGP, Krypto) og opsnapper data over TOR.
    """
    def __init__(self):
        super().__init__()
        self.name = "ABYSS DARKWEB SPIDER & INTERCEPTOR"
        self.description = "Asynkron Level-2 Tor-Scraping, Turnstile Bypass & Identity Resolution."
        self.category = ModuleCategory.NETWORK
        
        self.api_key = vault.get("api_keys", "2captcha_api_key") if vault else None
        self.visited_urls = set()
        
        self.data = {
            "Target": "",
            "Scraped_URLs": [],
            "PGP_Public_Keys": [],
            "Jabber_XMPP_Konti": set(),
            "Kryptovaluta": set(),
            "Hashes_Fundet": set(),
            "Emails_Identificeret": set(),
            "Lækkede_Kredentialer": set(),
            "Raw_Dumps_Scraped": 0,
            "Turnstile_Bypassed": False
        }

    def check_requirements(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", 9050), timeout=2):
                return True
        except OSError:
            print(f"{C.RED}[!] Fejl: Modulet kræver at lokal Tor-tjeneste kører (port 9050).{C.RESET}")
            return False

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[05] ABYSS DARKWEB SPIDER V42\n{'='*60}{C.RESET}")
        self.data["Target"] = target
        
        if not target.endswith(".onion") and ".onion/" not in target:
            print(f"{C.YELLOW}[*] Target er ikke et direkte .onion link. Starter Clearnet Ahmia-Søgning...{C.RESET}")
            if driver:
                hits = omni_dork_search(driver, f'"{target}" site:onion.ly OR site:onion.ws', max_links=3)
                for hit in hits:
                    url = hit.get('url')
                    if url:
                        print(f"{C.GREEN}[+] Fandt Clearnet-Tor Gateway link: {url}{C.RESET}")
                        self.data["Scraped_URLs"].append(url)
            datalake.ingest(self.name, target, self.data)
            return self.data

        url = target if target.startswith("http") else f"http://{target}"
        base_domain = urlparse(url).netloc
        
        print(f"{C.YELLOW}[*] Engagerer Asynkron Playwright TOR-Spider mod: {base_domain} (Max Dybde: 2){C.RESET}")
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(self._init_spider(url, base_domain))
        except Exception as e:
            print(f"{C.RED}[!] Async Spider Fejl: {e}{C.RESET}")

        # Formater sets til lister
        self.data = {k: list(v) if isinstance(v, set) else v for k, v in self.data.items()}
        datalake.ingest(self.name, target, self.data)
        self._print_summary()
        return self.data

    async def _init_spider(self, start_url: str, base_domain: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, proxy={"server": "socks5://127.0.0.1:9050"})
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0")
            await self._spider_node(context, start_url, 0, base_domain)
            await browser.close()

    async def _spider_node(self, context: Any, url: str, depth: int, base_domain: str):
        if depth > 2 or url in self.visited_urls: return
        self.visited_urls.add(url)
        self.data["Scraped_URLs"].append(url)
        
        prefix = "  " * depth
        print(f"{C.CYAN}{prefix}[*] Dykker (Niveau {depth}): {url[:70]}...{C.RESET}")
        
        # Hvis URL'en peger direkte på et dump/log, scraper vi det lynhurtigt med network.py via Tor
        if any(url.lower().endswith(ext) for ext in ['.txt', '.csv', '.sql', '.log', '.dump', '.db']):
            print(f"{C.YELLOW}{prefix}  [*] Raw Dump detekteret. Udfører stealth-ekstraktion via core.network...{C.RESET}")
            try:
                # Bruger Tor-proxies direkte med stealth-sessionen fra network.py
                proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
                res = await asyncio.to_thread(http.get, url, proxies=proxies, timeout=20)
                if res.status_code == 200:
                    # Sikker UTF-8 håndtering til danske lækager (Expansion Mode)
                    text_content = res.content.decode('utf-8', errors='replace')
                    self._extract_credentials(text_content, prefix)
                    self.data["Raw_Dumps_Scraped"] += 1
                return
            except Exception as e:
                print(f"{C.RED}{prefix}  [!] Raw Dump fejl: {e}{C.RESET}")
                return

        page = await context.new_page()
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Cloudflare / Turnstile DOM Injektion
            turnstile_el = await page.query_selector("div.cf-turnstile, input[name='cf-turnstile-response']")
            if turnstile_el and self.api_key:
                sitekey = await turnstile_el.get_attribute("data-sitekey")
                if sitekey:
                    print(f"{C.YELLOW}{prefix}  [*] WAF Detekteret. Smadrer beskyttelsen med 2Captcha...{C.RESET}")
                    solver = AsyncTurnstileSolver(self.api_key)
                    token = await solver.solve(url, sitekey)
                    if token:
                        await page.evaluate(f'document.getElementsByName("cf-turnstile-response")[0].value="{token}";')
                        submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
                        if submit_btn: await submit_btn.click()
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        self.data["Turnstile_Bypassed"] = True
                        print(f"{C.GREEN}{prefix}  ✓ WAF Neutraliseret!{C.RESET}")

            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser", from_encoding="utf-8")
            text_content = soup.get_text(separator=' ')

            # Threat Intel Extraction
            pgp_blocks = re.findall(r'(-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----)', text_content, re.DOTALL)
            if pgp_blocks: self.data["PGP_Public_Keys"].extend([b.strip() for b in pgp_blocks])
            self.data["Jabber_XMPP_Konti"].update(re.findall(r'[a-zA-Z0-9_.+-]+@(?:jabber\.|xmpp\.|jabb\.|exploit\.im)[a-zA-Z0-9-.]+', text_content))
            iocs = ThreatIntelExtractor.extract_all(text_content)
            self.data["Kryptovaluta"].update(iocs.get("crypto_btc", []) + iocs.get("crypto_xmr", []) + iocs.get("crypto_eth", []))
            self.data["Emails_Identificeret"].update(iocs.get("email", []))
            self.data["Hashes_Fundet"].update(iocs.get("md5", []) + iocs.get("sha256", []))
            
            # Ekstraherer de-hashed passwords / klartekst-kredentialer fra DOM
            self._extract_credentials(text_content, prefix)

            # Spidering logik
            if depth < 2:
                links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
                valid_links = [l for l in set(links) if base_domain in urlparse(l).netloc and l not in self.visited_urls]
                
                tasks = [self._spider_node(context, link, depth+1, base_domain) for link in valid_links[:5]] # Max 5 forgreninger per side for OPSEC
                if tasks: await asyncio.gather(*tasks)
                
        except Exception as e:
            pass # Fejl under page navigation på lukkede lister ignoreres lydløst
        finally:
            await page.close()

    def _extract_credentials(self, text: str, prefix: str):
        """GOLIATH V42: Ekstraherer klartekst email:password kombinationer med OPSEC-filtrering."""
        creds = re.findall(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+):([^\s<"\'/]{6,40})', text)
        for c in creds:
            pwd = c[1]
            # Filtrerer kryptografiske hashes, så vi kun får de-hashed (klartekst)
            if len(pwd) not in [32, 40, 64] and not pwd.startswith('$2'):
                cred_str = f"{c[0]}:{pwd}"
                if cred_str not in self.data["Lækkede_Kredentialer"]:
                    self.data["Lækkede_Kredentialer"].add(cred_str)
                    print(f"{C.RED}{prefix}  🔥 Klartekst/De-hashed Credential fundet: {c[0]}:{pwd[:3]}***{C.RESET}")
                    
                    # GOLIATH V42: Nexus Graph Integration for Dashboard Visualisering
                    if nexus:
                        target = self.data.get("Target", "Ukendt Mål")
                        email_addr = c[0]
                        nexus.ingest(EntityType.EMAIL, email_addr, source="AbyssSpider", confidence=0.9)
                        nexus.ingest(EntityType.CREDENTIAL, pwd, source="AbyssSpider", confidence=0.9)
                        nexus.link(target, email_addr, "Eksponeret_Email")
                        nexus.link(email_addr, pwd, "Lækket_Password")

    def _print_summary(self):
        print(f"\n{C.CYAN}--- ABYSS SPIDER SUMMARY ---{C.RESET}")
        print(f"[+] Sider Scannet over TOR: {C.WHITE}{len(self.data['Scraped_URLs'])}{C.RESET}")
        if self.data["Turnstile_Bypassed"]: print(f"{C.GREEN}[+] Turnstile WAF Bypassed: Ja{C.RESET}")
        print(f"[+] PGP Nøgler Fundet: {C.WHITE}{len(self.data['PGP_Public_Keys'])}{C.RESET}")
        print(f"[+] XMPP/Jabber Konti: {C.WHITE}{len(self.data['Jabber_XMPP_Konti'])}{C.RESET}")
        print(f"[+] Krypto-adresser: {C.WHITE}{len(self.data['Kryptovaluta'])}{C.RESET}")
        if self.data["Lækkede_Kredentialer"]: print(f"[+] De-hashed Passwords: {C.RED}{len(self.data['Lækkede_Kredentialer'])}{C.RESET}")
