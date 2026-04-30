# -*- coding: utf-8 -*-
import os
import json
import re
from pathlib import Path
from datetime import datetime
from core.utils import C, session

class GoogleEarthExporter:
    """GOLIATH V8: Geospatial Intelligence Hub til Google Earth & GIS analyse."""
    def __init__(self):
        self.loot_dir = session.get("loot_folder", "loot_evidence")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.kml_file = f"GOLIATH_GEOINT_{self.timestamp}.kml"
        self.placemarks = []

    def generate(self):
        print(f"\n{C.CYAN}{'='*60}\n[29] Geospatial Intelligence Hub (KML Export V8)\n{'='*60}{C.RESET}")
        files = list(Path(self.loot_dir).glob("*.json"))
        
        if not files:
            print(f"{C.YELLOW}[!] Ingen data fundet i {self.loot_dir}. Kør skanninger først.{C.RESET}")
            return

        print(f"{C.YELLOW}[*] Deep-Scanning efter koordinater i {len(files)} efterretningsfiler...{C.RESET}")
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                self._process_geo_logic(data, file.name)
            except Exception:
                continue

        if not self.placemarks:
            print(f"{C.RED}[!] Ingen GPS-koordinater fundet i dine beviser.{C.RESET}")
            return

        self._write_kml()

    def _process_geo_logic(self, data, filename):
        """Mapper data fra alle GOLIATH-moduler til kortet"""
        
        # 1. Billed-Forensik (Modul 11 / OPSEC)
        if "GPS_Koordinater" in data and data["GPS_Koordinater"]:
            lat = data["GPS_Koordinater"].get("Breddegrad")
            lon = data["GPS_Koordinater"].get("Længdegrad")
            ts = data.get("Temporal_Data", {}).get("Oprettet")
            
            # Formatér tidsstempel til KML standard (YYYY-MM-DDThh:mm:ssZ) hvis muligt
            kml_time = ""
            if ts and ts != "Ukendt":
                try:
                    # Antager format som "2023:10:25 14:30:00" fra EXIF
                    dt = datetime.strptime(ts, "%Y:%m:%d %H:%M:%S")
                    kml_time = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    kml_time = ts # Fallback
            
            if lat and lon:
                self.placemarks.append({
                    "name": f"FOTO: {data.get('Fil', 'Billede')}",
                    "desc": f"Enhed: {data.get('Enheds_Info', {}).get('Kameramodel', 'Ukendt')}<br>Dato: {ts}",
                    "lat": lat, "lon": lon, "type": "photo", "time": kml_time
                })

        # 2. WiFi Geofencing (Modul 21)
        if "BSSID" in data and data.get("Fundet") == True:
            self.placemarks.append({
                "name": f"WIFI: {data.get('Netværksnavn_SSID', 'Router')}",
                "desc": f"BSSID: {data['BSSID']}<br>Hardware: {data.get('Producent_OUI', 'Ukendt')}<br>Kilde: {data.get('Kilde', 'API')}",
                "lat": data["Lat"], "lon": data["Lon"], "type": "wifi", "time": None
            })

        # 3. TITAN Mass-Scan (Modul 16)
        if "Case_Intelligence" in data:
            gps_leads = data["Case_Intelligence"].get("Physical_Leads", {}).get("GPS_Data", [])
            for entry in gps_leads:
                link = entry.get("Link", "")
                # Udtrækker koordinater fra Google Maps links i TITAN data (fx. Maps links fra PDF'er)
                match = re.search(r'([-+]?\d+\.\d+),([-+]?\d+\.\d+)', link)
                if match:
                    self.placemarks.append({
                        "name": f"TITAN: {entry.get('File', 'Dokument')[:20]}",
                        "desc": "Lokation fundet via dokument-mining",
                        "lat": match.group(1), "lon": match.group(2), "type": "titan", "time": None
                    })

    def _write_kml(self):
        # Definerer Styles for professionelt udseende i Google Earth
        styles = """
    <Style id="photo">
        <IconStyle>
            <color>ff0000ff</color> <scale>1.2</scale>
            <Icon><href>http://maps.google.com/mapfiles/kml/shapes/camera.png</href></Icon>
        </IconStyle>
    </Style>
    <Style id="wifi">
        <IconStyle>
            <color>ffff0000</color> <scale>1.1</scale>
            <Icon><href>http://maps.google.com/mapfiles/kml/shapes/target.png</href></Icon>
        </IconStyle>
    </Style>
    <Style id="titan">
        <IconStyle>
            <color>ff00ff00</color> <scale>1.1</scale>
            <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
        </IconStyle>
    </Style>
        """
        
        nodes = ""
        for p in self.placemarks:
            time_tag = f"<TimeStamp><when>{p['time']}</when></TimeStamp>" if p['time'] else ""
            nodes += f"""
        <Placemark>
            <name>{p['name']}</name>
            <styleUrl>#{p['type']}</styleUrl>
            <description><![CDATA[{p['desc']}]]></description>
            {time_tag}
            <Point>
                <coordinates>{p['lon']},{p['lat']},0</coordinates>
            </Point>
        </Placemark>"""

        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>GOLIATH V8 - Taktisk GEOINT</name>
        <open>1</open>
        {styles}
        {nodes}
    </Document>
</kml>"""

        file_path = os.path.join(self.loot_dir, self.kml_file)
        
        # Sikker overskrivning
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(kml_content)
            
        print(f"\n{C.GREEN}[✓] GEOINT MISSION FULDFØRT!{C.RESET}")
        print(f"{C.MAGENTA}    [*] Plottede lokationer: {len(self.placemarks)}{C.RESET}")
        print(f"{C.CYAN}    -> Åbn filen i Google Earth Pro for 3D-analyse: {file_path}{C.RESET}")