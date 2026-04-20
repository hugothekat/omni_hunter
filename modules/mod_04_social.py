# -*- coding: utf-8 -*-
import json
import os
import requests
import sys
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By

from core.utils import C, session
from core.network import omni_dork_search, safe_get_with_retry

class SocialMediaProfiler:
    def __init__(self, username):
        self.username = username.strip()
        self.data = {
            "Brugernavn": self.username, 
            "Deep_Scrape": {}, 
            "Fundne_Profiler": [], 
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[04] Social Media Profiler (MONSTER EDITION)\n{'='*60}{C.RESET}")
        print(f"Søger efter spor på: {self.username}\n")
        
        # 1. DEEP SCRAPE (GitHub - med Avatar Download)
        github_url = f"https://github.com/{self.username}"
        print(f"{C.YELLOW}[*] Udfører Deep Scrape på primære platforme...{C.RESET}")
        
        if safe_get_with_retry(driver, github_url):
            if "404" not in driver.title and "Not Found" not in driver.title:
                print(f"{C.GREEN}    ✓ GitHub profil fundet! Udtrækker intel...{C.RESET}")
                try:
                    navn_el = driver.find_elements(By.CSS_SELECTOR, "span.p-name")
                    bio_el = driver.find_elements(By.CSS_SELECTOR, "div.p-note")
                    img_el = driver.find_elements(By.CSS_SELECTOR, "img.avatar-user")

                    navn = navn_el[0].text if navn_el else "Ukendt"
                    bio = bio_el[0].text if bio_el else ""
                    billede_url = img_el[0].get_attribute("src") if img_el else None
                    
                    self.data["Deep_Scrape"]["GitHub"] = {"Navn": navn, "Bio": bio}
                    print(f"      -> Navn: {navn}")
                    if bio: print(f"      -> Bio: {bio.replace(chr(10), ' ')}")
                    
                    if billede_url:
                        self._download_avatar(billede_url, "GitHub")
                except Exception as e:
                    print(f"{C.DIM}      [-] Profil fundet, men fejl ved dataudtræk: {e}{C.RESET}")

        # 2. MASSIV DORKING MATRIX (International + Dansk)
        print(f"\n{C.YELLOW}[*] Udruller massiv OSINT Dorking Matrix over 40+ platforme...{C.RESET}")
        
        international_sites = [
            "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", 
            "twitter.com", "x.com", "reddit.com/user", "pinterest.com", 
            "youtube.com", "twitch.tv", "steamcommunity.com/id", 
            "tinder.com", "badoo.com", "vk.com", "medium.com", "github.com",
            "t.me", "vimeo.com", "soundcloud.com", "spotify.com/user", "snapchat.com/add"
        ]
        
        danish_sites = [
            "dba.dk", "guloggratis.dk", "scor.dk", "dating.dk", 
            "holdet.dk", "amino.dk", "hardwareonline.dk", "studieportalen.dk", 
            "trustpilot.com/users", "kino.dk", "boligportal.dk", "heste-nettet.dk", "trendsales.dk"
        ]
        
        all_platforms = international_sites + danish_sites
        
        chunk_size = 4
        for i in range(0, len(all_platforms), chunk_size):
            total_chunks = (len(all_platforms) + chunk_size - 1) // chunk_size
            current_chunk = (i // chunk_size) + 1
            pct = int((current_chunk / total_chunks) * 100)
            
            sys.stdout.write(f"\r{C.CYAN}    [*] Skanner platform matrix... {pct}% ({all_platforms[i]})      {C.RESET}")
            sys.stdout.flush()
            
            chunk = all_platforms[i:i+chunk_size]
            sites_query = " OR ".join([f"site:{site}" for site in chunk])
            dork = f'({sites_query}) "{self.username}"'
            
            links = omni_dork_search(driver, dork, max_links=6)
            if links:
                for link in links:
                    url = link['url']
                    titel = link.get('text', '')
                    
                    # Validering: Sikrer at domænet fra vores chunk faktisk er i URL'en
                    if any(p.replace('/user', '').replace('/id', '').replace('/users', '').replace('/add', '') in url for p in chunk):
                        sys.stdout.write("\r" + " " * 80 + "\r") # Ryd linjen før vi printer fund
                        print(f"{C.GREEN}    🔥 SPOR FUNDET: {url}{C.RESET}")
                        if titel:
                            print(f"{C.CYAN}      -> Kontekst: {titel[:70]}...{C.RESET}")
                        
                        if not any(p['URL'] == url for p in self.data["Fundne_Profiler"]):
                            self.data["Fundne_Profiler"].append({"URL": url, "Kontekst": titel})

        print(f"\n{C.GREEN}[✓] Profil-scanning komplet.{C.RESET}")
        self.save()

    def _download_avatar(self, url, platform):
        try:
            img_data = requests.get(url, timeout=10).content
            mappe = os.path.join(session["loot_folder"], "avatars")
            os.makedirs(mappe, exist_ok=True)
            filsti = os.path.join(mappe, f"{platform}_{self.username}.jpg")
            with open(filsti, 'wb') as handler:
                handler.write(img_data)
            print(f"{C.GREEN}      ✓ Profilbillede sikret til Reverse Image Search: {filsti}{C.RESET}")
        except Exception: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/04_SOCIAL_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"{C.GREEN}[✓] Omfattende profil-rapport gemt ({len(self.data['Fundne_Profiler'])} hits): {filename}{C.RESET}")