# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class BSSIDGeofencer(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "BSSID GEOFENCER"
        self.description = "Søgning efter Router MAC-adresser."
        self.category = ModuleCategory.NETWORK
        self.data = {"Geo_Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.RED}=== BSSID GEOFENCING ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:wigle.net', max_links=3):
                self.data["Geo_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
