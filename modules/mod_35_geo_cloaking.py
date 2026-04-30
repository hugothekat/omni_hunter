# -*- coding: utf-8 -*-
import hashlib
from datetime import datetime
from typing import Dict, Any

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.browser import OmniHunterBrowser, BrowserConfig

class GeoDifferentialRecon(BaseModule):
    """
    GOLIATH V36: Mullvad / Exit-Node Recon Mode
    Henter samme URL via forskellige proxies/Tor for at detektere geo-blokering og WAF cloaking.
    """
    def __init__(self):
        super().__init__()
        self.name = "GEO DIFFERENTIAL RECON"
        self.description = "Sammenligner server-responser fra ClearNet og TOR (Anti-Censur)."
        self.category = ModuleCategory.NETWORK
        self.data = {
            "Target": "",
            "Differential_Analysis": {},
            "Cloaking_Detected": False,
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[35] GEO DIFFERENTIAL & CLOAKING RECON V36\n{'='*60}{C.RESET}")
        url = target if target.startswith("http") else f"https://{target}"
        self.data["Target"] = url

        print(f"{C.YELLOW}[*] Henter HTML via Standard IP (ClearNet)...{C.RESET}")
        cfg_clear = BrowserConfig(headless=True, browser_type="requests")
        browser_clear = OmniHunterBrowser(cfg_clear)
        res_clear = browser_clear.fetch(url)
        hash_clear = hashlib.md5(res_clear.get("html", "").encode()).hexdigest()
        len_clear = len(res_clear.get("html", ""))
        
        print(f"{C.YELLOW}[*] Henter HTML via TOR / Darknet (Spoofing Exit Node)...{C.RESET}")
        cfg_tor = BrowserConfig(headless=True, browser_type="requests", proxy="socks5h://127.0.0.1:9050")
        browser_tor = OmniHunterBrowser(cfg_tor)
        
        try:
            res_tor = browser_tor.fetch(url)
            hash_tor = hashlib.md5(res_tor.get("html", "").encode()).hexdigest()
            len_tor = len(res_tor.get("html", ""))
            
            if hash_clear != hash_tor:
                self.data["Cloaking_Detected"] = True
                print(f"{C.RED}    🔥 CLOAKING / GEO-BLOKERING DETEKTERET!{C.RESET}")
                print(f"       ClearNet Størrelse: {len_clear} bytes | TOR Størrelse: {len_tor} bytes")
                self.data["Differential_Analysis"] = {"ClearNet_Len": len_clear, "Tor_Len": len_tor}
            else:
                print(f"{C.GREEN}    ✓ Siden returnerer samme indhold uanset geografisk lokation.{C.RESET}")
                
        except Exception as e:
            print(f"{C.RED}    [!] TOR Fetch Fejl (Serveren smider måske TCP Drops mod Tor): {e}{C.RESET}")

        datalake.ingest(self.name, target, self.data)
        return self.data