# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V51: PERSONA RECONSTRUCTOR & IDENTITY LINKER
📌 Formål: Cross-Module Correlation, Fuzzy Matching og 360-graders profilering.
"""
import sys
import os
import json
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake

class PersonaReconstructor(BaseModule):
    """GOLIATH V51: The Identity Linker (Batch 11)."""
    
    def __init__(self):
        super().__init__()
        self.name = "PERSONA RECONSTRUCTOR & LINKER"
        self.description = "Bygger 360-graders identiteter ud fra rå Harvested Data og Credentials."
        self.category = ModuleCategory.PERSON
        self.data = {
            "Target": "",
            "Personas_Reconstructed": 0,
            "Master_Personas": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _get_harvested_data(self, target: str) -> List[Dict]:
        db_path = Path(session.get("loot_folder", "loot_evidence")) / "omni_datalake.db"
        payloads = []
        if db_path.exists():
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    # Hent de seneste payloads
                    cursor.execute("SELECT payload FROM harvested_data WHERE target=? ORDER BY timestamp DESC", (target,))
                    for row in cursor.fetchall():
                        try:
                            payloads.append(json.loads(row[0]))
                        except: pass
            except Exception as e:
                print(f"{C.RED}[!] Databasefejl ved læsning af Harvested Data: {e}{C.RESET}")
        return payloads

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[27] PERSONA RECONSTRUCTOR & IDENTITY LINKER V51\n{'='*60}{C.RESET}")
        self.target = target.strip() if target else "Unknown"
        self.data["Target"] = self.target
        
        payloads = self._get_harvested_data(self.target)
        if not payloads:
            print(f"{C.YELLOW}[*] Ingen harvested_data fundet for målet. Kør Modul 26 først!{C.RESET}")
            return self.data
            
        print(f"{C.YELLOW}[*] Analyserer {len(payloads)} JSON-blobs for identitets-markører (Fuzzy Matching)...{C.RESET}")
        
        personas_map = {}
        
        # 1. Parsing Logik: Leder efter felter der indikerer en person (Fuzzy Matching)
        for payload in payloads:
            # Håndter både lister og dicts rekursivt/flat
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if not isinstance(item, dict): continue
                
                name = item.get("name") or item.get("display_name") or item.get("fullname") or item.get("full_name") or ""
                email = item.get("email") or item.get("mail") or ""
                phone = item.get("phone") or item.get("telefon") or item.get("mobile") or ""
                username = item.get("username") or item.get("handle") or item.get("user") or ""
                
                # Hvis vi har et unikt ID eller stærk indikator (email/username), bygger vi identiteten
                uid = username or email or name
                if uid:
                    if uid not in personas_map:
                        personas_map[uid] = {
                            "name": name, "email": email, 
                            "phone": phone, "social_handle": username,
                            "raw_data_ref": json.dumps(item, ensure_ascii=False)
                        }
                    else:
                        # Flet data (Cross-Module Correlation Logic)
                        if not personas_map[uid]["email"] and email: personas_map[uid]["email"] = email
                        if not personas_map[uid]["phone"] and phone: personas_map[uid]["phone"] = phone
                        
        self.data["Master_Personas"] = list(personas_map.values())
        self.data["Personas_Reconstructed"] = len(personas_map)
        
        print(f"{C.GREEN}[✓] Reconstruerede {len(personas_map)} 360-graders profiler fra rå data!{C.RESET}")
        
        # Sender til Datalake så det gemmes i master_personas tabellen
        datalake.ingest(self.name, self.target, self.data)
        
        return self.data