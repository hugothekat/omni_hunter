import os
import json
import re
from datetime import datetime
from core.utils import C, session
from core.network import omni_dork_search

class ChatAppIntelligence:
    def __init__(self, query):
        self.query = query.strip()
        self.data = {"Søgeord": self.query, "Telegram_Hits": [], "Discord_Hits": [], "Snowflakes_Decoded": [], "Timestamp": datetime.now().isoformat()}

    # --- TILFØJ DENNE NYE FUNKTION ---
    def _decode_discord_snowflake(self, snowflake_id):
        """Dekoder et Discord ID for at finde oprettelsesdatoen (OSINT Trick)"""
        try:
            # Discord Epoch (2015-01-01T00:00:00.000Z)
            discord_epoch = 1420070400000
            # Tidsstemplet er gemt i de første 42 bits af ID'et
            timestamp_ms = (int(snowflake_id) >> 22) + discord_epoch
            creation_date = datetime.fromtimestamp(timestamp_ms / 1000.0)
            return creation_date.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[22] Chat App Intelligence & Forensics\n{'='*60}{C.RESET}")
        
        # 1. Tjek om søgeordet rent faktisk er et Discord ID!
        if self.query.isdigit() and 17 <= len(self.query) <= 19:
            print(f"{C.YELLOW}[*] Detekterede et muligt Discord Snowflake ID! Udfører matematisk dekodning...{C.RESET}")
            creation_time = self._decode_discord_snowflake(self.query)
            if creation_time:
                print(f"{C.RED}    🔥 KONTO/SERVER OPRETTET: {creation_time}{C.RESET}")
                self.data["Snowflakes_Decoded"].append({"ID": self.query, "Oprettet": creation_time})

        # ... (Din eksisterende kode med tg_dork og dc_dork fortsætter herunder)
        print(f"\n{C.YELLOW}[*] Scanner Telegram økosystemet...{C.RESET}")
        tg_dork = f'"{self.query}" site:t.me OR site:telegra.ph'
        tg_links = omni_dork_search(driver, tg_dork, max_links=5)
        for link in tg_links:
            print(f"{C.GREEN}    ✓ TELEGRAM SPOR: {link['url']}{C.RESET}")
            self.data["Telegram_Hits"].append(link['url'])

        # Scanner Discord og fanger automatisk IDs i URL'er
        print(f"\n{C.YELLOW}[*] Scanner Discord servere...{C.RESET}")
        dc_dork = f'"{self.query}" site:discord.com/invite OR site:discord.gg'
        dc_links = omni_dork_search(driver, dc_dork, max_links=5)
        for link in dc_links:
            print(f"{C.GREEN}    ✓ DISCORD INVITE: {link['url']}{C.RESET}")
            self.data["Discord_Hits"].append(link['url'])

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/22_CHATAPP_{self.query.replace(' ', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")