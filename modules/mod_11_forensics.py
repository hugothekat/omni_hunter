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
        self.file_path = file_path
        self.data = {
            "Fil": os.path.basename(file_path),
            "Sti": file_path,
            "Filstørrelse": 0,
            "Filtype": "",
            "GPS_Koordinater": None,
            "GPS_Maps_Link": "",
            "Temporal_Data": {
                "Oprettet": None,
                "Ændret": None,
                "Manipuleret": False
            },
            "Enheds_Info": {},
            "EXIF_Data": {},
            "Integritetstjek": {
                "Bevis": "",
                "Modsigende_Felter": []
            },
            "Timestamp": datetime.now().isoformat()
        }
    
    def run(self):
        """Execute forensics analysis"""
        print(f"\n{'='*60}")
        print(f"[11] Udtræk ALT data fra billeder")
        print(f"{'='*60}")
        print(f"File: {os.path.basename(self.file_path)}\n")
        
        if not os.path.exists(self.file_path):
            print(f"[!] File not found")
            return
        
        self._extract_basic_info()
        if self.data["Filtype"].lower() in ['jpg', 'jpeg', 'png', 'gif']:
            self._extract_exif_data()
            self._extract_gps_data()
        self._temporal_analysis()
        self._device_profiling()
        self._integrity_check()
        self.save()
    
    def _extract_basic_info(self):
        """Extract basic file information and Cryptographic Hashes"""
        try:
            stat_info = os.stat(self.file_path)
            self.data["Filstørrelse"] = stat_info.st_size
            self.data["Filtype"] = os.path.splitext(self.file_path)[1][1:].upper()
            
            # --- NYT: Kryptografisk Bevis-sikring (Chain of Custody) ---
            print(f"[*] Beregner kryptografiske fingeraftryk...")
            with open(self.file_path, "rb") as f:
                file_bytes = f.read()
                self.data["Kryptografi"] = {
                    "MD5": hashlib.md5(file_bytes).hexdigest(),
                    "SHA-256": hashlib.sha256(file_bytes).hexdigest()
                }
            
            print(f"[*] File Type: {self.data['Filtype']}")
            print(f"[*] Size: {self.data['Filstørrelse']} bytes")
            print(f"[*] SHA-256: {self.data['Kryptografi']['SHA-256'][:15]}...")
        except Exception as e:
            print(f"[!] Error: {str(e)}")
    
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
            print(f"[*] EXIF Fields: {len(self.data['EXIF_Data'])}")
        except Exception:
            print(f"[*] No EXIF data")
    
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
            self.data["GPS_Maps_Link"] = f"https://www.google.com/maps/?q={lat},{lon}"
            
            print(f"[✓] GPS: {lat:.6f}, {lon:.6f}")
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
                print(f"[!] MANIPULATION DETECTED")
            
            print(f"[*] Created: {created}")
            print(f"[*] Modified: {modified}")
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
                    print(f"[*] {tag_name}: {value}")
        except Exception:
            pass
    
    def _integrity_check(self):
        """Check file integrity"""
        print(f"\n[*] Integrity Check...")
        modsigende = []
        
        if (self.data["Temporal_Data"]["Oprettet"] and self.data["Temporal_Data"]["Ændret"]):
            if self.data["Temporal_Data"]["Oprettet"] != self.data["Temporal_Data"]["Ændret"]:
                modsigende.append("Timestamps differ")
        
        self.data["Integritetstjek"]["Modsigende_Felter"] = modsigende
        
        if modsigende:
            print(f"[!] ANOMALIES DETECTED")
            self.data["Integritetstjek"]["Bevis"] = "CRITICAL"
        else:
            print(f"[✓] Clean")
            self.data["Integritetstjek"]["Bevis"] = "OK"
    
    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/10_FORENSIK_{os.path.basename(self.file_path).replace('.', '_')}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"\n[✓] Report saved: {filename}")