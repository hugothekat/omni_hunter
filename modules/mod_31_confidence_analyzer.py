# -*- coding: utf-8 -*-
"""
🚀 GOLIATH V56: CONFIDENCE ANALYZER (Batch 16)
📌 Formål: Beregner tillidsscore for Master Personas baseret på Cross-Module Validation.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake

class ConfidenceAnalyzer(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "CONFIDENCE ANALYZER"
        self.description = "Beregner matematisk tillidsscore via Cross-Module Validation."
        self.category = ModuleCategory.ANALYSIS
        self.data = {
            "Target": "",
            "Personas_Scored": 0,
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[31] CONFIDENCE ANALYZER V56\n{'='*60}{C.RESET}")
        self.target = target.strip()
        self.data["Target"] = self.target
        
        print(f"{C.YELLOW}[*] Starter automatisk Confidence Scoring for {self.target or 'ALLE'} personas...{C.RESET}")
        db_path = Path(session.get("loot_folder", "loot_evidence")) / "omni_datalake.db"
        
        if not db_path.exists():
            print(f"{C.RED}[!] Datalake ikke fundet.{C.RESET}")
            return self.data

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Hvis et target er angivet, scorer vi kun det. Ellers scorer vi alle.
                if self.target:
                    cursor.execute("SELECT id, name, email FROM master_personas WHERE target=?", (self.target,))
                else:
                    cursor.execute("SELECT id, name, email FROM master_personas")
                    
                personas = cursor.fetchall()
                
                for p_id, name, email in personas:
                    score = 0
                    if name: score += 20
                    if email: score += 30
                    
                    # Cross-module validation: Hvor mange uafhængige OSINT kilder har set denne email?
                    if email:
                        cursor.execute("SELECT COUNT(DISTINCT source_module) FROM osint_records WHERE data_json LIKE ?", (f'%{email}%',))
                        source_count = cursor.fetchone()[0]
                        score += (source_count * 15) # +15 point pr. uafhængig kilde (f.eks. MailRip + Siterip)
                    
                    final_score = min(score, 100) # Cap på 100%
                    cursor.execute("UPDATE master_personas SET confidence_score = ? WHERE id = ?", (final_score, p_id))
                    self.data["Personas_Scored"] += 1
                    
                    print(f"{C.GREEN}    ✓ Persona #{p_id} opdateret: Confidence Score -> {final_score}%{C.RESET}")
                    
        except Exception as e:
            print(f"{C.RED}[!] Databasefejl under scoring: {e}{C.RESET}")
            
        print(f"\n{C.GREEN}[✓] Analyse fuldført. {self.data['Personas_Scored']} profiler valideret.{C.RESET}")
        datalake.ingest(self.name, self.target, self.data)
        
        return self.data
