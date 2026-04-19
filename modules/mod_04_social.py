# modules/mod_04_social.py
import json
import os
import requests
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By

from core.utils import C, session
from core.network import omni_dork_search, safe_get_with_retry

class SocialMediaProfiler:
    def __init__(self, username):
        self.username = username.strip()
        self.data = {"Brugernavn": self.username, "Profiler": [], "Deep_Scrape": {}, "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[04] Social Media Deep Profiler\n{'='*60}{C.RESET}")
        print(f"Username: {self.username}\n")
        
        # DEEP SCRAPE (GitHub Eksempel)
        github_url = f"https://github.com/{self.username}"
        print(f"{C.YELLOW}[*] Forsøger Deep Scrape på GitHub profil...{C.RESET}")
        
        if safe_get_with_retry(driver, github_url):
            if "404" not in driver.title:
                print(f"{C.GREEN}    ✓ Profil fundet! Udtrækker data...{C.RESET}")
                self.data["Profiler"].append(github_url)
                
                try:
                    navn = driver.find_element(By.CSS_SELECTOR, "span.p-name").text
                    bio = driver.find_element(By.CSS_SELECTOR, "div.p-note").text
                    billede_url = driver.find_element(By.CSS_SELECTOR, "img.avatar-user").get_attribute("src")
                    
                    self.data["Deep_Scrape"]["GitHub"] = {"Navn": navn, "Bio": bio}
                    print(f"      -> Registreret Navn: {navn}")
                    print(f"      -> Biografi: {bio.replace(chr(10), ' ')}")
                    
                    # Bevissikring: Download Profilbillede
                    if billede_url:
                        self._download_avatar(billede_url, "GitHub")
                except Exception:
                    print(f"{C.DIM}      [-] Kunne ikke udtrække alle elementer.{C.RESET}")

        # DORKING ALMINDELIGE PROFILER
        print(f"\n{C.YELLOW}[*] Dorking for at finde andre sociale medier...{C.RESET}")
        platforms = ["facebook.com", "instagram.com", "linkedin.com", "tiktok.com"]
        for site in platforms:
            dork = f'site:{site} "{self.username}"'
            links = omni_dork_search(driver, dork, max_links=2)
            for link in links:
                if site in link['url']:
                    print(f"{C.GREEN}    ✓ FUNDET PÅ {site.upper()}: {link['url']}{C.RESET}")
                    self.data["Profiler"].append(link['url'])

        self.save()

    def _download_avatar(self, url, platform):
        try:
            img_data = requests.get(url, timeout=10).content
            mappe = os.path.join(session["loot_folder"], "avatars")
            os.makedirs(mappe, exist_ok=True)
            filsti = os.path.join(mappe, f"{platform}_{self.username}.jpg")
            with open(filsti, 'wb') as handler:
                handler.write(img_data)
            print(f"{C.GREEN}      ✓ Profilbillede sikret: {filsti}{C.RESET}")
        except Exception: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/04_SOCIAL_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")