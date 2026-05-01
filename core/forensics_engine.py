# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER CORE: FORENSICS ENGINE (GOLIATH V8)
📌 Formål: Udtræk af digitale spor fra SQLite-databaser og fil-metadata.
Inspireret af "Violent Python" til mass-forensics.
"""
import sqlite3
import os
from core.logger import logger

class ForensicsEngine:
    def __init__(self, loot_dir):
        """Initialiserer motoren med stien til den aktive bevis-mappe."""
        self.loot_dir = loot_dir
        self.findings = {}

    def parse_sqlite_db(self, db_name, query):
        """
        Forbinder til en SQLite database og udfører en SQL forespørgsel (ReadOnly).
        Kan bruges til at trække data ud af browser-historik eller chat-logs.
        """
        db_path = os.path.join(self.loot_dir, db_name)
        if not os.path.isfile(db_path):
            logger.error(f"[FORENSICS] Databasen {db_name} findes ikke.")
            return None

        try:
            uri = f"file:{os.path.abspath(db_path)}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            cursor = conn.cursor()
            cursor.execute(query)
            
            results = cursor.fetchall()
            conn.close()
            
            self.findings[db_name] = results
            return results
        except Exception as e:
            logger.error(f"[FORENSICS] SQL Fejl i {db_name}: {e}")
            return None

    def extract_image_metadata(self, image_filename):
        """Udtrækker Exif-metadata fra et billede (kræver Pillow)."""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            img_path = os.path.join(self.loot_dir, image_filename)
            if not os.path.isfile(img_path): return None

            with Image.open(img_path) as img_file:
                info = img_file._getexif()
                
            if info:
                exif_data = {TAGS.get(tag, tag): value for tag, value in info.items()}
                if 'GPSInfo' in exif_data: self.findings[f"{image_filename}_GPS"] = exif_data['GPSInfo']
                return exif_data
        except Exception as e:
            logger.error(f"[FORENSICS] Fejl ved læsning af billed-data for {image_filename}: {e}")
        return None