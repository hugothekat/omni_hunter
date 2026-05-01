# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V52: GEO-SPATIAL ATTRIBUTION & EVIDENCE DOSSIER
📌 Formål: Samler rekonstruerede Personas, lokationer og bevismateriale i et offline HTML dossier.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.reporter import AutomatedCaseReporter

class IntelDossierGenerator(BaseModule):
    """GOLIATH V52: Den endelige efterretnings-syntese (Batch 12)."""
    
    def __init__(self):
        super().__init__()
        self.name = "GEO-SPATIAL ATTRIBUTION & EVIDENCE DOSSIER"
        self.description = "Genererer en komplet, geo-beriget HTML rapport med fil-links."
        self.category = ModuleCategory.REPORTING
        self.data = {
            "Target": "",
            "Dossier_Path": "",
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[28] INTEL DOSSIER & GEO-ATTRIBUTION V52\n{'='*60}{C.RESET}")
        self.target = target.strip() if target else "Unknown"
        self.data["Target"] = self.target
        
        reporter = AutomatedCaseReporter()
        dossier_path = reporter.generate_target_dossier(self.target)
        self.data["Dossier_Path"] = dossier_path
        
        print(f"{C.GREEN}[✓] Tactical Evidence Dossier er genereret og sikret!{C.RESET}")
        print(f"{C.MAGENTA}    -> Åbn filen: {dossier_path}{C.RESET}")
        
        datalake.ingest(self.name, self.target, self.data)
        return self.data