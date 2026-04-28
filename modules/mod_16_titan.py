# -*- coding: utf-8 -*-
import os
import glob
import time
import json
import re
import zipfile
import tarfile # NY V8: Tilføjet tar/gz support
import hashlib # NY V8: Til kryptografisk sikring
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

HAS_OCR = True
HAS_PDF = True

class AutoForensicMassScanner:
    """TITAN Orchestrator: Den mest komplette kombination af OSINT og digital forensik (GOLIATH V8)."""
    def _convert_to_degrees(self, value):
        try:
            d, m, s = float(value[0]), float(value[1]), float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except Exception: return None
    
    def __init__(self, folder_path):
        self.folder_path = folder_path.strip()
        self.start_time = time.time()
        
        self.master_data = {
            "Meta": {"Sagsmappe": self.folder_path, "Timestamp": datetime.now().isoformat(), "Filer_Behandlet": 0},
            "Case_Intelligence": {
                "Verified_Identities": {}, 
                "Digital_Footprint": {"Emails": {}, "Social_Handles": set(), "IP_Adresser": set(), "Telefonnumre": set()}, # NY V8: IPs og Telefoner
                "Financial_Leads": {"Bankkonti": set(), "IBAN_Konti": set(), "Crypto_Seeds": [], "Keys_Secrets": [], "CVR": set()}, # NY V8: IBAN
                "Physical_Leads": {"Adresser": set(), "Nummerplader": set(), "GPS_Data": []},
                "ID_Documents": {"MRZ_Koder": [], "CPR_Numre": set(), "Pasnumre": set()},
                "Timeline": {"Datoer_Fundet": set()}
            },
            "Metadata_Report": {}, 
            "Forensic_Hashes": {}, # NY V8: Chain of custody
            "Source_Map": {},      
            "File_Integrity_Alerts": [], 
            "Berigelse_Resultater": {"Phone_Data": [], "Breach_Reports": [], "IP_Reports": []}, # NY V8: IP Reports
            "Raw_Text_Archive": {} 
        }
        self.noise_list = ["Matas", "Apple", "Google", "Lunar", "Faktura", "Store", "Support", "Maria Casino", "Gældsstyrelsen", "Danske Spil", "Danske Inkasso"]

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[16] GOLIATH TITAN: FULL SPECTRUM FORENSICS V8\n{'='*60}{C.RESET}")
        if not os.path.exists(self.folder_path): 
            print(f"{C.RED}[!] Fejl: Stien {self.folder_path} findes ikke.{C.RESET}"); return
        
        print(f"{C.YELLOW}[*] Step 1: Deep Unpacking af arkiver (.zip, .tar, .gz)...{C.RESET}")
        self._unpack_archives()

        files = [f for f in glob.glob(f"{self.folder_path}/**/*", recursive=True) if os.path.isfile(f)]
        self.master_data["Meta"]["Filer_Behandlet"] = len(files)

        print(f"{C.YELLOW}[*] Step 2: Starter synkroniseret OCR/Tekst/Krypto-analyse af {len(files)} enheder (Max 8 tråde)...{C.RESET}")
        completed = 0
        
        # Vi tilføjer robusthed her: Hvis én proces fejler (Pga. en mystisk fil), fortsætter de 7 andre
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._titan_process_file, f): f for f in files}
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                self._print_progress(completed, len(files))
                try:
                    res = future.result()
                    if res: self._ingest_results(res)
                except Exception as e:
                    pass # Skjuler specifikke tråd-fejl for brugeren for at holde konsollen ren
        
        print(f"\n{C.GREEN}[✓] Forensic Pipeline komplet. Starter automatisk Omni-Berigelse...{C.RESET}")
        self._auto_pivot_engine(driver)
        self._save_master_file()
        
        print(f"\n{C.CYAN}--- TITAN MISSION SUMMARY ---{C.RESET}")
        print(f"Filer Hashet (Krypto): {len(self.master_data['Forensic_Hashes'])}")
        print(f"Emails fundet: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['Emails'])}")
        print(f"Telefonnumre: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['Telefonnumre'])}")
        print(f"IP-Adresser: {len(self.master_data['Case_Intelligence']['Digital_Footprint']['IP_Adresser'])}")
        print(f"Bankkonti/IBAN: {len(self.master_data['Case_Intelligence']['Financial_Leads']['Bankkonti']) + len(self.master_data['Case_Intelligence']['Financial_Leads']['IBAN_Konti'])}")
        print(f"CPR numre fundet: {len(self.master_data['Case_Intelligence']['ID_Documents']['CPR_Numre'])}")
        
        if self.master_data.get("File_Integrity_Alerts"):
            print(f"{C.RED}Steganografi/Integrity Alerts: {len(self.master_data['File_Integrity_Alerts'])} filer flaget!{C.RESET}")
        
        if "Devices" in self.master_data["Case_Intelligence"]:
            print(f"Identificerede Enheder: {', '.join(self.master_data['Case_Intelligence']['Devices'].keys())}")
        print(f"{C.CYAN}----------------------------{C.RESET}")

    def _titan_process_file(self, f_path):
        fname = os.path.basename(f_path)
        res = {"file": fname, "path": f_path, "text": "", "meta": {}, "mime": "unknown", "entities": {}}
        
        if f_path.lower().endswith('.zip') or f_path.lower().endswith('.tar.gz') or f_path.lower().endswith('.tar'):
            return res

        try:
            # --- NY V8: Hash filen for retsgyldighed ---
            with open(f_path, 'rb') as bin_f:
                f_bytes = bin_f.read()
                res["meta"]["MD5"] = hashlib.md5(f_bytes).hexdigest()
                res["meta"]["SHA256"] = hashlib.sha256(f_bytes).hexdigest()

            mime_type = magic.from_file(f_path, mime=True)
            res["mime"] = mime_type if mime_type else "unknown"

            if "image" in res["mime"]:
                # --- NY V8: Steganografi Check ---
                if res["mime"] in ["image/jpeg", "image/jpg"]:
                    eof_idx = f_bytes.rfind(b"\xff\xd9")
                    if eof_idx != -1 and eof_idx + 2 < len(f_bytes):
                        res["meta"]["Steganografi_Advarsel"] = f"Fundet {len(f_bytes) - (eof_idx + 2)} skjulte bytes!"

                res["meta"].update(self._extract_exif(f_path))
                if HAS_OCR: res["text"] = self._ocr_pro(f_path)
                
            elif "pdf" in res["mime"] and HAS_PDF:
                try:
                    doc = fitz.open(f_path)
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
                
            elif any(x in res["mime"] for x in ["text", "json", "csv", "plain"]):
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f: res["text"] = f.read()

            if res["text"]:
                res["entities"] = self._scrub_all(res["text"])
                res["secrets"] = self._find_secrets(res["text"])
                
                if len(res["text"]) > 50:
                    ai = TitanAIEnrichment()
                    ai_data = ai.analyze_text(res["text"])
                    if ai_data:
                        res["ai_context"] = ai_data
        except Exception: pass
        return res

    def _ocr_pro(self, path):
        """OpenCV Pre-processing med MAX opløsning for memory-sikkerhed."""
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
        
        for mail in REGEX_EMAIL.findall(text):
            clean_mail = self._sanitize_email(mail.lower())
            e["emails"].append({"val": clean_mail, "score": 100})
            
        e["bank"] = REGEX_BANK.findall(text)
        e["cpr"] = REGEX_CPR.findall(text)
        
        # --- NY V8 TILFØJELSE: IP, Tlf, IBAN ---
        for ip in re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text):
            e["ips"].append(ip)
            
        for ph in re.findall(r'\b(?:\+45|0045|45)?\s*([2-9]\d{1}\s?\d{2}\s?\d{2}\s?\d{2})\b', text):
            clean_ph = ph.replace(" ", "")
            if len(clean_ph) == 8: e["telefoner"].append(clean_ph)
            
        for iban in re.findall(r'\b[a-zA-Z]{2}[0-9]{2}\s?[a-zA-Z0-9]{4}\s?[0-9]{4}\s?[0-9]{3}\s?[a-zA-Z0-9]{3}\b', text):
            e["iban"].append(iban.replace(" ", ""))

        for m in REGEX_BTC.findall(text): e["crypto"].append({"type": "Bitcoin_Addr", "val": m})
        for m in REGEX_ETH.findall(text): e["crypto"].append({"type": "Ethereum_Addr", "val": m})
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
        
        # 1. PIVOT PÅ EMAILS
        if intel["Digital_Footprint"]["Emails"]:
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
                import random
                time.sleep(random.uniform(2, 4))
                
        # 2. PIVOT PÅ TELEFONNUMRE (NY V8)
        if intel["Digital_Footprint"].get("Telefonnumre"):
            phones = list(intel["Digital_Footprint"]["Telefonnumre"])[:3]
            for ph in phones:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] {C.YELLOW}[*] Deep-Scan via Modul 12 (RevPhone): {ph}...{C.RESET}")
                try:
                    from modules.mod_12_revphone import ReversePhoneIntelligence
                    mod_ph = ReversePhoneIntelligence(ph); mod_ph.save = lambda: None
                    mod_ph.run(driver)
                    self.master_data["Berigelse_Resultater"]["Phone_Data"].append(mod_ph.data)
                except ImportError:
                    print(f"{C.DIM}  [-] Modul 12 (RevPhone) ikke fundet.{C.RESET}")
                except Exception: pass
                time.sleep(1)

        # 3. PIVOT PÅ IP-ADRESSER (NY V8)
        if intel["Digital_Footprint"].get("IP_Adresser"):
            ips = [ip for ip in list(intel["Digital_Footprint"]["IP_Adresser"]) if not ip.startswith(("192.168", "10.", "127.", "172."))]
            for ip in ips[:3]:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] {C.YELLOW}[*] Deep-Scan via Modul 10 (IP Intel): {ip}...{C.RESET}")
                try:
                    from modules.mod_10_ip import IPNetworkAnalyzer
                    mod_ip = IPNetworkAnalyzer(ip); mod_ip.save = lambda: None
                    mod_ip.run(driver)
                    self.master_data["Berigelse_Resultater"]["IP_Reports"].append(mod_ip.data)
                except ImportError:
                    print(f"{C.DIM}  [-] Modul 10 (IP Intel) ikke fundet.{C.RESET}")
                except Exception: pass

    def _ingest_results(self, res):
        intel = self.master_data["Case_Intelligence"]
        
        # --- NY V8: Hash Register Ingestion ---
        if "MD5" in res.get("meta", {}):
            self.master_data["Forensic_Hashes"][res["file"]] = {
                "MD5": res["meta"]["MD5"], "SHA256": res["meta"]["SHA256"]
            }
            if "Steganografi_Advarsel" in res["meta"]:
                self.master_data["File_Integrity_Alerts"].append({"File": res["file"], "Alert": res["meta"]["Steganografi_Advarsel"]})
        
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

        # --- NY V8 Ingestion (Tlf, IP, IBAN) ---
        for ip in res["entities"].get("ips", []):
            intel["Digital_Footprint"]["IP_Adresser"].add(ip)
        for ph in res["entities"].get("telefoner", []):
            intel["Digital_Footprint"]["Telefonnumre"].add(ph)
        for iban in res["entities"].get("iban", []):
            intel["Financial_Leads"]["IBAN_Konti"].add(iban)

        if res.get("meta") and "Make" in res["meta"]:
            device = f"{res['meta'].get('Make', 'Unknown')} {res['meta'].get('Model', '')}".strip()
            if "Devices" not in intel: 
                intel["Devices"] = {}
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

    def _save_master_file(self):
        def convert_sets(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: convert_sets(v) for k, v in obj.items()}
            if isinstance(obj, list): return [convert_sets(i) for i in obj]
            return obj

        self.master_data["Case_Intelligence"] = convert_sets(self.master_data["Case_Intelligence"])
        
        mappe_navn = os.path.basename(os.path.normpath(self.folder_path))
        path = f"{session['loot_folder']}/16_TITAN_REPORT_{mappe_navn}_{datetime.now().strftime('%H%M%S')}.json"
        
        # NY V8: Sikker overskrivning
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
            
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
                
        # --- NY V8 TILFØJELSE: TAR og GZ udpakning ---
        for tf in glob.glob(f"{self.folder_path}/**/*.tar*", recursive=True):
            extract_dir = os.path.join(self.folder_path, f"_extracted_{os.path.basename(tf).split('.')[0]}")
            if not os.path.exists(extract_dir):
                try:
                    with tarfile.open(tf, 'r:*') as tar_ref: tar_ref.extractall(extract_dir)
                except Exception: pass