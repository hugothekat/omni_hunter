# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class ChatAppIntelligence(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "CHAT-APP SYNDICATE INTEL"
        self.description = "Kortlægning af Telegram & Discord."
        self.category = ModuleCategory.SOCIAL
        self.data = {"Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.RED}=== CHAT-APP INTEL ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'site:t.me "{target}" OR site:discord.com "{target}"', max_links=3):
                self.data["Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
