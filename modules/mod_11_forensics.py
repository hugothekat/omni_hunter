# -*- coding: utf-8 -*-
import os
import json
import hashlib
import re # NY V8 TILFØJELSE: Til string extraction
from pathlib import Path
from datetime import datetime
from PIL import Image
import piexif
from PIL.ExifTags import TAGS
from core.utils import C, session

class DigitalForensicsExaminer:
    """Advanced file forensics with metadata extraction"""
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {
            "Fil": os.path.basename(file_path),
            "Sti": file_path,
            "Filstørrelse": 0,
            "Filtype": "",
            "Kryptografi": {},            # Flyttet op for struktur
            "GPS_Koordinater": None,
            "GPS_Maps_Link": "",
            "Temporal_Data": {
                "Oprettet": None,
                "Ændret": None,
                "Manipuleret": False
            },
            "Enheds_Info": {},
            "EXIF_Data": {},
            "Steganografi_Analyse": {},   # NY V8 TILFØJELSE
            "Skjulte_Netværksspor": [],   # NY V8 TILFØJELSE: IP/Emails i RAW data
            "Integritetstjek": {
                "Bevis": "",
                "Modsigende_Felter": []
            },
            "Timestamp": datetime.now().isoformat()
        }
    
    def run(self, driver=None): # NY V8 TILFØJELSE: driver parameter for pivot kompatibilitet
        """Execute forensics analysis"""
        print(f"\n{C.CYAN}{'='*60}{C.RESET}")
        print(f"{C.CYAN}[11] Digital Forensics & Steganografi Analyse (GOLIATH V8){C.RESET}")
        print(f"{C.CYAN}{'='*60}{C.RESET}")
        print(f"File: {os.path.basename(self.file_path)}\n")
        
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] File not found{C.RESET}")
            return
        
        self._extract_basic_info()
        if self.data["Filtype"].lower() in ['jpg', 'jpeg', 'png', 'gif']:
            self._extract_exif_data()
            self._extract_gps_data()
        
        self._temporal_analysis()
        self._device_profiling()
        
        # --- NYE V8 ANALYSER ---
        self._steganography_check()
        self._extract_strings_and_intel()
        
        self._integrity_check()
        self.save()
    
    def _extract_basic_info(self):
        """Extract basic file information and Cryptographic Hashes"""
        try:
            stat_info = os.stat(self.file_path)
            self.data["Filstørrelse"] = stat_info.st_size
            self.data["Filtype"] = os.path.splitext(self.file_path)[1][1:].upper()
            
            # --- NYT: Kryptografisk Bevis-sikring (Chain of Custody) ---
            print(f"{C.YELLOW}[*] Beregner kryptografiske fingeraftryk...{C.RESET}")
            with open(self.file_path, "rb") as f:
                file_bytes = f.read()
                self.data["Kryptografi"] = {
                    "MD5": hashlib.md5(file_bytes).hexdigest(),
                    "SHA-1": hashlib.sha1(file_bytes).hexdigest(), # NY V8 TILFØJELSE
                    "SHA-256": hashlib.sha256(file_bytes).hexdigest()
                }
            
            print(f"{C.GREEN}[*] File Type: {self.data['Filtype']}{C.RESET}")
            print(f"{C.GREEN}[*] Size: {self.data['Filstørrelse']} bytes{C.RESET}")
            print(f"{C.GREEN}[*] SHA-256: {self.data['Kryptografi']['SHA-256'][:15]}...{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Error: {str(e)}{C.RESET}")
    
    def _extract_exif_data(self):
        """Extract EXIF metadata"""
        try:
            img = Image.open(self.file_path)
            exif_dict = piexif.load(self.file_path)
            for ifd_name in ("0th", "Exif", "GPS", "1st"):
                ifd = exif_dict[ifd_name]
                for tag in ifd:
                    tag_name = piexif.TAGS[ifd_name][tag]["name"]
                    tag_value = ifd[tag]
                    try:
                        if isinstance(tag_value, bytes):
                            tag_value = tag_value.decode('utf-8', errors='ignore')
                        self.data["EXIF_Data"][tag_name] = str(tag_value)[:500]
                    except Exception:
                        pass
            print(f"{C.GREEN}[*] EXIF Fields: {len(self.data['EXIF_Data'])}{C.RESET}")
        except Exception:
            print(f"{C.DIM}[*] No EXIF data{C.RESET}")
    
    def _extract_gps_data(self):
        """Extract GPS coordinates"""
        try:
            img = Image.open(self.file_path)
            exif_data = img._getexif()
            if exif_data is None:
                return
            
            gps_ifd = exif_data.get(34853)
            if gps_ifd is None:
                return
            
            lat = self._convert_to_degrees(gps_ifd[2])
            lon = self._convert_to_degrees(gps_ifd[4])
            lat_ref = gps_ifd[1].decode('utf-8', errors='ignore')
            lon_ref = gps_ifd[3].decode('utf-8', errors='ignore')
            
            if lat_ref == 'S':
                lat = -lat
            if lon_ref == 'W':
                lon = -lon
            
            self.data["GPS_Koordinater"] = {"Breddegrad": lat, "Længdegrad": lon}
            self.data["GPS_Maps_Link"] = f"https://www.google.com/maps?q={lat},{lon}" # Opdateret til direkte klikbart link
            
            print(f"{C.RED}[✓] GPS KOORDINATER FUNDET: {lat:.6f}, {lon:.6f}{C.RESET}")
            print(f"{C.CYAN}    -> MAPS: {self.data['GPS_Maps_Link']}{C.RESET}")
        except Exception:
            pass
    
    def _convert_to_degrees(self, value):
        """Convert GPS data to degrees"""
        try:
            d, m, s = value
            return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
        except Exception:
            return None
    
    def _temporal_analysis(self):
        """Analyze file timestamps"""
        try:
            stat_info = os.stat(self.file_path)
            created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            self.data["Temporal_Data"]["Oprettet"] = created
            self.data["Temporal_Data"]["Ændret"] = modified
            
            if created != modified:
                self.data["Temporal_Data"]["Manipuleret"] = True
                print(f"{C.RED}[!] MANIPULATION DETECTED (Oprettet og Ændret stemmer ikke overens){C.RESET}")
            
            print(f"{C.GREEN}[*] Created: {created}{C.RESET}")
            print(f"{C.GREEN}[*] Modified: {modified}{C.RESET}")
        except Exception:
            pass
    
    def _device_profiling(self):
        """Extract device information"""
        try:
            img = Image.open(self.file_path)
            exif_data = img._getexif()
            if exif_data is None:
                return
            
            important_tags = {271: "Fabrikant", 272: "Kameramodel", 305: "Software"}
            
            for tag_id, tag_name in important_tags.items():
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='ignore')
                    self.data["Enheds_Info"][tag_name] = str(value)
                    print(f"{C.MAGENTA}[*] ENHEDS INFO: {tag_name}: {value}{C.RESET}")
        except Exception:
            pass

    def _steganography_check(self):
        """NY V8 TILFØJELSE: Scanner filen for skjult data efter End-Of-File (EOF) markøren"""
        print(f"\n{C.YELLOW}[*] Udfører Steganografi-tjek (EOF Analyse)...{C.RESET}")
        try:
            with open(self.file_path, "rb") as f:
                content = f.read()
                
            # Tjekker specifikt for JPG filer
            if self.data["Filtype"].lower() in ["jpg", "jpeg"]:
                eof_marker = b"\xff\xd9"
                eof_index = content.rfind(eof_marker)
                
                if eof_index != -1 and eof_index + 2 < len(content):
                    hidden_bytes = len(content) - (eof_index + 2)
                    self.data["Steganografi_Analyse"] = {
                        "Status": "Mistænkelig",
                        "Skjulte_Bytes": hidden_bytes,
                        "Beskrivelse": "Data fundet efter officiel EOF markør"
                    }
                    print(f"{C.RED}    🔥 ADVARSEL: STEGANOGRAFI DETEKTERET! Fandt {hidden_bytes} skjulte bytes efter EOF!{C.RESET}")
                else:
                    self.data["Steganografi_Analyse"] = {"Status": "Ren", "Beskrivelse": "Ingen data efter EOF"}
                    print(f"{C.GREEN}    ✓ Ingen åbenlys fil-vedhængning detekteret.{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [-] Kunne ikke udføre steganografi tjek: {e}{C.RESET}")

    def _extract_strings_and_intel(self):
        """NY V8 TILFØJELSE: River rå strenge ud af binærfilen for at finde hardcodede links og emails"""
        print(f"\n{C.YELLOW}[*] Udfører RAW String Extraction (Søger efter skjulte netværksspor)...{C.RESET}")
        try:
            with open(self.file_path, "rb") as f:
                data = f.read().decode('ascii', errors='ignore')
            
            # Leder efter URL'er og Emails i de rå binære data
            emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', data))
            urls = set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', data))
            
            for em in emails:
                # Frasorterer ubrugelige null-strenge eller Adobe XML namespaces
                if "adobe" not in em.lower() and "ns.adobe.com" not in em.lower():
                    self.data["Skjulte_Netværksspor"].append(em)
                    print(f"{C.RED}    🔥 SKJULT EMAIL FUNDET I RAW DATA: {em}{C.RESET}")
                    
            for url in urls:
                if "w3.org" not in url.lower() and "adobe.com" not in url.lower() and "purl.org" not in url.lower():
                    self.data["Skjulte_Netværksspor"].append(url)
                    print(f"{C.RED}    🔥 SKJULT URL FUNDET I RAW DATA: {url}{C.RESET}")
                    
            if not self.data["Skjulte_Netværksspor"]:
                print(f"{C.DIM}    [-] Ingen skjulte emails/URL'er i raw data.{C.RESET}")

        except Exception as e:
            print(f"{C.DIM}    [-] Fejl under RAW string extraction: {e}{C.RESET}")

    def _integrity_check(self):
        """Check file integrity"""
        print(f"\n{C.YELLOW}[*] Integrity Check...{C.RESET}")
        modsigende = []
        
        if (self.data["Temporal_Data"]["Oprettet"] and self.data["Temporal_Data"]["Ændret"]):
            if self.data["Temporal_Data"]["Oprettet"] != self.data["Temporal_Data"]["Ændret"]:
                modsigende.append("Timestamps differ (Filen er redigeret efter oprettelse)")
        
        self.data["Integritetstjek"]["Modsigende_Felter"] = modsigende
        
        if modsigende or self.data.get("Steganografi_Analyse", {}).get("Status") == "Mistænkelig":
            print(f"{C.RED}[!] ANOMALIES DETECTED: Beviserne indikerer manipulation.{C.RESET}")
            self.data["Integritetstjek"]["Bevis"] = "CRITICAL / MANIPULATED"
        else:
            print(f"{C.GREEN}[✓] Clean - Filen ser urørt ud.{C.RESET}")
            self.data["Integritetstjek"]["Bevis"] = "OK"
    
    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        # NYT: Rettes fra 10_FORENSIK til 11_FORENSIK for at matche modul-nummeret!
        filename = f"{session['loot_folder']}/11_FORENSIK_{os.path.basename(self.file_path).replace('.', '_')}.json"
        
        # NY V8: Sikker overskrivning af fil
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"\n{C.GREEN}[✓] Report saved: {filename}{C.RESET}")