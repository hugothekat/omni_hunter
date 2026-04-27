# -*- coding: utf-8 -*-
import json
import os
import requests
import sys
import re
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.utils import C, session
from core.network import omni_dork_search, safe_get_with_retry

class SocialMediaProfiler:
    def __init__(self, username):
        self.username = username.strip()
        # Hvis input er et fuldt navn, gemmer vi det til alias-generering
        self.full_name = username if " " in username else None
        self.data = {
            "Brugernavn": self.username,
            "Fuldt_Navn": self.full_name,
            "Deep_Scrape": {}, 
            "Fundne_Profiler": [],
            "Identificerede_Aliaser": [],
            "Timestamp": datetime.now().isoformat(),
            "Network_Intelligence": {"Inner_Circle": []},
    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[04] GOLIATH SOCIAL STALKER (MONSTER EDITION)\n{'='*60}{C.RESET}")
        
        # --- NYT: ALIAS GENERERING ---
        if self.full_name:
            print(f"{C.YELLOW}[*] Genererer sandsynlige brugernavne ud fra navn...{C.RESET}")
            self._generate_aliases()
            print(f"      -> Aliaser: {', '.join(self.data['Identificerede_Aliaser'][:5])}...")

        # --- EKSISTERENDE GITHUB SCRAPE (Bibeholdt) ---
        print(f"\n{C.YELLOW}[*] Udfører Deep Scrape på GitHub...{C.RESET}")
        github_url = f"https://github.com/{self.username}"
        if safe_get_with_retry(driver, github_url):
            if "404" not in driver.title and "Not Found" not in driver.title:
                self._scrape_github(driver)

        # --- NYT: INSTAGRAM DEEP SCRAPE (Cemile Specific) ---
        # Hvis vi har et alias som cemileb.c, prøver vi at scrape det direkte
        insta_handle = self.username if "." in self.username or "_" in self.username else "cemileb.c"
        print(f"\n{C.YELLOW}[*] Udfører Deep Scrape på Instagram (@{insta_handle})...{C.RESET}")
        self._scrape_instagram(driver, insta_handle)

        # --- NYT: TIKTOK DEEP SCRAPE ---
        print(f"\n{C.YELLOW}[*] Udfører Deep Scrape på TikTok...{C.RESET}")
        self._scrape_tiktok(driver, self.username)

        # --- EKSISTERENDE MASSIV DORKING MATRIX (Bibeholdt & Forbedret) ---
        print(f"\n{C.YELLOW}[*] Udruller massiv OSINT Dorking Matrix over 40+ platforme...{C.RESET}")
        
        international_sites = [
            "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", 
            "twitter.com", "x.com", "reddit.com/user", "pinterest.com", 
            "youtube.com", "twitch.tv", "steamcommunity.com/id", 
            "tinder.com", "badoo.com", "vk.com", "medium.com", "github.com",
            "t.me", "vimeo.com", "soundcloud.com", "spotify.com", "snapchat.com/add"
        ]
        
        danish_sites = [
            "dba.dk", "guloggratis.dk", "scor.dk", "dating.dk", 
            "holdet.dk", "amino.dk", "hardwareonline.dk", "studieportalen.dk", 
            "trustpilot.com/users", "kino.dk", "boligportal.dk", "heste-nettet.dk", "trendsales.dk"
        ]
        
        all_platforms = international_sites + danish_sites
        
        # Vi tilføjer navne-søgning til dorking hvis vi har et fuldt navn
        search_term = f'"{self.full_name}"' if self.full_name else f'"{self.username}"'
        
        chunk_size = 4
        for i in range(0, len(all_platforms), chunk_size):
            total_chunks = (len(all_platforms) + chunk_size - 1) // chunk_size
            current_chunk = (i // chunk_size) + 1
            pct = int((current_chunk / total_chunks) * 100)
            
            sys.stdout.write(f"\r{C.CYAN}    [*] Skanner platform matrix... {pct}% ({all_platforms[i]})      {C.RESET}")
            sys.stdout.flush()
            
            chunk = all_platforms[i:i+chunk_size]
            sites_query = " OR ".join([f"site:{site}" for site in chunk])
            dork = f'({sites_query}) {search_term}'
            
            links = omni_dork_search(driver, dork, max_links=6)
            if links:
                for link in links:
                    url = link['url']
                    titel = link.get('text', '')
                    
                    if any(p.replace('/user', '').replace('/id', '').replace('/users', '').replace('/add', '') in url for p in chunk):
                        sys.stdout.write("\r" + " " * 80 + "\r")
                        print(f"{C.GREEN}    🔥 SPOR FUNDET: {url}{C.RESET}")
                        if not any(p['URL'] == url for p in self.data["Fundne_Profiler"]):
                            self.data["Fundne_Profiler"].append({"URL": url, "Kontekst": titel})

        print(f"\n{C.GREEN}[✓] Profil-scanning komplet.{C.RESET}")
        self.save()

    def _generate_aliases(self):
        """Kreativ generering af brugernavne ud fra navn"""
        if not self.full_name: return
        parts = self.full_name.lower().split()
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            m = parts[1] if len(parts) > 2 else ""
            self.data["Identificerede_Aliaser"].extend([
                f"{f}{l}", f"{f}.{l}", f"{f}_{l}", f"{f}{l[0]}", 
                f"{f}{m}{l}", f"{f}.{m}.{l}", f"{f}{m[0]}.{l[0]}"
            ])

    # --- Tilføj/Opdater denne metode i mod_04_social.py ---
    def _scrape_instagram(self, driver, handle):
        """Deep Scrape af Instagram Bio og Stats med fokus på SOSU-info"""
        url = f"https://www.instagram.com/{handle}/"
        if safe_get_with_retry(driver, url):
            time.sleep(4) # Giv den tid til at loade bio
            try:
                # Find bio-containeren
                bio_elements = driver.find_elements(By.CSS_SELECTOR, "header section div.-v79Z, header section div.Qpx6u")
                if not bio_elements:
                    bio_elements = driver.find_elements(By.XPATH, "//header//section")

                if bio_elements:
                    bio_text = bio_elements[0].text
                    self.data["Deep_Scrape"]["Instagram"] = {
                        "Handle": handle,
                        "Raw_Bio": bio_text
                    }
                    print(f"{C.GREEN}    ✓ Instagram Bio udtrukket:{C.RESET}")
                    # Her printer vi specifikt bio-linjerne ud i terminalen
                    for line in bio_text.split('\n'):
                        if line.strip():
                            print(f"      -> {C.CYAN}{line.strip()}{C.RESET}")
                
                # Gem profilbillede til Reverse Image Search
                img = driver.find_elements(By.CSS_SELECTOR, "header img")
                if img:
                    self._download_avatar(img[0].get_attribute("src"), "Instagram")
                    self._image_forensics_pivot(img[0].get_attribute("src"), "Instagram")
                    self._analyze_network_intelligence(driver)
            except Exception as e:
                print(f"{C.DIM}      [-] Kunne ikke udtrække fuld bio: {e}{C.RESET}")

    def _scrape_tiktok(self, driver, handle):
        """Deep Scrape af TikTok profiler"""
        url = f"https://www.tiktok.com/@{handle}"
        if safe_get_with_retry(driver, url):
            try:
                title = driver.title
                if "@" in title:
                    bio = driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-bio']").text
                    stats = driver.find_element(By.CSS_SELECTOR, "[data-e2e='user-stats']").text
                    self.data["Deep_Scrape"]["TikTok"] = {"Bio": bio, "Stats": stats}
                    print(f"{C.GREEN}    ✓ TikTok Profil fundet!{C.RESET}")
                    print(f"      -> Bio: {bio}")
            except Exception: pass

    def _scrape_github(self, driver):
        """Eksisterende GitHub logik pakket ind for renhed"""
        try:
            navn_el = driver.find_elements(By.CSS_SELECTOR, "span.p-name")
            bio_el = driver.find_elements(By.CSS_SELECTOR, "div.p-note")
            img_el = driver.find_elements(By.CSS_SELECTOR, "img.avatar-user")
            navn = navn_el[0].text if navn_el else "Ukendt"
            bio = bio_el[0].text if bio_el else ""
            billede_url = img_el[0].get_attribute("src") if img_el else None
            self.data["Deep_Scrape"]["GitHub"] = {"Navn": navn, "Bio": bio}
            print(f"{C.GREEN}    ✓ GitHub intel udtrukket.{C.RESET}")
            if billede_url: self._download_avatar(billede_url, "GitHub")
        except Exception: pass

    def _download_avatar(self, url, platform):
        try:
            img_data = requests.get(url, timeout=10).content
            mappe = os.path.join(session["loot_folder"], "avatars")
            os.makedirs(mappe, exist_ok=True)
            filsti = os.path.join(mappe, f"{platform}_{self.username}.jpg")
            with open(filsti, 'wb') as handler:
                handler.write(img_data)
            print(f"{C.GREEN}      ✓ Profilbillede sikret: {platform}{C.RESET}")
        except Exception: pass

def _image_forensics_pivot(self, image_url, platform):
        """NY V7: Image Forensics & Reverse Search Generation"""
        print(f"{C.MAGENTA}    [*] Image Forensics på {platform}: Genererer Reverse Search...{C.RESET}")
        try:
            import urllib.parse
            encoded_url = urllib.parse.quote(image_url)
            print(f"      -> Google Lens: https://www.google.com/searchbyimage?image_url={encoded_url}")
            print(f"      -> Yandex: https://yandex.com/images/search?url={encoded_url}")
        except: pass

    def _analyze_network_intelligence(self, driver):
        """NY V7: Finder 'Inner Circle' leads via tags/mentions"""
        print(f"{C.YELLOW}    [*] Scanner efter Network Intelligence (mentions)...{C.RESET}")
        try:
            elements = driver.find_elements(By.PARTIAL_LINK_TEXT, "@")
            for el in elements:
                handle = el.text.replace("@", "")
                if handle and handle not in self.data["Network_Intelligence"]["Inner_Circle"]:
                    self.data["Network_Intelligence"]["Inner_Circle"].append(handle)
                    print(f"{C.CYAN}      -> Inner Circle Lead fundet: @{handle}{C.RESET}")
        except: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/04_SOCIAL_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"{C.GREEN}[✓] Omfattende profil-rapport gemt: {filename}{C.RESET}")