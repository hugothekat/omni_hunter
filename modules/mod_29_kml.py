# modules/mod_29_kml.py
import os
import json
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class GoogleEarthExporter:
    """Støvsuger beviser for GPS koordinater og genererer et Google Earth 3D-kort"""
    def __init__(self):
        self.loot_dir = session["loot_folder"]
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.kml_file = f"MAP_EXPORT_{self.timestamp}.kml"

    def generate(self):
        print(f"\n{C.CYAN}{'='*60}\n[29] Google Earth KML-Kortlægning\n{'='*60}{C.RESET}")
        files = list(Path(self.loot_dir).glob("*.json"))
        
        placemarks = []
        
        print(f"{C.YELLOW}[*] Støvsuger {len(files)} bevisfiler for lokations-data (GPS/BSSID)...{C.RESET}")
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                
                # Finder GPS fra Forensik (Modul 11)
                if "GPS_Koordinater" in data and data["GPS_Koordinater"]:
                    lat = data["GPS_Koordinater"].get("Breddegrad")
                    lon = data["GPS_Koordinater"].get("Længdegrad")
                    if lat and lon:
                        placemarks.append(self._create_placemark(
                            name=f"Billede EXIF: {data.get('Fil', 'Ukendt')}",
                            desc=f"Tidspunkt: {data.get('Temporal_Data', {}).get('Oprettet', 'Ukendt')}",
                            lat=lat, lon=lon
                        ))

                # Finder GPS fra WiFi BSSID (Modul 21)
                if "BSSID" in data and data.get("Fundet") == True:
                    placemarks.append(self._create_placemark(
                        name=f"Router BSSID: {data['BSSID']}",
                        desc="Fysisk router lokation",
                        lat=data["Lat"], lon=data["Lon"]
                    ))
                    
            except Exception: continue

        if not placemarks:
            print(f"{C.RED}[!] Ingen GPS-koordinater fundet i dine beviser.{C.RESET}")
            return

        self._write_kml(placemarks)

    def _create_placemark(self, name, desc, lat, lon):
        # KML kræver Længdegrad før Breddegrad (Lon, Lat)
        return f"""
        <Placemark>
            <name>{name}</name>
            <description>{desc}</description>
            <Point>
                <coordinates>{lon},{lat},0</coordinates>
            </Point>
        </Placemark>
        """

    def _write_kml(self, placemarks):
        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>OMNI-HUNTER Lokations Spor</name>
        <description>Automatisk genereret OSINT kort</description>
        {''.join(placemarks)}
    </Document>
</kml>
        """
        file_path = os.path.join(self.loot_dir, self.kml_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(kml_content)
            
        print(f"{C.GREEN}[✓] Fandt {len(placemarks)} præcise GPS-lokationer!{C.RESET}")
        print(f"{C.CYAN}    -> Åbn denne fil direkte i Google Earth: {file_path}{C.RESET}")