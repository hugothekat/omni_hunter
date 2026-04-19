# modules/mod_04_social.py
import json
import os
from pathlib import Path
from datetime import datetime

# Henter fra Core
from core.utils import C, session
from core.network import safe_get_with_retry, omni_dork_search

class SocialMediaProfiler:
    def __init__(self, username):
        self.username = username.strip()
        self.data = {"Brugernavn": self.username, "Direct_Hits": [], "Dork_Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[04] Social Media Profiler\n{'='*60}{C.RESET}")
        print(f"Username: {self.username}\n")
        
        # 1. Direkte hits
        for platform, url in {"GitHub": f"https://github.com/{self.username}", "TikTok": f"https://www.tiktok.com/@{self.username}"}.items():
            if safe_get_with_retry(driver, url) and "404" not in driver.title.lower():
                print(f"{C.GREEN}    ✓ {platform}: {url}{C.RESET}")
                self.data["Direct_Hits"].append(url)
        
        # 2. Dorking efter profiler (Anti-Ban)
        platforms = ["facebook.com", "instagram.com", "linkedin.com", "dba.dk", "twitter.com"]
        for site in platforms:
            dork = f'site:{site} "{self.username}"'
            links = omni_dork_search(driver, dork, max_links=2)
            for link in links:
                if site in link['url']:
                    print(f"{C.GREEN}    ✓ FUNDET PÅ {site.upper()}: {link['url']}{C.RESET}")
                    self.data["Dork_Hits"].append(link['url'])
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/04_SOCIAL_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")