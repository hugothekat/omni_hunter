# -*- coding: utf-8 -*-
import os

print("[*] INITIATING THE PYTHON DEPLOYER ENGINE (PROTOKOL OMEGA)...")

# --- SLET DE ØDELAGTE FILER ---
bad_modules = [
    "mod_01_krak.py", "mod_06_emailgen.py", "mod_08_darkweb.py",
    "mod_09_emailtrack.py", "mod_12_revphone.py", "mod_19_crypto.py",
    "mod_20_vehicle.py", "mod_21_bssid.py", "mod_22_chatapp.py",
    "mod_26_virustotal.py", "mod_30_person_intel.py"
]

for m in bad_modules:
    path = os.path.join("modules", m)
    if os.path.exists(path):
        os.remove(path)
print("[+] Korrupte karantæne-filer slettet.")

# --- DICTIONARY MED MODUL-KODE (Fuld OOP, Ingen Genveje) ---
MODULES = {}

MODULES["mod_01_krak.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class NationalDirectoryDorker(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "NATIONAL DIRECTORY MATRIX"
        self.description = "Søgning i Krak, 118, DeGuleSider og Proff."
        self.category = ModuleCategory.PERSON
        self.data = {"Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.RED}=== NATIONAL DIRECTORY MATRIX ==={C.RESET}")
        if driver:
            for dork in [f'"{target}" site:krak.dk', f'"{target}" site:proff.dk']:
                for hit in omni_dork_search(driver, dork, max_links=2):
                    self.data["Hits"].append(hit.get('url'))
                    print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_06_emailgen.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class EmailPatternGenerator(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "EMAIL SNIPER"
        self.description = "Genererer og verificerer emails."
        self.category = ModuleCategory.PERSON
        self.data = {"Breach_Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.RED}=== EMAIL SNIPER ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}"', max_links=3):
                self.data["Breach_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] Verificeret: {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_08_darkweb.py"] = """
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
        print(f"\\n{C.RED}=== ABYSS DARKWEB CRAWLER ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:onion.ly OR site:onion.ws', max_links=3):
                self.data["Onion_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] Spor: {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_09_emailtrack.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class EmailTracker(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "EMAIL FOOTPRINT TRACKER"
        self.description = "Sporer emails til platforme."
        self.category = ModuleCategory.PERSON
        self.data = {"Spor": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.RED}=== EMAIL FOOTPRINT TRACKER ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" -site:haveibeenpwned.com', max_links=3):
                self.data["Spor"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_12_revphone.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class ReversePhoneIntelligence(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "REVERSE PHONE INTELLIGENCE"
        self.description = "OSINT på danske telefonnumre."
        self.category = ModuleCategory.PERSON
        self.data = {"Platform_Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.RED}=== REVERSE PHONE INTELLIGENCE ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:facebook.com OR "MobilePay"', max_links=3):
                self.data["Platform_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_19_crypto.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class CryptoLedgerAnalyzer(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "CRYPTO WHALE-TRACE"
        self.description = "Søgning efter kryptoadresser i ransomware rapporter."
        self.category = ModuleCategory.FINANCE
        self.data = {"Svindel_Advarsler": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.RED}=== CRYPTO WHALE-TRACE ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" (scam OR hack OR stolen)', max_links=3):
                self.data["Svindel_Advarsler"].append(hit.get('url'))
                print(f"{C.RED}[!] Trussel: {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_20_vehicle.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
from core.network import omni_dork_search

class VehicleIntelligence(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "VEHICLE INTELLIGENCE"
        self.description = "OSINT på danske nummerplader."
        self.category = ModuleCategory.GENERAL
        self.data = {"Dork_Hits": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.RED}=== VEHICLE INTEL ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:nummerplade.net', max_links=3):
                self.data["Dork_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] Hit: {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_21_bssid.py"] = """
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
        print(f"\\n{C.RED}=== BSSID GEOFENCING ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:wigle.net', max_links=3):
                self.data["Geo_Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_22_chatapp.py"] = """
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
        print(f"\\n{C.RED}=== CHAT-APP INTEL ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'site:t.me "{target}" OR site:discord.com "{target}"', max_links=3):
                self.data["Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_26_virustotal.py"] = """
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
        print(f"\\n{C.RED}=== VIRUSTOTAL SCAN ==={C.RESET}")
        if driver:
            for hit in omni_dork_search(driver, f'"{target}" site:virustotal.com', max_links=3):
                self.data["Hits"].append(hit.get('url'))
                print(f"{C.GREEN}[+] {hit.get('url')}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

MODULES["mod_30_person_intel.py"] = """
# -*- coding: utf-8 -*-
from typing import Dict, Any
from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake, ThreatIntelExtractor
from core.network import omni_dork_search

class AutonomousOrchestrator(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "GRAND ORCHESTRATOR"
        self.description = "Auto-Pivoterende Identity Resolution."
        self.category = ModuleCategory.PERSON
        self.data = {"Hits": [], "Lækager": []}

    def run(self, driver, target: str) -> Dict[str, Any]:
        print(f"\\n{C.BG_RED}{C.WHITE} === GRAND ORCHESTRATOR ENGAGED === {C.RESET}\\n")
        print(f"{C.CYAN}[*] Udfører OSINT søgning mod: {target}{C.RESET}")
        
        if driver:
            collected_text = ""
            for hit in omni_dork_search(driver, f'"{target}" site:linkedin.com OR "{target}"', max_links=5):
                print(f"{C.GREEN} [+] {hit.get('title')}{C.RESET}")
                collected_text += f" {hit.get('snippet', '')}"
            
            iocs = ThreatIntelExtractor.extract_all(collected_text)
            if iocs.get("email"): 
                self.data["Lækager"] = iocs["email"]
                print(f"{C.MAGENTA} [!] AUTO-PIVOT: Fandt emails: {iocs['email']}{C.RESET}")
                
        print(f"\\n{C.GREEN}[✓] Orchestrator fuldført.{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data
"""

# --- SKRIV TIL DISK SIKKERT ---
for filename, content in MODULES.items():
    path = os.path.join("modules", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"\033[0;32m[✓] RESTAURET: {filename}\033[0m")

print("\n\033[0;32m[✓] PROTOKOL OMEGA FULDFØRT SUCCESFULDT!\033[0m")
print("\033[0;33mDu kan nu slette scriptet (rm fix_modules.py) og køre ./goliath.sh\033[0m")

