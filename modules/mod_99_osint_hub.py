# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V61: MASTER OSINT AGGREGATOR
📌 Formål: Samler al passiv OSINT under én lynhurtig kørsel.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.base_module import BaseModule, ModuleCategory
from core.osint_hub import OSINTHub
from core.utils import C, datalake

class MasterOSINTAggregator(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "MASTER OSINT AGGREGATOR (HUB)"
        self.category = ModuleCategory.RECON
        self.data = {}

    def run(self, driver=None, target=""):
        print(f"\n{C.CYAN}{'='*60}\n[99] MASTER OSINT AGGREGATOR V61\n{'='*60}{C.RESET}")
        print(f"{C.YELLOW}[*] Starter fuld OSINT-undersøgelse af: {target}...{C.RESET}")
        
        hub = OSINTHub(target)
        self.data = hub.run_all(driver=driver)
        print(f"{C.GREEN}[✓] Fuld OSINT cyklus gennemført!{C.RESET}")
        return self.data