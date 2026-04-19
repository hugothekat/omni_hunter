import requests
from core.utils import C
from core.network import CONFIG

class VirusTotalAnalyzer:
    def __init__(self, hash_or_ip):
        self.target = hash_or_ip.strip()
        self.api_key = CONFIG["api_keys"].get("virus_total", "")
        self.data = {"Target": self.target, "Malicious": 0, "Undetected": 0, "Details": {}}

    def run(self, driver=None):
        print(f"\n{C.CYAN}[26] VirusTotal Threat Intelligence{C.RESET}")
        if not self.api_key:
            print(f"{C.RED}[!] VirusTotal API-nøgle mangler i config.json{C.RESET}")
            return
            
        headers = {"x-apikey": self.api_key}
        # Auto-detekter om det er IP eller File Hash
        if "." in self.target and len(self.target) < 16:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{self.target}"
        else:
            url = f"https://www.virustotal.com/api/v3/files/{self.target}"

        try:
            res = requests.get(url, headers=headers).json()
            stats = res['data']['attributes']['last_analysis_stats']
            print(f"{C.RED}    🔥 Malicious Hits: {stats['malicious']}{C.RESET}")
            print(f"{C.GREEN}    ✓ Rene Scans: {stats['undetected']}{C.RESET}")
            self.data["Malicious"] = stats['malicious']
            # Gem logik her...
        except Exception as e:
            print(f"{C.RED}[!] Fejl ved VT API: {e}{C.RESET}")