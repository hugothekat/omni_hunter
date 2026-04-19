import os
import glob
import time
import json
import re
import zipfile
import concurrent.futures
from pathlib import Path
from datetime import datetime

import magic
import cv2
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
from PIL.ExifTags import TAGS

from core.utils import C, session, REGEX_EMAIL, REGEX_BANK, REGEX_CPR, REGEX_BTC, REGEX_ETH
from modules.mod_27_ai import TitanAIEnrichment
from modules.mod_03_breach import BreachIntelligenceAnalyst

class AutoForensicMassScanner:
    """TITAN Orchestrator: Den mest komplette kombination af OSINT og digital forensik."""
    def _convert_to_degrees(self, value):
        """Hjælpefunktion til at konvertere EXIF GPS til decimaler."""
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    
    def __init__(self, folder_path):
        self.folder_path = folder_path.strip()
        self.start_time = time.time()
        
        self.master_data = {
            "Meta": {"Sagsmappe": self.folder_path, "Timestamp": datetime.now().isoformat(), "Filer_Behandlet": 0},
            "Case_Intelligence": {
                "Verified_Identities": {}, # Navne med confidence score og kilde
                "Digital_Footprint": {"Emails": {}, "Social_Handles": set(), "IP_Adresser": set()},
                "Financial_Leads": {"Bankkonti": set(), "Crypto_Seeds": [], "Keys_Secrets": [], "CVR": set()},
                "Physical_Leads": {"Adresser": set(), "Nummerplader": set(), "GPS_Data": []},
                "ID_Documents": {"MRZ_Koder": [], "CPR_Numre": set(), "Pasnumre": set()},
                "Timeline": {"Datoer_Fundet": set()}
            },
            "Metadata_Report": {}, # EXIF data (GPS/Tid)
            "Source_Map": {},      # Relation mellem data og filnavn
            "File_Integrity_Alerts": [], # Magic byte mismatches
            "Berigelse_Resultater": {"Phone_Data": [], "Breach_Reports": []},
            "Raw_Text_Archive": {} # ALT tekst gemmes ordret her
        }
        self.noise_list = ["Matas", "Apple", "Google", "Lunar", "Faktura", "Store", "Support", "Maria Casino", "Gældsstyrelsen", "Danske Spil", "Danske Inkasso"]

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[16] GOLIATH TITAN: FULL SPECTRUM FORENSICS\n{'='*60}{C.RESET}")
        if not os.path.exists(self.folder_path): 
            print(f"{C.RED}[!] Fejl: Stien findes ikke.{C.RESET}"); return
        
        # 1. DEEP UNPACKING
        self._unpack_archives()

        # 2. PARALLEL TITAN ENGINE (8 tråde for max speed)
        files = [f for f in glob.glob(f"{self.folder_path}/**/*", recursive=True) if os.path.isfile(f)]
        self.master_data["Meta"]["Filer_Behandlet"] = len(files)

        print(f"[*] Starter synkroniseret analyse af {len(files)} enheder via 8 CPU-processer...")
        completed = 0
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._titan_process_file, f): f for f in files}
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                self._print_progress(completed, len(files))
                try:
                    res = future.result()
                    if res: self._ingest_results(res)
                except Exception as e:
                    print(f"\n{C.RED} [!] TITAN Crash i fil: {e}{C.RESET}")
        
        print(f"\n{C.GREEN}[✓] Forensic Pipeline komplet. Starter automatisk berigelse...{C.RESET}")
        self._auto_pivot_engine(driver)
        self._save_master_file()
        # Terminal Summary for analytikeren
        print(f"\n{C.CYAN}--- TITAN MISSION SUMMARY ---{C.RESET}")
        print(f"Emails fundet: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['Emails'])}")
        print(f"Bankkonti fundet: {len(self.master_data['Case_Intelligence']['Financial_Leads']['Bankkonti'])}")
        print(f"CPR numre fundet: {len(self.master_data['Case_Intelligence']['ID_Documents']['CPR_Numre'])}")
        
        if "Devices" in self.master_data["Case_Intelligence"]:
            print(f"Identificerede Enheder: {', '.join(self.master_data['Case_Intelligence']['Devices'].keys())}")
        print(f"{C.CYAN}----------------------------{C.RESET}")

    def _titan_process_file(self, f_path):
        fname = os.path.basename(f_path)
        res = {"file": fname, "path": f_path, "text": "", "meta": {}, "mime": "unknown", "entities": {}}
        
        # Da _unpack_archives() allerede HAR pakket indholdet ud,
        # ignorerer vi bare selve .zip filen for at spare massiv CPU-tid!
        if f_path.lower().endswith('.zip'):
            return res

        try:
            res["mime"] = magic.from_file(f_path, mime=True)

            if "image" in res["mime"]:
                # ... resten af din kode forsætter herfra ...
                res["meta"] = self._extract_exif(f_path)
                if HAS_OCR: res["text"] = self._ocr_pro(f_path)
                
            elif "pdf" in res["mime"] and HAS_PDF:
                doc = fitz.open(f_path)
                text_parts = []
                for page in doc:
                    # Hent den indlejrede tekst
                    text_parts.append(page.get_text())
                    
                    # NYT: Træk skjulte billeder/scanninger ud og OCR dem!
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
                
            elif any(x in res["mime"] for x in ["text", "json", "csv", "plain"]):
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f: res["text"] = f.read()

            if res["text"]:
                res["entities"] = self._scrub_all(res["text"])
                res["secrets"] = self._find_secrets(res["text"])
                
                # --- NYT: AI Berigelse af dokumentet ---
                if len(res["text"]) > 50:
                    ai = TitanAIEnrichment()
                    ai_data = ai.analyze_text(res["text"])
                    if ai_data:
                        res["ai_context"] = ai_data
                        print(f"\n{C.GREEN}    🧠 AI Fandt Kontekst i {fname}: {ai_data.get('navne', [])}{C.RESET}")
        except Exception: pass
        return res

    def _ocr_pro(self, path):
        """OpenCV Pre-processing med MAX opløsning for memory-sikkerhed."""
        try:
            img = cv2.imread(path)
            if img is None: return ""
            
            # OPTIMERING: Tving max bredde på 2500px, bevar aspect ratio
            height, width = img.shape[:2]
            max_dimension = 2500
            if width > max_dimension or height > max_dimension:
                scaling_factor = max_dimension / float(max(width, height))
                img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            text = pytesseract.image_to_string(thresh, config='--psm 3 --oem 3')
            
            if "<" in text or "PAS" in text.upper() or "DANMARK" in text.upper():
                text += "\n" + pytesseract.image_to_string(thresh, config='--psm 11')
            return text
        except Exception as e: return ""

    def _scrub_all(self, text):
        e = {"emails": [], "bank": [], "cpr": [], "mrz": [], "secrets": [], "crypto": []}
        
        for mail in REGEX_EMAIL.findall(text):
            e["emails"].append({"val": mail.lower(), "score": 100})
            
        e["bank"] = REGEX_BANK.findall(text)
        e["cpr"] = REGEX_CPR.findall(text)
        
        for m in REGEX_BTC.findall(text): e["crypto"].append({"type": "Bitcoin_Addr", "val": m})
        for m in REGEX_ETH.findall(text): e["crypto"].append({"type": "Ethereum_Addr", "val": m})
        
        # ... fortsæt logik
        return e

    def _sanitize_email(self, email):
        """Retter gængse OCR-fejl i domænenavne for at undgå 'hotmail.cona'."""
        replacements = {
            ".cona": ".com", ".con": ".com", "hotmell": "hotmail",
            "hotmall": "hotmail", "gmaill": "gmail", "gmall": "gmail",
            "outloook": "outlook", "live.dkk": "live.dk"
        }
        for fault, fix in replacements.items():
            email = email.replace(fault, fix)
        return email

    def _find_secrets(self, text):
        """Leder efter Crypto Seeds og Keys (GitHub Intelligence)."""
        secrets = []
        mnemonic = re.findall(r'\b(?:[a-z]{3,12}\s){11,23}[a-z]{3,12}\b', text.lower())
        if mnemonic: secrets.append({"type": "Crypto_Mnemonic", "val": mnemonic})
        keys = re.findall(r'\b(?:AIza[0-9A-Za-z-_]{35}|[0-9a-f]{64})\b', text)
        if keys: secrets.append({"type": "API_Key_or_Hash", "val": keys})
        return secrets

    def _auto_pivot_engine(self, driver):
        """Intelligent Orchestrator: Beriger automatisk de fundne spor."""
        intel = self.master_data["Case_Intelligence"]
        print(f"\n{C.CYAN}{'='*60}\nBERIGELSE: GOLIATH TITAN ORCHESTRATOR\n{'='*60}{C.RESET}")

        emails = [e for e, data in sorted(intel["Digital_Footprint"]["Emails"].items(), key=lambda x: x[1]['score'], reverse=True)[:5]]
        for email in emails:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] {C.YELLOW}[*] Deep-Scan: Email {email}...{C.RESET}")
            mod = BreachIntelligenceAnalyst(email); mod.save = lambda: None
            try: 
                mod.run(driver)
                self.master_data["Berigelse_Resultater"]["Breach_Reports"].append(mod.data)
            except Exception: pass
            time.sleep(random.uniform(3, 6))

    def _ingest_results(self, res):
        intel = self.master_data["Case_Intelligence"]
        # Din eksisterende ingest logik her...
        
        # NYT: Saml statistik over enheder (iPhone, Samsung, etc.)
        if res.get("meta") and "Make" in res["meta"]:
            device = f"{res['meta'].get('Make')} {res['meta'].get('Model')}"
            if "Devices" not in intel: 
                intel["Devices"] = {}
            # Tæller hvor mange gange hver enhed optræder
            intel["Devices"][device] = intel["Devices"].get(device, 0) + 1

    def _extract_exif(self, path):
        meta = {}
        try:
            with Image.open(path) as img:
                info = img._getexif()
                if info:
                    for tag, value in info.items():
                        decoded = TAGS.get(tag, tag)
                        
                        # --- NY GPS LOGIK ---
                        if decoded == 'GPSInfo':
                            gps_link = self._get_gps_link(value)
                            if gps_link:
                                meta['GPS_Link'] = gps_link
                                print(f"{C.YELLOW}    📍 GPS FUNDET: {gps_link}{C.RESET}")
                        elif decoded in ['DateTime', 'Make', 'Model']: 
                            meta[decoded] = str(value)
        except Exception as e: 
            print(f"{C.DIM}    [Debug] EXIF Fejl: {e}{C.RESET}")
        return meta

    def _print_progress(self, current, total):
        pct = int((current / total) * 100)
        bar = "█" * (pct // 2) + "-" * (50 - (pct // 2))
        print(f"\r{C.YELLOW}[*] TITAN-SCAN: |{bar}| {pct}% ({current}/{total}){C.RESET}", end="", flush=True)

    def _save_master_file(self):
        """Gemmer rapporten og sikrer at ALLE 'sets' konverteres til lister for at undgå crash."""
        def convert_sets(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: convert_sets(v) for k, v in obj.items()}
            if isinstance(obj, list): return [convert_sets(i) for i in obj]
            return obj

        self.master_data["Case_Intelligence"] = convert_sets(self.master_data["Case_Intelligence"])
        
        mappe_navn = os.path.basename(os.path.normpath(self.folder_path))
        path = f"{session['loot_folder']}/16_TITAN_REPORT_{mappe_navn}_{datetime.now().strftime('%H%M%S')}.json"
        
        try:
            Path(path).write_text(json.dumps(self.master_data, indent=4, ensure_ascii=False), encoding="utf-8")
            print(f"\n{C.GREEN}[✓✓✓] TITAN MISSION FULDFØRT! FIL GEMT: {path}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Fejl under gemning: {e}{C.RESET}")

    def _unpack_archives(self):
        for zf in glob.glob(f"{self.folder_path}/**/*.zip", recursive=True):
            extract_dir = os.path.join(self.folder_path, f"_extracted_{os.path.basename(zf)[:-4]}")
            if not os.path.exists(extract_dir):
                try:
                    with zipfile.ZipFile(zf, 'r') as zip_ref: zip_ref.extractall(extract_dir)
                except Exception: pass

    # Tilføj denne hjælpefunktion i bunden af TITAN klassen
    def _get_gps_link(self, gps_info):
        try:
            if gps_info:
                def to_dec(val): 
                    return float(val[0]) + float(val[1])/60 + float(val[2])/3600
                lat = to_dec(gps_info[2]) * (-1 if gps_info[1] == 'S' else 1)
                lon = to_dec(gps_info[4]) * (-1 if gps_info[3] == 'W' else 1)
                return f"https://www.google.com/maps?q={lat},{lon}"
        except Exception: return None
        return None