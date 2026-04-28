# -*- coding: utf-8 -*-
import os
import json
import re
import requests
from bs4 import BeautifulSoup # NY V8 TILFØJELSE: Til Telegram Web scraping
from datetime import datetime
from pathlib import Path
from core.utils import C, session
from core.network import omni_dork_search

class ChatAppIntelligence:
    def __init__(self, query):
        self.query = query.strip()
        self.data = {
            "Søgeord": self.query, 
            "Telegram_Hits": [], 
            "Telegram_Intel": [],       # NY V8 TILFØJELSE: Deep Scrape data
            "Discord_Hits": [], 
            "Discord_Intel": [],        # NY V8 TILFØJELSE: Server Info via API
            "WhatsApp_Hits": [],        # NY V8 TILFØJELSE: WhatsApp Grupper
            "Skype_Hits": [],           # NY V8 TILFØJELSE: Skype Profiler
            "Snowflakes_Decoded": [], 
            "Timestamp": datetime.now().isoformat()
        }

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
        print(f"\n{C.CYAN}{'='*60}\n[22] Chat App Intelligence & Forensics (GOLIATH V8)\n{'='*60}{C.RESET}")
        
        # 1. Tjek om søgeordet rent faktisk er et Discord ID!
        if self.query.isdigit() and 17 <= len(self.query) <= 19:
            print(f"{C.YELLOW}[*] Detekterede et muligt Discord Snowflake ID! Udfører matematisk dekodning...{C.RESET}")
            creation_time = self._decode_discord_snowflake(self.query)
            if creation_time:
                print(f"{C.RED}    🔥 KONTO/SERVER OPRETTET: {creation_time}{C.RESET}")
                self.data["Snowflakes_Decoded"].append({"ID": self.query, "Oprettet": creation_time})

        # --- TELEGRAM OSINT ---
        print(f"\n{C.YELLOW}[*] Scanner Telegram økosystemet...{C.RESET}")
        tg_dork = f'"{self.query}" site:t.me OR site:telegra.ph'
        tg_links = omni_dork_search(driver, tg_dork, max_links=5)
        if tg_links:
            for link in tg_links:
                url = link['url']
                print(f"{C.GREEN}    ✓ TELEGRAM SPOR: {url}{C.RESET}")
                self.data["Telegram_Hits"].append(url)
                # NY V8: Deep Scrape af Telegram link
                self._analyze_telegram_link(url)
        else:
            print(f"{C.DIM}    [-] Ingen Telegram spor fundet.{C.RESET}")

        # --- DISCORD OSINT ---
        print(f"\n{C.YELLOW}[*] Scanner Discord servere...{C.RESET}")
        dc_dork = f'"{self.query}" site:discord.com/invite OR site:discord.gg'
        dc_links = omni_dork_search(driver, dc_dork, max_links=5)
        if dc_links:
            for link in dc_links:
                url = link['url']
                print(f"{C.GREEN}    ✓ DISCORD INVITE: {url}{C.RESET}")
                self.data["Discord_Hits"].append(url)
                
                # NY V8: Auto-ekstraher og API tjek invites
                invite_match = re.search(r'discord\.(?:com/invite|gg)/([a-zA-Z0-9-]+)', url)
                if invite_match:
                    self._analyze_discord_invite(invite_match.group(1))
                    
                # NY V8: Auto-detekter Snowflake IDs i URL'en (f.eks. besked links)
                snowflakes = re.findall(r'\b(\d{17,19})\b', url)
                for sf in set(snowflakes):
                    c_time = self._decode_discord_snowflake(sf)
                    if c_time:
                        print(f"{C.MAGENTA}      -> Skjult Snowflake ({sf}) dekodet: Oprettet {c_time}{C.RESET}")
                        if not any(d.get("ID") == sf for d in self.data["Snowflakes_Decoded"]):
                            self.data["Snowflakes_Decoded"].append({"ID": sf, "Oprettet": c_time, "Kilde": url})
        else:
            print(f"{C.DIM}    [-] Ingen Discord invites fundet.{C.RESET}")

        # --- WHATSAPP OSINT (NY V8) ---
        print(f"\n{C.YELLOW}[*] Scanner åbne WhatsApp Grupper...{C.RESET}")
        wa_dork = f'"{self.query}" site:chat.whatsapp.com'
        wa_links = omni_dork_search(driver, wa_dork, max_links=3)
        if wa_links:
            for link in wa_links:
                print(f"{C.GREEN}    ✓ WHATSAPP GRUPPE: {link['url']}{C.RESET}")
                self.data["WhatsApp_Hits"].append(link['url'])
        else:
            print(f"{C.DIM}    [-] Ingen WhatsApp grupper fundet.{C.RESET}")

        # --- SKYPE OSINT (NY V8) ---
        print(f"\n{C.YELLOW}[*] Scanner åbne Skype profiler...{C.RESET}")
        sk_dork = f'"{self.query}" site:skype.com'
        sk_links = omni_dork_search(driver, sk_dork, max_links=3)
        if sk_links:
            for link in sk_links:
                print(f"{C.GREEN}    ✓ SKYPE SPOR: {link['url']}{C.RESET}")
                self.data["Skype_Hits"].append(link['url'])
        else:
            print(f"{C.DIM}    [-] Ingen Skype profiler fundet.{C.RESET}")

        self.save()

    def _analyze_discord_invite(self, invite_code):
        """NY V8: Kalder Discord API direkte for at stjæle server info udenom Google"""
        print(f"{C.DIM}      -> Slår invite '{invite_code}' op via Discord API...{C.RESET}")
        try:
            res = requests.get(f"https://discord.com/api/v9/invites/{invite_code}?with_counts=true", timeout=5).json()
            if "guild" in res:
                guild_name = res["guild"].get("name", "Ukendt")
                members = res.get("approximate_member_count", "Ukendt")
                online = res.get("approximate_presence_count", "Ukendt")
                channel = res.get("channel", {}).get("name", "Ukendt")
                
                print(f"{C.RED}      🔥 SERVER FUNDET: {guild_name} | {members} Medlemmer ({online} Online) | Kanal: #{channel}{C.RESET}")
                self.data["Discord_Intel"].append({
                    "Invite": invite_code,
                    "Server_Navn": guild_name,
                    "Medlemmer": members,
                    "Online": online,
                    "Kanal": channel
                })
            elif "message" in res:
                print(f"{C.DIM}      [-] Invite link udløbet eller ugyldigt ({res.get('message')}).{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}      [-] Fejl ved Discord API opslag: {e}{C.RESET}")

    def _analyze_telegram_link(self, url):
        """NY V8: Udfører et HTTP kald for at udtrække navn og bio fra Telegram Meta-tags"""
        print(f"{C.DIM}      -> Tjekker Telegram Web Preview for '{url}'...{C.RESET}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                title = soup.find("meta", property="og:title")
                desc = soup.find("meta", property="og:description")
                
                title_val = title["content"] if title else "Ukendt"
                desc_val = desc["content"] if desc else "Ingen bio tilgængelig"
                
                # Hvis vi fanger en retsgyldig titel
                if title_val and title_val != "Telegram: Contact @telegram":
                    print(f"{C.RED}      🔥 KONTO/GRUPPE: {title_val}{C.RESET}")
                    print(f"{C.MAGENTA}      -> Bio: {desc_val[:100]}...{C.RESET}")
                    
                    self.data["Telegram_Intel"].append({
                        "URL": url,
                        "Navn": title_val,
                        "Beskrivelse": desc_val
                    })
        except Exception:
            pass

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/22_CHATAPP_{self.query.replace(' ', '_')}.json"
        
        # NY V8: Sikker overskrivning af fil
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
                
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"\n{C.GREEN}[✓] Chat App Rapport gemt: {filename}{C.RESET}")