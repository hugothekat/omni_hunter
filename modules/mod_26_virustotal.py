# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class VirusTotalScanner(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "VIRUSTOTAL THREAT GRAPH"
        self.description = "Søgning på filer, domæner og IP'er."
        self.category = ModuleCategory.FORENSICS
        self.data = {"Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.RED}=== VIRUSTOTAL SCAN ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:virustotal.com', max_links=3):
                self.data["Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
