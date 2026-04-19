import os
import json
import urllib.parse
from pathlib import Path
from datetime import datetime
from core.utils import C, session
from core.network import safe_get_with_retry, extract_duckduckgo_links

class PhoneIntelligenceHunter:
    """Deep web search for phone number occurrences"""
    def __init__(self, phone):
        self.phone = phone.replace(" ", "").replace("+45", "")
        self.data = {
            "Nummer": f"+45 {self.phone}",
            "Web_Spor": [],
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver):
        """Execute phone search"""
        print(f"\n{'='*60}")
        print(f"[07] Telefon-efterretning")
        print(f"{'='*60}")
        print(f"Target: +45 {self.phone}\n")

        formats = [
            f'"{self.phone}"',
            f'"{self.phone[:2]} {self.phone[2:4]} {self.phone[4:6]} {self.phone[6:8]}"',
            f'"{self.phone[:4]} {self.phone[4:]}"'
        ]
        
        print("[*] Dorking formats...")
        for dork in formats:
            if safe_get_with_retry(driver, f"https://duckduckgo.com/html/?q={urllib.parse.quote(dork)}"):
                links = extract_duckduckgo_links(driver, max_links=4)
                for link in links:
                    href = link["url"]
                    if "krak.dk" not in href:
                        print(f"    ✓ {href[:60]}")
                        if href not in self.data["Web_Spor"]:
                            self.data["Web_Spor"].append(href)
        
        self.save()

    def save(self):
        """Save findings to JSON"""
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/06_PHONE_{self.phone}.json"
        Path(filename).write_text(
            json.dumps(self.data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n[✓] Report saved: {filename}")