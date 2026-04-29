# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class EmailTracker(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "EMAIL FOOTPRINT TRACKER"
        self.description = "Sporer emails til platforme."
        self.category = ModuleCategory.PERSON
        self.data = {"Spor": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.RED}=== EMAIL FOOTPRINT TRACKER ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" -site:haveibeenpwned.com', max_links=3):
                self.data["Spor"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
