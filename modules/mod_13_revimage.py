# -*- coding: utf-8 -*-
import os
import json
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.utils import C, session
from core.network import safe_get_with_retry

class ReverseImageIntelligence:
    def __init__(self, image_path):
        self.image_path = image_path.strip()
        self.data = {
            "Billede": os.path.basename(image_path),
            "Yandex_URL": "",
            "TinEye_URL": "",        # NY V8 TILFØJELSE
            "Google_Lens_URL": "",   # NY V8 TILFØJELSE
            "Google_Klar": False,
            "Bing_Klar": False,
            "AI_Deepfake_Mistanke": False, # NY V8 TILFØJELSE
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[13] Omvendt Billedsøgning (Multi-Tab OSINT & Deepfake Tjek V8)\n{'='*60}{C.RESET}")
        
        if not os.path.exists(self.image_path):
            print(f"{C.RED}[!] Fejl: Billede ikke fundet på stien: {self.image_path}{C.RESET}")
            return
            
        # Beskyttelse mod gigantiske filer der crasher browseren
        if os.path.getsize(self.image_path) > 15 * 1024 * 1024:
            print(f"{C.RED}[!] Filen er for stor (>15MB). Komprimer den først.{C.RESET}")
            return

        # 1. Præ-Analyse for Autenticitet og AI
        self._analyze_authenticity()
        
        # 2. Tjek adgang til portaler
        self._check_google_bing(driver)
        
        # 3. Yandex Auto-Upload (Kører i fane 1)
        self._yandex_auto_upload(driver)
        
        # 4. TinEye Auto-Upload (Kører i fane 2)
        self._tineye_auto_upload(driver)
        
        # 5. Google Lens Auto-Upload (Forsøges i fane 3)
        self._google_lens_auto_upload(driver)

        self.save()

    def _analyze_authenticity(self):
        """Udvidet til også at inkludere AI / Deepfake Heuristik"""
        print(f"\n{C.YELLOW}[*] Kører lokal visuel præ-analyse (Autenticitet & AI-Tjek)...{C.RESET}")
        try:
            img = Image.open(self.image_path)
            score = 0
            
            # --- NY V8 TILFØJELSE: AI Signatur Tjek ---
            ai_signatures = ["midjourney", "dall-e", "stable diffusion", "ai generated", "comfyui"]
            exif_data = img.getexif()
            
            if exif_data:
                score += 20
                for tag_id, value in exif_data.items():
                    val_str = str(value).lower()
                    if any(ai_tag in val_str for ai_tag in ai_signatures):
                        self.data["AI_Deepfake_Mistanke"] = True
                        print(f"{C.RED}    [!] KRITISK ADVARSEL: AI-Genererings signatur fundet i EXIF data! ({val_str}){C.RESET}")
            else:
                print(f"{C.DIM}    [-] Ingen EXIF data fundet (Ofte tegn på SoMe-scrubbing eller AI-generering).{C.RESET}")

            # --- NY V8 TILFØJELSE: Aspect Ratio Tjek (AI generatorer bruger ofte 1:1) ---
            width, height = img.size
            if width == height and width in [512, 1024, 2048]:
                self.data["AI_Deepfake_Mistanke"] = True
                print(f"{C.RED}    [!] ADVARSEL: Opløsningen ({width}x{height}) er en klassisk AI-generator standard!{C.RESET}")
                score -= 10
            
            if img.size[0] > 1920: 
                score += 15
                
            print(f"{C.GREEN}    ✓ Metadata og Opløsning analyseret (Autenticitets-score: {score}).{C.RESET}")
            
        except Exception as e: 
            print(f"{C.DIM}    [-] Kunne ikke analysere billede lokalt: {e}{C.RESET}")

    def _check_google_bing(self, driver):
        """Tjekker om portalerne er tilgængelige for manuel søgning"""
        print(f"\n{C.YELLOW}[*] Checker adgang til vestlige Reverse-Image portaler...{C.RESET}")
        try:
            if safe_get_with_retry(driver, "https://www.google.com/imghp"):
                print(f"{C.GREEN}    ✓ Google Lens portal er tilgængelig{C.RESET}")
                self.data["Google_Klar"] = True
            if safe_get_with_retry(driver, "https://www.bing.com/images"):
                print(f"{C.GREEN}    ✓ Bing Visual Search er tilgængelig{C.RESET}")
                self.data["Bing_Klar"] = True
        except Exception: pass

    def _yandex_auto_upload(self, driver):
        """Udfører den automatiske ansigts/billede søgning på Yandex (Markant bedre til ansigter)"""
        print(f"\n{C.YELLOW}[*] Auto-uploader {os.path.basename(self.image_path)} til Yandex Vision...{C.RESET}")
        try:
            # Sørg for at vi er i den rigtige fane
            driver.switch_to.window(driver.window_handles[0])
            driver.get("https://yandex.com/images/")
            
            # Smart klik på kamera ikon
            try:
                cam_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Image search'], button[title='Image search']"))
                )
                cam_btn.click()
            except Exception:
                # Fallback hvis yandex UI har ændret sig
                driver.get("https://yandex.com/images/search?rpt=imageview")
            
            time.sleep(1.5)
            
            # Finder den usynlige file-input og injicerer billedet direkte
            file_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            # Sikrer absolut sti uanset styresystem
            abs_path = os.path.abspath(self.image_path)
            file_input.send_keys(abs_path)
            
            print(f"{C.CYAN}    [*] Uploader billede. Venter på Yandex analyse...{C.RESET}")
            
            # Venter tålmodigt på resultatsiden
            WebDriverWait(driver, 25).until(
                lambda d: "rpt=imageview" not in d.current_url or len(d.find_elements(By.CSS_SELECTOR, ".CbirItem")) > 0
            )
            
            self.data["Yandex_URL"] = driver.current_url
            print(f"{C.GREEN}    ✓ Yandex Analyse færdig! Ansigts/Objekt genkendelse udført.{C.RESET}")
            print(f"{C.CYAN}    -> ÅBN RESULTAT HER: {self.data['Yandex_URL'][:100]}...{C.RESET}")
            
        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved Yandex upload (Browser timeout eller UI blokering): {e}{C.RESET}")

    def _tineye_auto_upload(self, driver):
        """NY V8 TILFØJELSE: Åbner en ny fane og uploader til TinEye (Bedst til at finde kilde-hjemmesider)"""
        print(f"\n{C.YELLOW}[*] Auto-uploader til TinEye (Global Reverse Image Search)...{C.RESET}")
        try:
            # Åbn ny fane
            driver.execute_script("window.open('https://tineye.com/', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            
            file_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'], input#upload_box"))
            )
            abs_path = os.path.abspath(self.image_path)
            file_input.send_keys(abs_path)
            
            print(f"{C.CYAN}    [*] Uploader billede til TinEye...{C.RESET}")
            
            WebDriverWait(driver, 20).until(
                lambda d: "result" in d.current_url.lower() or "search" in d.current_url.lower()
            )
            
            self.data["TinEye_URL"] = driver.current_url
            print(f"{C.GREEN}    ✓ TinEye Analyse færdig!{C.RESET}")
            print(f"{C.CYAN}    -> ÅBN RESULTAT HER: {self.data['TinEye_URL'][:100]}...{C.RESET}")
            
        except Exception as e:
            print(f"{C.DIM}    [-] TinEye auto-upload fejlede (UI Ændring eller Timeout): {e}{C.RESET}")

    def _google_lens_auto_upload(self, driver):
        """NY V8 TILFØJELSE: Forsøger at injicere lokalt billede i Google Lens"""
        print(f"\n{C.YELLOW}[*] Forsøger injektion i Google Lens...{C.RESET}")
        try:
            driver.execute_script("window.open('https://images.google.com/', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            
            # Prøver at klikke på Lens kamera-ikonet
            try:
                lens_btn = driver.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label*='Søg på billede'], div[role='button'][aria-label*='Search by image']")
                driver.execute_script("arguments[0].click();", lens_btn)
                time.sleep(1)
            except: pass
            
            # Injicerer filen
            file_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            abs_path = os.path.abspath(self.image_path)
            file_input.send_keys(abs_path)
            
            print(f"{C.CYAN}    [*] Uploader til Google Lens...{C.RESET}")
            
            WebDriverWait(driver, 20).until(
                lambda d: "lens" in d.current_url.lower() or "search" in d.current_url.lower()
            )
            
            self.data["Google_Lens_URL"] = driver.current_url
            print(f"{C.GREEN}    ✓ Google Lens Analyse færdig!{C.RESET}")
            print(f"{C.CYAN}    -> ÅBN RESULTAT HER: {self.data['Google_Lens_URL'][:100]}...{C.RESET}")
            
        except Exception as e:
            print(f"{C.DIM}    [-] Google Lens auto-injektion fejlede (Google blokerer ofte automation): {e}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/13_REVERSE_IMAGE_{os.path.basename(self.image_path).replace('.', '_')}.json"
        
        # NY V8 TILFØJELSE: Sikker fil-overskrivning
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Billed-rapport gemt: {filename}{C.RESET}")