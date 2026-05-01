# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - MODUL 22: SITERIP & REPOSITORY CLONING
📌 Formål: Sikker og stealthy kloning af Git repositories og websites med indbygget OPSEC og secret-scanning.
"""
import os
import subprocess
import shutil
import re
from datetime import datetime
import concurrent.futures
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import Dict, Any

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake, sanitize_filename
from core.logger import logger
from core.config_vault import vault
from core.browser import OmniHunterBrowser, BrowserConfig

class SiteripModule(BaseModule):
    """
    Advanced Siterip & Forensics Engine (GOLIATH V8).
    Tillader kloning af Git repos og scraping af webinfrastruktur med proxy-integration og memory-scanning.
    """
    
    def __init__(self, target_url: str = ""):
        super().__init__()
        self.name = "SITERIP & REPO FORENSICS"
        self.category = ModuleCategory.FORENSICS
        self.target_url = target_url.strip()
        self.loot_dir = session.get("loot_folder", "./loot")

    def run(self, driver: Any = None, target: str = "") -> Dict[str, Any]:
        url = self.target_url or target
        if not url:
            logger.error("Intet mål (URL) angivet til Siterip.")
            return {}

        # Auto-Heal: Sikrer at URL'en har et skema, så urlparse fungerer korrekt.
        if not url.startswith(("http://", "https://")) and not url.endswith(".git"):
            url = f"https://{url}"

        print(f"\n{C.CYAN}{'='*60}\n[22] GOLIATH SITERIP (Git & Web Clone V8)\n{'='*60}{C.RESET}")
        print(f"[*] Initialiserer Siterip Profiling for: {url}")

        # Opretter specifik loot undermappe for dette rip
        domain_name = url.split("//")[-1].split("/")[0].replace(".git", "")
        repo_name = url.split("/")[-1].replace(".git", "")
        safe_name = f"{domain_name}_{repo_name}_{datetime.now().strftime('%Y%md_%H%M')}"
        target_dir = os.path.join(self.loot_dir, "22_SITERIP", safe_name)
        os.makedirs(target_dir, exist_ok=True)

        logger.info(f"[*] Klargør OPSEC-miljø til rip: {target_dir}")

        if url.endswith(".git") or "github.com" in url or "gitlab.com" in url:
            self._clone_git_repo(url, target_dir)
            self._extract_git_secrets(target_dir)
        else:
            # GOLIATH V43: Advanced Python Ripper til dynamiske/WAF sider som scor.dk
            self._advanced_python_siterip(url, target_dir)

        self.data["Target"] = url
        self.data["Loot_Directory"] = target_dir
        self.data["Timestamp"] = datetime.now().isoformat()
        
        self.save_to_loot(f"22_SITERIP_{safe_name}.json")
        
        # Integration med datalake til Cross-Pollination
        datalake.ingest(self.name, url, self.data)
        
        return self.data

    def _clone_git_repo(self, url: str, target_dir: str):
        """Kloner et Git repo via OS-kald med OPSEC proxy-støtte."""
        print(f"{C.YELLOW}[*] Udfører OPSEC Git Kloning af {url}...{C.RESET}")
        
        # Henter proxy konfiguration fra Vault (hvis sat)
        proxy = vault.get("network", "proxy")
        
        env = os.environ.copy()
        if proxy:
            logger.info(f"[*] Anvender Vault Proxy ({proxy}) til Git for anonymitet.")
            env["http_proxy"] = proxy
            env["https_proxy"] = proxy

        try:
            # Kloner hele historikken for evt. at finde slettede secrets (Expansion Mode)
            result = subprocess.run(
                ["git", "clone", url, target_dir],
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8' # Garanter 100% korrekt UTF-8 håndtering
            )
            if result.returncode == 0:
                print(f"{C.GREEN}[+] Kloning fuldført! Repository gemt i: {target_dir}{C.RESET}")
                logger.info(f"Git clone succes for {url}")
            else:
                print(f"{C.RED}[!] Fejl ved kloning: {result.stderr}{C.RESET}")
                logger.error(f"Git clone fejl: {result.stderr}")
        except Exception as e:
            logger.error(f"Exception under git clone: {e}")
            print(f"{C.RED}[!] Kritisk fejl under kloning. Er 'git' installeret?{C.RESET}")

    def _extract_git_secrets(self, repo_dir: str):
        """Scanner git log for slettede secrets, passwords og API nøgler."""
        print(f"{C.YELLOW}[*] Støvsuger git-historik for lækager, danske metadata (ÆØÅ) og slettede filer...{C.RESET}")
        try:
            # Henter historik for alle commits
            log_res = subprocess.run(
                ["git", "-C", repo_dir, "log", "-p"],
                capture_output=True,
                text=True,
                errors="replace", # Håndterer korrupte tegn, bevarer UTF-8
                encoding='utf-8'
            )
            
            secrets_found = set()
            # Avanceret regex til at fange credentials
            secret_pattern = re.compile(r'(?i)(api[_-]?key|password|secret|token|auth)[\s=:]+[\'"]?([A-Za-z0-9\-_]{8,})[\'"]?')
            
            for line in log_res.stdout.splitlines():
                # Tjekker primært diff-linjer for tilføjelser/sletninger
                if line.startswith("+") or line.startswith("-"):
                    matches = secret_pattern.findall(line)
                    for match in matches:
                        secret = f"{match[0]}: {match[1]}"
                        secrets_found.add(secret)
                            
            if secrets_found:
                print(f"{C.RED}    🔥 Lækkede Secrets Fundet i Historikken ({len(secrets_found)} fund)!{C.RESET}")
                for i, s in enumerate(list(secrets_found)[:5]):
                    print(f"{C.RED}       - {s[:15]}...[REDACTED_OPSEC]{C.RESET}")
                if len(secrets_found) > 5:
                    print(f"{C.RED}       - ... og {len(secrets_found) - 5} flere. Tjek loot for detaljer.{C.RESET}")
                
                self.data["Git_Secrets"] = list(secrets_found)
                logger.info(f"Fandt {len(secrets_found)} potentielle secrets i git log.")
            else:
                print(f"{C.GREEN}    [✓] Ingen umiddelbare secrets fundet i loggen.{C.RESET}")
                
        except Exception as e:
            logger.error(f"Fejl ved secret scanning: {e}")

    def _wget_siterip(self, url: str, target_dir: str):
        """Alternativ WGET SiteRip for webservere der ikke er git repos."""
        print(f"{C.YELLOW}[*] Udfører aggressiv WGET SiteRip for webserver...{C.RESET}")
        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            cmd = [
                "wget", "--mirror", "--convert-links", "--adjust-extension", "--page-requisites",
                "--no-parent", "-e", "robots=off", "--user-agent", user_agent,
                "--directory-prefix", target_dir, url
            ]
            
            proxy = vault.get("network", "proxy")
            env = os.environ.copy()
            if proxy:
                env["http_proxy"] = proxy
                env["https_proxy"] = proxy
                cmd.append(f"--execute=http_proxy={proxy}")

            subprocess.run(cmd, env=env, capture_output=True, timeout=600)
            print(f"{C.GREEN}[+] SiteRip fuldført! Filer ligger i: {target_dir}{C.RESET}")
            logger.info("Wget SiteRip succes.")
        except Exception as e:
            logger.error(f"SiteRip fejl: {e}")
            print(f"{C.RED}[!] Kritisk fejl under SiteRip. Er 'wget' installeret?{C.RESET}")

    def _advanced_python_siterip(self, start_url: str, target_dir: str):
        """
        NY V43: Native Python SiteRipper via Playwright.
        Knuser Cloudflare, fuld Asset-Mirroring (JS/CSS), Cookie-Auth og Offline DB-Handoff.
        """
        print(f"{C.YELLOW}[*] Udfører Advanced Python DOM-SiteRip for at omgå WAF og JS-walls...{C.RESET}")
        
        # NYT V44: Klargør mappe til opsnappede API-kald
        network_capture_dir = os.path.join(target_dir, "network_captures")
        
        # Sender cookies_file ind, så browseren tjekker om vi har givet den en auth-session
        config = BrowserConfig(
            headless=True, 
            js_rendering=True, 
            anti_detection=True, 
            cookies_file="cookies.json",
            network_capture=True,
            network_capture_dir=network_capture_dir)
        browser = OmniHunterBrowser(config)
        browser.start()
        
        visited = set()
        to_visit = [start_url]
        base_domain = urlparse(start_url).netloc
        max_pages = 25 # Begrænsning for OPSEC og tid, kan hæves til dybere rips
        
        # Opsæt mappe til javascript, css og billeder
        assets_dir = os.path.join(target_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        def fetch_and_replace_asset(el, attr, a_url):
            """Suger asset ned over stealth network.py tråd og omskriver kildekoden lokalt."""
            try:
                from core.network import http
                res = http.get(a_url, timeout=10)
                if res.status_code == 200:
                    a_name = sanitize_filename(os.path.basename(urlparse(a_url).path)) or str(hash(a_url))
                    a_path = os.path.join(assets_dir, a_name)
                    with open(a_path, 'wb') as af: af.write(res.content)
                    el[attr] = f"assets/{a_name}"
            except: pass

        try:
            for i in range(max_pages):
                if not to_visit: break
                current_url = to_visit.pop(0)
                if current_url in visited: continue
                
                visited.add(current_url)
                print(f"{C.DIM}    -> Spejler side: {current_url}{C.RESET}")
                
                res = browser.fetch(current_url)
                html = res.get("html", "")
                captured_network_files = res.get("captured_files", [])
                if captured_network_files:
                    print(f"{C.MAGENTA}    -> Opsnappede {len(captured_network_files)} skjulte API-kald!{C.RESET}")

                if not html: continue
                
                # THE DOM REWRITER: Trækker CSS, JS og Billeder ned
                soup = BeautifulSoup(html, "html.parser")
                asset_tasks = []
                for tag, attr in [('script', 'src'), ('link', 'href'), ('img', 'src')]:
                    for el in soup.find_all(tag):
                        link = el.get(attr)
                        if link and not link.startswith('data:'):
                            asset_tasks.append((el, attr, urljoin(current_url, link)))

                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(fetch_and_replace_asset, el, attr, a_url) for el, attr, a_url in asset_tasks]
                    concurrent.futures.wait(futures)

                # Skab et filnavn baseret på stien
                parsed_url = urlparse(current_url)
                safe_name = parsed_url.path.strip("/").replace("/", "_") or "index"
                if not safe_name.endswith(".html"): safe_name += ".html"
                
                file_path = os.path.join(target_dir, safe_name)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(str(soup))
                    
                # Find flere interne links at klone
                for a in soup.find_all("a", href=True):
                    next_url = urljoin(start_url, a["href"])
                    # Krav: Skal være samme domæne, og vi vil ikke rippe log-out links osv.
                    if urlparse(next_url).netloc == base_domain and next_url not in visited:
                        if next_url not in to_visit:
                            to_visit.append(next_url)
                            
                time.sleep(1.5) # Gaussian delay for at undgå rate-limits
                
        except Exception as e:
            print(f"{C.RED}[!] Fejl under Python SiteRip: {e}{C.RESET}")
        finally:
            browser.close()
            
        print(f"{C.GREEN}[+] Kloning af struktur, aktiver og netværkskald fuldført!{C.RESET}")
        
        # =====================================================================
        # GOLIATH V43 AUTONOMOUS HANDOFF: OFFLINE DATABASE ANALYZER
        # =====================================================================
        print(f"{C.YELLOW}[*] Overdrager den klonede kildekode til Modul 03 for Secret Scanning...{C.RESET}")
        try:
            from modules.mod_03_offline import OfflineDatabaseAnalyzer
            # Søger efter domænet, firmanavnet eller "API" som target key i kildekoden
            db_scanner = OfflineDatabaseAnalyzer(target=base_domain.replace("www.", "").split(".")[0], file_path=target_dir)
            scan_results = db_scanner.run()
            if scan_results and scan_results.get("Hits"):
                self.data["Offline_Scan_Findings"] = scan_results
        except ImportError:
            print(f"{C.DIM}[-] Modul 03 ikke fundet. Handoff afbrudt.{C.RESET}")
