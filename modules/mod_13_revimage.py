import os
import json
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from core.utils import C, session
from core.network import safe_get_with_retry

class ReverseImageIntelligence:
    def __init__(self, image_path):
        self.image_path = image_path.strip()
        self.data = {
            "Billede": os.path.basename(image_path),
            "Yandex_URL": "",
            "Google_Klar": False,
            "Bing_Klar": False,
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[13] Omvendt Billedsøgning (Yandex + Google + Bing)\n{'='*60}{C.RESET}")
        
        if not os.path.exists(self.image_path):
            print(f"{C.RED}[!] Billede ikke fundet: {self.image_path}{C.RESET}")
            return
            
        self._analyze_authenticity()
        self._check_google_bing(driver)
        self._yandex_auto_upload(driver)
        self.save()

    def _check_google_bing(self, driver):
        """Tjekker om portalerne er tilgængelige for manuel søgning"""
        print(f"\n{C.YELLOW}[*] Checker adgang til Google Lens og Bing Visual...{C.RESET}")
        try:
            if safe_get_with_retry(driver, "https://www.google.com/imghp"):
                print(f"{C.GREEN}    ✓ Google Images er tilgængelig{C.RESET}")
                self.data["Google_Klar"] = True
            if safe_get_with_retry(driver, "https://www.bing.com/images"):
                print(f"{C.GREEN}    ✓ Bing Images er tilgængelig{C.RESET}")
                self.data["Bing_Klar"] = True
        except Exception: pass

    def _yandex_auto_upload(self, driver):
        """Udfører den automatiske ansigts/billede søgning på Yandex"""
        print(f"\n{C.YELLOW}[*] Auto-uploader {os.path.basename(self.image_path)} til Yandex...{C.RESET}")
        try:
            driver.get("https://yandex.com/images/")
            time.sleep(2)
            cam_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Image search'], button[title='Image search']")
            if cam_btn: cam_btn[0].click()
            else: driver.get("https://yandex.com/images/search?rpt=imageview")
            
            time.sleep(2)
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(self.image_path))
            
            print(f"{C.CYAN}    [*] Uploader billede og analyserer...{C.RESET}")
            # Vi venter max 20 sek på at url'en skifter væk fra upload-siden ELLER et resultat popper op
            WebDriverWait(driver, 20).until(
                lambda d: "rpt=imageview" not in d.current_url or len(d.find_elements(By.CSS_SELECTOR, ".CbirItem")) > 0
            )
            
            self.data["Yandex_URL"] = driver.current_url
            print(f"{C.GREEN}    ✓ Yandex Analyse færdig!{C.RESET}")
            print(f"{C.CYAN}    -> RESULTAT LINK: {self.data['Yandex_URL'][:80]}...{C.RESET}")
            
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved Yandex upload: {e}{C.RESET}")

    def _analyze_authenticity(self):
        """Dit originale integritets-tjek"""
        print(f"{C.YELLOW}[*] Lokal Authenticity Analysis{C.RESET}")
        try:
            img = Image.open(self.image_path)
            score = 0
            if hasattr(img, '_getexif') and img._getexif(): score += 20
            if img.size[0] > 1920: score += 15
            print(f"{C.GREEN}    ✓ Metadata og Opløsning analyseret. Score: {score}{C.RESET}")
        except Exception: pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/13_REVERSE_IMAGE_{os.path.basename(self.image_path).replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")