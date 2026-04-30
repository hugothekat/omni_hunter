# -*- coding: utf-8 -*-
"""
🚀 GOLIATH TITAN V36: FULL SPECTRUM FORENSICS & AUTO-PIVOT
📌 Formål: Den mest komplette kombination af OSINT, heuristisk analyse og digital forensik.
"""

import sys
from pathlib import Path
# Sikrer at modulet altid kan finde 'core', selv hvis det køres direkte!
sys.path.append(str(Path(__file__).resolve().parent.parent))
import tools
import os
import glob
import time
import json
import re
import zipfile
import tarfile
import hashlib
import math
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, Optional, List
import magic
import cv2
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
from PIL import UnidentifiedImageError
from PIL.ExifTags import TAGS

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, REGEX_EMAIL, datalake
from core.network import safe_get_with_retry
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Undgår cirkulære imports under init
try:
    from modules.mod_12_ai import TitanAIEnrichment
    from modules.mod_03_breach import BreachIntelligenceAnalyst
except ImportError:
    TitanAIEnrichment = None
    BreachIntelligenceAnalyst = None

HAS_OCR = True
HAS_PDF = True

class AutoForensicMassScanner(BaseModule):
    """TITAN Orchestrator: Den mest komplette kombination af OSINT og digital forensik (GOLIATH V36)."""
    
    def __init__(self, folder_path=""):
        super().__init__()
        self.name = "TITAN HEURISTIC ENGINE"
        self.description = "Dybdegående mass-scanning, OCR, EXIF, Entropy, dHash og Heuristik."
        self.category = ModuleCategory.FORENSICS
        self.folder_path = folder_path.strip() if folder_path else session.get("loot_folder", "loot")
        self.start_time = time.time()
        
        self.master_data = {
            "Meta": {"Sagsmappe": self.folder_path, "Timestamp": datetime.now().isoformat(), "Filer_Behandlet": 0, "Images_For_RevSearch": []},
            "Case_Intelligence": {
                "Verified_Identities": {}, 
                "Digital_Footprint": {"Emails": {}, "Social_Handles": set(), "IP_Adresser": set(), "Telefonnumre": set()},
                "Financial_Leads": {"Bankkonti": set(), "IBAN_Konti": set(), "Crypto_Seeds": [], "Keys_Secrets": [], "CVR": set()},
                "Physical_Leads": {"Adresser": set(), "Nummerplader": set(), "GPS_Data": []},
                "ID_Documents": {"MRZ_Koder": [], "CPR_Numre": set(), "Pasnumre": set()},
                "Timeline": {"Datoer_Fundet": set()}
            },
            "Metadata_Report": {}, 
            "Forensic_Hashes": {}, 
            "Reverse_Image_Hits": {},
            "AI_Deepfake_Mistanke": [],
            "Source_Map": {},
            "File_Integrity_Alerts": [], 
            "Berigelse_Resultater": {"Phone_Data": [], "Breach_Reports": [], "IP_Reports": []},
            "Raw_Text_Archive": {} 
        }

        # Regex overført fra utils for robusthed
        self.REGEX_BANK = re.compile(r'\b(?:Reg|Reg nr|Regnr|Bank)[.\s:]*([0-9]{4})[\s-]*([0-9]{6,10})\b', re.IGNORECASE)
        self.REGEX_CPR = re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b')
        self.REGEX_BTC = re.compile(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b')
        self.REGEX_ETH = re.compile(r'\b0x[a-fA-F0-9]{40}\b')

    def _convert_to_degrees(self, value):
        try:
            d, m, s = float(value[0]), float(value[1]), float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except Exception: return None

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[16] GOLIATH TITAN: FULL SPECTRUM FORENSICS V36\n{'='*60}{C.RESET}")
        if not os.path.exists(self.folder_path): 
            print(f"{C.RED}[!] Fejl: Stien {self.folder_path} findes ikke.{C.RESET}"); return self.data
        
        print(f"{C.YELLOW}[*] Step 1: Deep Unpacking af arkiver (.zip, .tar, .gz)...{C.RESET}")
        self._unpack_archives()

        files = [f for f in glob.glob(f"{self.folder_path}/**/*", recursive=True) if os.path.isfile(f)]
        self.master_data["Meta"]["Filer_Behandlet"] = len(files)

        print(f"{C.YELLOW}[*] Step 2: Starter synkroniseret OCR/Heuristik/Krypto-analyse af {len(files)} enheder (Max 8 tråde)...{C.RESET}")
        completed = 0
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._titan_process_file, f): f for f in files}
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                self._print_progress(completed, len(files))
                try:
                    res = future.result()
                    if res: self._ingest_results(res)
                except Exception:
                    pass
        
        print(f"\n{C.GREEN}[✓] Forensic Pipeline komplet. Starter automatisk Omni-Berigelse...{C.RESET}")
        self._auto_pivot_engine(driver)
        self._save_master_file(target)
        
        print(f"\n{C.CYAN}--- TITAN MISSION SUMMARY ---{C.RESET}")
        print(f"Filer Hashet (Krypto & Visuelt): {len(self.master_data['Forensic_Hashes'])}")
        print(f"Emails fundet: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['Emails'])}")
        print(f"Telefonnumre: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['Telefonnumre'])}")
        print(f"IP-Adresser: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['IP_Adresser'])}")
        print(f"Bankkonti/IBAN: {len(self.master_data['Case_Intelligence']['Financial_Leads']['Bankkonti']) + len(self.master_data['Case_Intelligence']['Financial_Leads']['IBAN_Konti'])}")
        print(f"CPR numre fundet: {len(self.master_data['Case_Intelligence']['ID_Documents']['CPR_Numre'])}")
        
        if self.master_data.get("File_Integrity_Alerts"):
            print(f"{C.RED}Steganografi & Heuristik Alerts: {len(self.master_data['File_Integrity_Alerts'])} filer flaget!{C.RESET}")
        
        if "Devices" in self.master_data["Case_Intelligence"]:
            print(f"Identificerede Enheder: {', '.join(self.master_data['Case_Intelligence']['Devices'].keys())}")
        if self.master_data.get("Reverse_Image_Hits"):
            print(f"Ansigter reverse-searched: {len(self.master_data['Reverse_Image_Hits'])}")
        print(f"{C.CYAN}----------------------------{C.RESET}")
        
        return self.master_data

    def _calculate_entropy(self, data: bytes) -> float:
        """Shannon Entropy beregner - Fanger krypterede payloads og malware blobs"""
        if not data: return 0.0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(x))/len(data)
            if p_x > 0:
                entropy += - p_x*math.log(p_x, 2)
        return entropy

    def _heuristic_malware_scan(self, f_bytes: bytes) -> List[str]:
        """NY V36: Scanner filens binære data for typiske malicious payloads / web shells."""
        alerts = []
        try:
            content = f_bytes.decode('utf-8', errors='ignore')
            # Leder efter PHP base64_decode web shells i billeder
            if re.search(r'eval\s*\(\s*base64_decode', content, re.IGNORECASE):
                alerts.append("PHP Base64 WebShell Signatur Detekteret")
            # Leder efter skjulte PowerShell kommandoer
            if re.search(r'powershell.*-WindowStyle\s+Hidden', content, re.IGNORECASE):
                alerts.append("Skjult PowerShell Eksekvering Detekteret")
            # Leder efter Windows commands i billeder
            if re.search(r'cmd\.exe\s+/c', content, re.IGNORECASE):
                alerts.append("CMD Eksekvering indlejret (Mulig Stego-Malware)")
        except Exception: pass
        return alerts

    def _calculate_dhash(self, img_path: str) -> Optional[str]:
        """NY V36: Perceptual Image Hashing (dHash). Tillader at finde visuelt identiske billeder."""
        try:
            with Image.open(img_path) as img:
                # Konverter til gråtone og resize til 9x8 for at beregne gradienter
                img = img.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
                pixels = list(img.getdata())
                diff = []
                # Beregn dHash forskellen mellem tilstødende pixels
                for row in range(8):
                    for col in range(8):
                        pixel_left = img.getpixel((col, row))
                        pixel_right = img.getpixel((col + 1, row))
                        diff.append(pixel_left > pixel_right)
                
                # Konverter binært array til HEX streng
                decimal_value = 0
                hex_string = []
                for index, value in enumerate(diff):
                    if value:
                        decimal_value += 2**(index % 8)
                    if (index % 8) == 7:
                        hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
                        decimal_value = 0
                return ''.join(hex_string)
        except (UnidentifiedImageError, OSError):
            return None
        except Exception:
            return None

    def _detect_faces(self, img_path: str) -> bool:
        """Bruger OpenCV Haar Cascades til at detektere ansigter til Auto-Pivot."""
        try:
            img = cv2.imread(img_path)
            if img is None: return False
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
            face_cascade = cv2.CascadeClassifier(cascade_path)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return len(faces) > 0
        except Exception:
            return False

    def _extract_office_metadata(self, f_path: str) -> dict:
        """Dyb ekstraktion af metadata fra .docx, .xlsx, .pptx"""
        meta = {}
        try:
            with zipfile.ZipFile(f_path, 'r') as z:
                # Udtager forfatter og oprettelse
                if 'docProps/core.xml' in z.namelist():
                    core_xml = z.read('docProps/core.xml').decode('utf-8')
                    creator = re.search(r'<dc:creator>(.*?)</dc:creator>', core_xml)
                    created = re.search(r'<dcterms:created[^>]*>(.*?)</dcterms:created>', core_xml)
                    if creator: meta["Document_Author"] = creator.group(1)
                    if created: meta["Document_Created"] = created.group(1)
                
                # NY V36: Udtager Software Version og Firma
                if 'docProps/app.xml' in z.namelist():
                    app_xml = z.read('docProps/app.xml').decode('utf-8')
                    app_name = re.search(r'<Application>(.*?)</Application>', app_xml)
                    company = re.search(r'<Company>(.*?)</Company>', app_xml)
                    if app_name: meta["Software_Application"] = app_name.group(1)
                    if company and company.group(1): meta["Corporate_Owner"] = company.group(1)
        except Exception: pass
        return meta

    def _extract_video_metadata(self, path: str) -> dict:
        """Udtrækker tekniske specs via OpenCV og metadata via ExifTool."""
        meta = {}
        try:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                meta["Video_FPS"] = round(cap.get(cv2.CAP_PROP_FPS), 2)
                meta["Video_Frames"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                meta["Video_Resolution"] = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                codec = int(cap.get(cv2.CAP_PROP_FOURCC))
                meta["Video_Codec"] = "".join([chr((codec >> 8 * i) & 0xFF) for i in range(4)])
                cap.release()
        except Exception: pass
        try:
            import subprocess
            res = subprocess.run(['exiftool', '-json', path], capture_output=True, text=True)
            if res.returncode == 0:
                edata = json.loads(res.stdout)[0]
                for k in ["CreateDate", "ModifyDate", "GPSCoordinates", "Make", "Model", "Software", "Duration"]:
                    if k in edata: meta[f"Exif_{k}"] = edata[k]
        except Exception: pass
        return meta

    def _titan_process_file(self, f_path):
        fname = os.path.basename(f_path)
        res = {"file": fname, "path": f_path, "text": "", "meta": {}, "mime": "unknown", "entities": {}, "face_detected": False}
        
        if f_path.lower().endswith('.zip') or f_path.lower().endswith('.tar.gz') or f_path.lower().endswith('.tar'):
            return res

        try:
            with open(f_path, 'rb') as bin_f:
                f_bytes = bin_f.read()
                res["meta"]["MD5"] = hashlib.md5(f_bytes).hexdigest()
                res["meta"]["SHA1"] = hashlib.sha1(f_bytes).hexdigest()
                res["meta"]["SHA256"] = hashlib.sha256(f_bytes).hexdigest()
                
                # Entropi & Heuristik
                entropy = self._calculate_entropy(f_bytes)
                res["meta"]["Entropy"] = round(entropy, 2)
                malware_alerts = self._heuristic_malware_scan(f_bytes)
                
                if entropy > 7.6:
                    res["meta"]["Steganografi_Advarsel"] = f"Ekstremt høj entropi ({round(entropy,2)}). Krypteret payload eller pakket malware mistænkes."
                if malware_alerts:
                    res["meta"]["Malware_Signaturer"] = malware_alerts
                    
                # RAW String Extraction (Søger efter skjulte netværksspor forbi obfuscation)
                raw_str = f_bytes.decode('ascii', errors='ignore')
                raw_emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_str))
                for em in raw_emails:
                    if "adobe" not in em.lower() and "w3.org" not in em.lower():
                        res["entities"].setdefault("emails", []).append({"val": em.lower(), "score": 30})

            mime_type = magic.from_file(f_path, mime=True)
            res["mime"] = mime_type if mime_type else "unknown"

            if "image" in res["mime"]:
                if res["mime"] in ["image/jpeg", "image/jpg"]:
                    eof_idx = f_bytes.rfind(b"\xff\xd9")
                    if eof_idx != -1 and (len(f_bytes) - (eof_idx + 2)) > 10:
                        if "Steganografi_Advarsel" not in res["meta"]:
                            res["meta"]["Steganografi_Advarsel"] = f"Fundet {len(f_bytes) - (eof_idx + 2)} skjulte bytes bag EOF!"

                # AI & Deepfake Heuristics
                ai_signatures = ["midjourney", "dall-e", "stable diffusion", "ai generated", "comfyui"]
                res["meta"].update(self._extract_exif(f_path))
                for k, v in res["meta"].items():
                    if any(sig in str(v).lower() for sig in ai_signatures):
                        res["meta"]["AI_Deepfake_Mistanke"] = True
                        
                if self._detect_faces(f_path):
                    res["face_detected"] = True

                # Udtrækker dHash for billedet
                dhash_val = self._calculate_dhash(f_path)
                if dhash_val:
                    res["meta"]["Visuel_Hash_dHash"] = dhash_val

                if HAS_OCR: res["text"] = self._ocr_pro(f_path)
                
            elif "pdf" in res["mime"] and HAS_PDF:
                try:
                    doc = fitz.open(f_path)
                    res["meta"].update(doc.metadata)
                    text_parts = []
                    for page in doc:
                        text_parts.append(page.get_text())
                        if HAS_OCR:
                            for img_idx, img in enumerate(page.get_images(full=True)):
                                try:
                                    base_image = doc.extract_image(img[0])
                                    tmp_img = f"/tmp/pdf_tmp_{time.time()}_{img[0]}.png"
                                    with open(tmp_img, "wb") as f: f.write(base_image["image"])
                                    text_parts.append(self._ocr_pro(tmp_img))
                                    os.remove(tmp_img)
                                except Exception: pass
                    res["text"] = "\n".join(text_parts)
                    doc.close()
                except Exception: pass
            
            elif f_path.lower().endswith(('.docx', '.xlsx', '.pptx')):
                res["meta"].update(self._extract_office_metadata(f_path))
                
            elif "video" in res["mime"] or f_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                res["meta"].update(self._extract_video_metadata(f_path))
                
            elif any(x in res["mime"] for x in ["text", "json", "csv", "plain", "log"]):
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f: res["text"] = f.read()

            if res["text"]:
                res["entities"] = self._scrub_all(res["text"])
                res["secrets"] = self._find_secrets(res["text"])
                
                if len(res["text"]) > 50 and TitanAIEnrichment:
                    try:
                        ai = TitanAIEnrichment()
                        ai_data = ai.analyze_text(res["text"])
                        if ai_data:
                            res["ai_context"] = ai_data
                    except Exception: pass
        except Exception: pass
        return res

    def _ocr_pro(self, path):
        try:
            img = cv2.imread(path)
            if img is None: return ""
            
            height, width = img.shape[:2]
            max_dimension = 2500
            if width > max_dimension or height > max_dimension:
                scaling_factor = max_dimension / float(max(width, height))
                img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            text = pytesseract.image_to_string(thresh, config='--psm 3 --oem 3')
            
            if "<" in text or "PASSPORT" in text.upper() or "ID" in text.upper() or "CARD" in text.upper():
                text += "\n" + pytesseract.image_to_string(thresh, config='--psm 11')
            return text
        except Exception: return ""

    def _scrub_all(self, text):
        e = {"emails": [], "bank": [], "cpr": [], "mrz": [], "crypto": [], "telefoner": [], "ips": [], "iban": []}
        for mail in REGEX_EMAIL.findall(text): e["emails"].append({"val": self._sanitize_email(mail.lower()), "score": 100})
        e["bank"] = self.REGEX_BANK.findall(text)
        e["cpr"] = self.REGEX_CPR.findall(text)
        
        for ip in re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text): e["ips"].append(ip)
        for ph in re.findall(r'\b(?:\+45|0045|45)?\s*([2-9]\d{1}\s?\d{2}\s?\d{2}\s?\d{2})\b', text):
            clean_ph = ph.replace(" ", "")
            if len(clean_ph) == 8: e["telefoner"].append(clean_ph)
            
        for iban in re.findall(r'\b[a-zA-Z]{2}[0-9]{2}\s?[a-zA-Z0-9]{4}\s?[0-9]{4}\s?[0-9]{3}\s?[a-zA-Z0-9]{3}\b', text):
            e["iban"].append(iban.replace(" ", ""))

        for m in self.REGEX_BTC.findall(text): e["crypto"].append({"type": "Bitcoin_Addr", "val": m})
        for m in self.REGEX_ETH.findall(text): e["crypto"].append({"type": "Ethereum_Addr", "val": m})
        return e

    def _sanitize_email(self, email):
        replacements = {
            ".cona": ".com", ".con": ".com", "hotmell": "hotmail",
            "hotmall": "hotmail", "gmaill": "gmail", "gmall": "gmail",
            "outloook": "outlook", "live.dkk": "live.dk"
        }
        for fault, fix in replacements.items():
            email = email.replace(fault, fix)
        return email

    def _find_secrets(self, text):
        secrets = []
        mnemonic = re.findall(r'\b(?:[a-z]{3,12}\s){11,23}[a-z]{3,12}\b', text.lower())
        if mnemonic: secrets.append({"type": "Crypto_Mnemonic", "val": mnemonic})
        keys = re.findall(r'\b(?:AIza[0-9A-Za-z-_]{35}|[0-9a-f]{64})\b', text)
        if keys: secrets.append({"type": "API_Key_or_Hash", "val": keys})
        return secrets

    def _auto_pivot_engine(self, driver):
        intel = self.master_data["Case_Intelligence"]
        print(f"\n{C.CYAN}{'='*60}\nBERIGELSE: GOLIATH TITAN ORCHESTRATOR\n{'='*60}{C.RESET}")
        
        # PIVOT PÅ EMAILS
        if intel["Digital_Footprint"]["Emails"] and BreachIntelligenceAnalyst:
            emails = [e for e, data in sorted(intel["Digital_Footprint"]["Emails"].items(), key=lambda x: x[1]['score'], reverse=True)[:5]]
            for email in emails:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] {C.YELLOW}[*] Deep-Scan via Modul 03 (Breach): {email}...{C.RESET}")
                try: 
                    mod = BreachIntelligenceAnalyst(email); mod.save = lambda: None
                    mod.run(driver)
                    if mod.data["Data_Leaks"] or mod.data["Paste_Sites"]:
                        self.master_data["Berigelse_Resultater"]["Breach_Reports"].append(mod.data)
                except Exception: pass
                time.sleep(2)

        # PIVOT PÅ ANSIGTER (REVERSE IMAGE SEARCH)
        if self.master_data["Meta"]["Images_For_RevSearch"] and driver:
            print(f"\n{C.YELLOW}[*] Reverse Image Search: Fandt {len(self.master_data['Meta']['Images_For_RevSearch'])} billeder med ansigter!{C.RESET}")
            for img_path in self.master_data["Meta"]["Images_For_RevSearch"][:3]: # Max 3 for at undgå Yandex bans
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {C.CYAN}[*] Udfører Reverse Image Pivot på: {os.path.basename(img_path)}...{C.RESET}")
                self.master_data["Reverse_Image_Hits"][img_path] = {}
                self._yandex_auto_upload(driver, img_path)
                self._tineye_auto_upload(driver, img_path)
                self._google_lens_auto_upload(driver, img_path)

    # --- REVERSE IMAGE SEARCH METHODS ---
    def _yandex_auto_upload(self, driver, img_path):
        try:
            driver.switch_to.window(driver.window_handles[0])
            driver.get("https://yandex.com/images/")
            try:
                cam_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Image search'], button[title='Image search']")))
                cam_btn.click()
            except: driver.get("https://yandex.com/images/search?rpt=imageview")
            
            time.sleep(1.5)
            file_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            file_input.send_keys(os.path.abspath(img_path))
            WebDriverWait(driver, 25).until(lambda d: "rpt=imageview" not in d.current_url or len(d.find_elements(By.CSS_SELECTOR, ".CbirItem")) > 0)
            self.master_data["Reverse_Image_Hits"][img_path]["Yandex"] = driver.current_url
            print(f"{C.GREEN}      ✓ Yandex Face-Match URL sikret.{C.RESET}")
        except Exception: pass

    def _tineye_auto_upload(self, driver, img_path):
        try:
            driver.execute_script("window.open('https://tineye.com/', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            file_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'], input#upload_box")))
            file_input.send_keys(os.path.abspath(img_path))
            WebDriverWait(driver, 20).until(lambda d: "result" in d.current_url.lower() or "search" in d.current_url.lower())
            self.master_data["Reverse_Image_Hits"][img_path]["TinEye"] = driver.current_url
            print(f"{C.GREEN}      ✓ TinEye Kilde-Match URL sikret.{C.RESET}")
        except Exception: pass

    def _google_lens_auto_upload(self, driver, img_path):
        try:
            driver.execute_script("window.open('https://images.google.com/', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            try:
                lens_btn = driver.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label*='Søg på billede'], div[role='button'][aria-label*='Search by image']")
                driver.execute_script("arguments[0].click();", lens_btn)
            except: pass
            file_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            file_input.send_keys(os.path.abspath(img_path))
            WebDriverWait(driver, 20).until(lambda d: "lens" in d.current_url.lower() or "search" in d.current_url.lower())
            self.master_data["Reverse_Image_Hits"][img_path]["GoogleLens"] = driver.current_url
            print(f"{C.GREEN}      ✓ Google Lens Objekt-Match URL sikret.{C.RESET}")
        except Exception: pass

    def _ingest_results(self, res):
        intel = self.master_data["Case_Intelligence"]
        
        if "MD5" in res.get("meta", {}):
            hash_data = {"MD5": res["meta"]["MD5"], "SHA256": res["meta"]["SHA256"]}
            if "Visuel_Hash_dHash" in res["meta"]:
                hash_data["Visuel_Hash_dHash"] = res["meta"]["Visuel_Hash_dHash"]
            self.master_data["Forensic_Hashes"][res["file"]] = hash_data
            
            if "Steganografi_Advarsel" in res["meta"]:
                self.master_data["File_Integrity_Alerts"].append({"File": res["file"], "Alert": res["meta"]["Steganografi_Advarsel"]})
            if "Malware_Signaturer" in res["meta"]:
                self.master_data["File_Integrity_Alerts"].append({"File": res["file"], "Alert": f"Malware Signatur: {res['meta']['Malware_Signaturer']}"})
            if res.get("meta", {}).get("AI_Deepfake_Mistanke"):
                self.master_data["AI_Deepfake_Mistanke"].append(res["file"])
                
        if res.get("face_detected"):
            self.master_data["Meta"]["Images_For_RevSearch"].append(res["path"])
                
            if "Document_Author" in res["meta"]:
                intel["Verified_Identities"][res["file"]] = res["meta"]["Document_Author"]
        
        for e in res["entities"].get("emails", []):
            email = e["val"]
            if email not in intel["Digital_Footprint"]["Emails"]:
                intel["Digital_Footprint"]["Emails"][email] = {"score": 0, "sources": set()}
            intel["Digital_Footprint"]["Emails"][email]["score"] += e["score"]
            intel["Digital_Footprint"]["Emails"][email]["sources"].add(res["file"])

        for bank in res["entities"].get("bank", []):
            if isinstance(bank, tuple): bank = f"{bank[0]} {bank[1]}"
            intel["Financial_Leads"]["Bankkonti"].add(bank)

        for cpr in res["entities"].get("cpr", []):
            intel["ID_Documents"]["CPR_Numre"].add(cpr)
            
        for crypt in res["entities"].get("crypto", []):
            intel["Financial_Leads"]["Crypto_Seeds"].append(crypt)
            
        for sec in res.get("secrets", []):
            intel["Financial_Leads"]["Keys_Secrets"].append(sec)

        for ip in res["entities"].get("ips", []):
            intel["Digital_Footprint"]["IP_Adresser"].add(ip)
        for ph in res["entities"].get("telefoner", []):
            intel["Digital_Footprint"]["Telefonnumre"].add(ph)
        for iban in res["entities"].get("iban", []):
            intel["Financial_Leads"]["IBAN_Konti"].add(iban)

        if res.get("meta") and "Make" in res["meta"]:
            device = f"{res['meta'].get('Make', 'Unknown')} {res['meta'].get('Model', '')}".strip()
            if "Devices" not in intel: intel["Devices"] = {}
            intel["Devices"][device] = intel["Devices"].get(device, 0) + 1
            
        if res.get("meta") and "GPS_Link" in res["meta"]:
            intel["Physical_Leads"]["GPS_Data"].append({"File": res["file"], "Link": res["meta"]["GPS_Link"]})

    def _extract_exif(self, path):
        meta = {}
        try:
            with Image.open(path) as img:
                info = img._getexif()
                if info:
                    for tag, value in info.items():
                        decoded = TAGS.get(tag, tag)
                        if decoded == 'GPSInfo':
                            gps_link = self._get_gps_link(value)
                            if gps_link: meta['GPS_Link'] = gps_link
                        elif decoded in ['DateTime', 'Make', 'Model']: 
                            meta[decoded] = str(value)
        except Exception: pass
        except (UnidentifiedImageError, OSError):
            pass
        return meta

    def _get_gps_link(self, gps_info):
        try:
            if gps_info and 2 in gps_info and 4 in gps_info:
                lat = self._convert_to_degrees(gps_info[2])
                lon = self._convert_to_degrees(gps_info[4])
                
                lat_ref = gps_info.get(1, 'N')
                lon_ref = gps_info.get(3, 'E')
                
                if isinstance(lat_ref, bytes): lat_ref = lat_ref.decode('utf-8')
                if isinstance(lon_ref, bytes): lon_ref = lon_ref.decode('utf-8')
                
                if lat and lon:
                    lat = lat * (-1 if lat_ref == 'S' else 1)
                    lon = lon * (-1 if lon_ref == 'W' else 1)
                    return f"https://www.google.com/maps?q={lat},{lon}"
        except Exception: return None
        return None

    def _print_progress(self, current, total):
        import sys
        pct = int((current / total) * 100)
        bar = "█" * (pct // 2) + "-" * (50 - (pct // 2))
        sys.stdout.write(f"\r{C.YELLOW}[*] TITAN-SCAN: |{bar}| {pct}% ({current}/{total}){C.RESET}")
        sys.stdout.flush()

    def _save_master_file(self, target=""):
        def convert_sets(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: convert_sets(v) for k, v in obj.items()}
            if isinstance(obj, list): return [convert_sets(i) for i in obj]
            return obj

        self.master_data["Case_Intelligence"] = convert_sets(self.master_data["Case_Intelligence"])
        
        mappe_navn = os.path.basename(os.path.normpath(self.folder_path))
        path = f"{session.get('loot_folder', 'loot')}/16_TITAN_REPORT_{mappe_navn}_{datetime.now().strftime('%H%M%S')}.json"
        
        try:
            if os.path.exists(path): os.remove(path)
            Path(path).write_text(json.dumps(self.master_data, indent=4, ensure_ascii=False), encoding="utf-8")
            print(f"\n{C.GREEN}[✓✓✓] TITAN MISSION FULDFØRT! FIL GEMT: {path}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Fejl under gemning: {e}{C.RESET}")

        datalake.ingest(self.name, target or "TITAN_SCAN", self.master_data)

    def _unpack_archives(self):
        for zf in glob.glob(f"{self.folder_path}/**/*.zip", recursive=True):
            extract_dir = os.path.join(self.folder_path, f"_extracted_{os.path.basename(zf)[:-4]}")
            if not os.path.exists(extract_dir):
                try:
                    with zipfile.ZipFile(zf, 'r') as zip_ref: zip_ref.extractall(extract_dir)
                except Exception: pass
                
        for tf in glob.glob(f"{self.folder_path}/**/*.tar*", recursive=True):
            extract_dir = os.path.join(self.folder_path, f"_extracted_{os.path.basename(tf).split('.')[0]}")
            if not os.path.exists(extract_dir):
                try:
                    with tarfile.open(tf, 'r:*') as tar_ref: tar_ref.extractall(extract_dir)
                except Exception: pass

# --- BACKWARDS COMPATIBILITY ALIASES ---
DigitalForensicsExaminer = AutoForensicMassScanner
ReverseImageIntelligence = AutoForensicMassScanner