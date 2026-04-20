# -*- coding: utf-8 -*-
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from PIL import Image
import piexif
from PIL.ExifTags import TAGS
from core.utils import C, session

class DigitalForensicsExaminer:
    """Advanced file forensics with metadata extraction"""
    def __init__(self, file_path):
        self.file_path = file_path.strip()
        self.data = {
            "Fil": os.path.basename(file_path),
            "Sti": file_path,
            "Filstørrelse": 0,
            "Filtype": "",
            "Kryptografi": {},
            "GPS_Koordinater": None,
            "GPS_Maps_Link": "",
            "Temporal_Data": {"Oprettet": None, "Ændret": None, "Manipuleret": False},
            "Enheds_Info": {},
            "EXIF_Data": {},
            "Integritetstjek": {"Bevis": "", "Modsigende_Felter": []},
            "Timestamp": datetime.now().isoformat()
        }
    
    def run(self):
        print(f"\n{C.CYAN}{'='*60}\n[11] Digital Forensik & Bevis-sikring\n{'='*60}{C.RESET}")
        print(f"Analyserer: {os.path.basename(self.file_path)}\n")
        
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Fejl: Filen findes ikke på stien.{C.RESET}")
            return
        
        self._extract_basic_info()
        if self.data["Filtype"].lower() in ['jpg', 'jpeg', 'png', 'tiff']:
            self._extract_exif_data()
            self._extract_gps_data()
        self._temporal_analysis()
        self._device_profiling()
        self._integrity_check()
        self.save()
    
    def _extract_basic_info(self):
        print(f"{C.YELLOW}[*] Beregner kryptografiske fingeraftryk for Chain of Custody...{C.RESET}")
        try:
            stat_info = os.stat(self.file_path)
            self.data["Filstørrelse"] = stat_info.st_size
            self.data["Filtype"] = os.path.splitext(self.file_path)[1][1:].upper()
            
            with open(self.file_path, "rb") as f:
                file_bytes = f.read()
                self.data["Kryptografi"] = {
                    "MD5": hashlib.md5(file_bytes).hexdigest(),
                    "SHA-1": hashlib.sha1(file_bytes).hexdigest(),
                    "SHA-256": hashlib.sha256(file_bytes).hexdigest()
                }
            
            print(f"    -> Filtype: {self.data['Filtype']}")
            print(f"    -> Størrelse: {self.data['Filstørrelse']} bytes")
            print(f"    -> SHA-256: {self.data['Kryptografi']['SHA-256']}")
        except Exception as e:
            print(f"{C.RED}[!] Fejl ved grund-analyse: {e}{C.RESET}")
    
    def _extract_exif_data(self):
        print(f"\n{C.YELLOW}[*] Deep-scan for skjult EXIF metadata...{C.RESET}")
        try:
            exif_dict = piexif.load(self.file_path)
            for ifd_name in ("0th", "Exif", "GPS", "1st"):
                ifd = exif_dict.get(ifd_name)
                if not ifd: continue
                for tag in ifd:
                    try:
                        tag_name = piexif.TAGS[ifd_name][tag]["name"]
                        tag_value = ifd[tag]
                        # Sikker dekodning af binære EXIF data
                        if isinstance(tag_value, bytes):
                            tag_value = tag_value.decode('utf-8', errors='ignore')
                        self.data["EXIF_Data"][tag_name] = str(tag_value)[:500]
                    except Exception: pass
            print(f"{C.GREEN}    ✓ Udtræk komplet. Fandt {len(self.data['EXIF_Data'])} EXIF felter.{C.RESET}")
        except piexif.InvalidImageDataError:
            print(f"{C.DIM}    [-] Billedet indeholder ingen eller korrupt EXIF-data (Muligvis renset/Social Media).{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [-] EXIF scan fejl: {e}{C.RESET}")
    
    def _extract_gps_data(self):
        try:
            img = Image.open(self.file_path)
            exif_data = img._getexif()
            if not exif_data: return
            
            gps_ifd = exif_data.get(34853) # GPS Info Tag
            if not gps_ifd: return
            
            lat = self._convert_to_degrees(gps_ifd.get(2))
            lon = self._convert_to_degrees(gps_ifd.get(4))
            lat_ref = gps_ifd.get(1, b'N').decode('utf-8', errors='ignore') if isinstance(gps_ifd.get(1), bytes) else gps_ifd.get(1, 'N')
            lon_ref = gps_ifd.get(3, b'E').decode('utf-8', errors='ignore') if isinstance(gps_ifd.get(3), bytes) else gps_ifd.get(3, 'E')
            
            if lat and lon:
                if lat_ref == 'S': lat = -lat
                if lon_ref == 'W': lon = -lon
                
                self.data["GPS_Koordinater"] = {"Breddegrad": lat, "Længdegrad": lon}
                self.data["GPS_Maps_Link"] = f"https://www.google.com/maps?q={lat},{lon}"
                print(f"{C.RED}    📍 BINGO! GPS Lokation Fundet: {lat:.6f}, {lon:.6f}{C.RESET}")
        except Exception: pass
    
    def _convert_to_degrees(self, value):
        try:
            d, m, s = value
            return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
        except Exception: return None
    
    def _temporal_analysis(self):
        print(f"\n{C.YELLOW}[*] Udfører Temporal Analyse (Timestamps)...{C.RESET}")
        try:
            stat_info = os.stat(self.file_path)
            created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            self.data["Temporal_Data"]["Oprettet"] = created
            self.data["Temporal_Data"]["Ændret"] = modified
            
            print(f"    -> Oprettet: {created.replace('T', ' ')}")
            print(f"    -> Senest ændret: {modified.replace('T', ' ')}")
        except Exception: pass
    
    def _device_profiling(self):
        try:
            img = Image.open(self.file_path)
            exif_data = img._getexif()
            if not exif_data: return
            
            important_tags = {271: "Fabrikant", 272: "Kameramodel", 305: "Software"}
            found = False
            for tag_id, tag_name in important_tags.items():
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    if isinstance(value, bytes): value = value.decode('utf-8', errors='ignore')
                    self.data["Enheds_Info"][tag_name] = str(value)
                    if not found: 
                        print(f"\n{C.YELLOW}[*] Analyserer optage-udstyr...{C.RESET}")
                        found = True
                    print(f"    -> {tag_name}: {value}")
        except Exception: pass
    
    def _integrity_check(self):
        print(f"\n{C.YELLOW}[*] Kører File Integrity Check...{C.RESET}")
        modsigende = []
        
        t_data = self.data["Temporal_Data"]
        if t_data["Oprettet"] and t_data["Ændret"]:
            if t_data["Oprettet"] != t_data["Ændret"]:
                modsigende.append("OS Timestamps stemmer ikke overens (Mulig manipulation/kopiering)")
                t_data["Manipuleret"] = True
        
        # Sammenlign OS oprettelse med EXIF oprettelse
        if "DateTimeOriginal" in self.data["EXIF_Data"] and t_data["Oprettet"]:
            exif_time = self.data["EXIF_Data"]["DateTimeOriginal"].replace(":", "-", 2)
            if exif_time[:10] not in t_data["Oprettet"]:
                modsigende.append("EXIF dato matcher ikke Fil-systemets oprettelsesdato")
        
        self.data["Integritetstjek"]["Modsigende_Felter"] = modsigende
        
        if modsigende:
            print(f"{C.RED}    [!] ADVARSEL: Unormaliteter detekteret i metadata!{C.RESET}")
            for m in modsigende: print(f"      -> {m}")
            self.data["Integritetstjek"]["Bevis"] = "CRITICAL"
        else:
            print(f"{C.GREEN}    ✓ Filen fremstår intakt uden åbenlyse tids-uoverensstemmelser.{C.RESET}")
            self.data["Integritetstjek"]["Bevis"] = "OK"
    
    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/11_FORENSIK_{os.path.basename(self.file_path).replace('.', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding='utf-8')
        print(f"\n{C.GREEN}[✓] Forensisk rapport gemt: {filename}{C.RESET}")