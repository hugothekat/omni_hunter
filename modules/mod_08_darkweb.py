# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class AbyssDarkwebCrawler(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "ABYSS DARKWEB CRAWLER"
        self.description = "Søgning på Tor gateways (Ahmia/Torch) via Clearnet proxies."
        self.category = ModuleCategory.NETWORK
        self.data = {"Onion_Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.RED}=== ABYSS DARKWEB CRAWLER ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:onion.ly OR site:onion.ws', max_links=3):
                self.data["Onion_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] Spor: {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
