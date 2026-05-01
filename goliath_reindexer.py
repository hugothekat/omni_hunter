# -*- coding: utf-8 -*-
"""
🚀 GOLIATH V63: MASTER REINDEXER (Consolidated Edition)
📌 Formål: Synkroniserer loot_evidence med Datalaken og linker intelligente entiteter.
"""

import os
import sqlite3
import json
from pathlib import Path
from core.utils import C, datalake, logger, session
from core.forensics_engine import ForensicsEngine # Vores nye motor fra Batch 21

class GoliathReindexer:
    def __init__(self):
        self.loot_dir = Path(session.get("loot_folder", "loot_evidence"))
        self.db_path = datalake.db_path
        self.forensics = ForensicsEngine(str(self.loot_dir))

    def reindex_all(self):
        print(f"{C.CYAN}[*] Starter Master Reindexing V63...{C.RESET}")
        
        # 1. Scan efter nye filer
        files = list(self.loot_dir.glob("**/*"))
        for file_path in files:
            if file_path.is_file():
                self._process_file(file_path)
        
        print(f"{C.GREEN}[✓] Reindeksering fuldført!{C.RESET}")

    def _process_file(self, file_path):
        """Analyserer filen og linker den til Master Personas."""
        ext = file_path.suffix.lower()
        filename = file_path.name
        
        # Eksempel: Hvis det er et billede, træk Exif-data via ForensicsEngine
        if ext in ['.jpg', '.jpeg', '.png']:
            metadata = self.forensics.extract_image_metadata(filename)
            if metadata:
                print(f"{C.YELLOW}    -> Indekserer Metadata for {filename}{C.RESET}")
                # Log fundet i Datalaken linket til filnavnet
                datalake.ingest("REINDEXER", filename, {"metadata": metadata})

        # Registrer filen i den generelle loot-oversigt
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO osint_records (timestamp, source_module, target, data_json)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
            """, ("REINDEXER", filename, json.dumps({"path": str(file_path)})))

if __name__ == "__main__":
    reindexer = GoliathReindexer()
    reindexer.reindex_all()