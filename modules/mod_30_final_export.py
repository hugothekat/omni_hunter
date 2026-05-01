# -*- coding: utf-8 -*-
import sys
import random
import string
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from tools.omni_export import GoliathExporter

class SecureEvidenceExport(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "SECURE EVIDENCE EXPORT"
        self.description = "Pakker og AES-256 krypterer hele sagsmappen for et target."
        self.category = ModuleCategory.REPORTING
        self.data = {}

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[30] SECURE EVIDENCE EXPORT V55\n{'='*60}{C.RESET}")
        self.target = target.strip()
        
        if not self.target:
            print(f"{C.RED}[!] Intet mål angivet for eksport.{C.RESET}")
            return {}

        # Genererer et stærkt One-Time Password for Perfect Forward Secrecy
        otp = ''.join(random.choices(string.ascii_letters + string.digits + "!@#%*", k=16))
        
        print(f"{C.YELLOW}[*] Genererer engangsadgangskode (OTP) til AES-256 Vaulten...{C.RESET}")
        print(f"{C.MAGENTA}    -> DECRYPTION PASSWORD: {otp}{C.RESET}")
        
        try:
            exporter = GoliathExporter(self.target, otp)
            export_path = exporter.export()
            
            self.data = {
                "Target": self.target, "Export_Path": export_path, "OTP_Password": otp,
                "Status": "Success", "Timestamp": datetime.now().isoformat()
            }
            datalake.ingest(self.name, self.target, self.data)
            print(f"{C.GREEN}[✓] Sagseksportering fuldført! Download klar via Web UI.{C.RESET}")
        except Exception as e:
            print(f"{C.RED}[!] Eksport fejlede: {e}{C.RESET}")
        return self.data