import os
import json
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search

class ChatAppIntelligence:
    """Specialiseret søgning i lukkede økosystemer (Telegram, Discord, Signal)"""
    def __init__(self, query):
        self.query = query.strip()
        self.data = {"Søgeord": self.query, "Telegram_Hits": [], "Discord_Hits": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[22] Chat App Intelligence (Telegram & Discord)\n{'='*60}{C.RESET}")
        print(f"[*] Afdækker lukkede netværk for: {self.query}")

        # Telegram Dorking (Leder efter t.me links og telegra.ph)
        print(f"{C.YELLOW}[*] Scanner Telegram økosystemet...{C.RESET}")
        tg_dork = f'"{self.query}" site:t.me OR site:telegra.ph'
        tg_links = omni_dork_search(driver, tg_dork, max_links=5)
        for link in tg_links:
            print(f"{C.GREEN}    ✓ TELEGRAM SPOR: {link['url']}{C.RESET}")
            self.data["Telegram_Hits"].append(link['url'])

        # Discord Dorking (Leder efter invite links og server logs)
        print(f"\n{C.YELLOW}[*] Scanner Discord servere...{C.RESET}")
        dc_dork = f'"{self.query}" site:discord.com/invite OR site:discord.gg'
        dc_links = omni_dork_search(driver, dc_dork, max_links=5)
        for link in dc_links:
            print(f"{C.GREEN}    ✓ DISCORD INVITE: {link['url']}{C.RESET}")
            self.data["Discord_Hits"].append(link['url'])

        if not tg_links and not dc_links:
            print(f"{C.DIM}    [-] Ingen offentlige chat-spor fundet.{C.RESET}")
            
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/22_CHATAPP_{self.query.replace(' ', '_')}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")