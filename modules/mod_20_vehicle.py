import os
import json
import re
import time
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from core.utils import C, session
from core.network import safe_get_with_retry
from core.browser import zap_cookies

class VehicleIntelligence:
    def __init__(self, reg_nr):
        self.reg = reg_nr.upper().replace(" ", "").replace("-", "")
        self.data = {"RegNr": self.reg, "Mærke_Model": "", "Stelnummer": "", "Status": "", "Timestamp": datetime.now().isoformat()}

    def run(self, driver):
        print(f"\n{C.CYAN}{'='*60}\n[20] Køretøjs-Efterretning (Nummerpladeopslag)\n{'='*60}{C.RESET}")
        print(f"[*] Slår nummerplade op: {self.reg}")

        url = f"https://www.tjekbil.dk/nummerplade/{self.reg}/overblik"
        if safe_get_with_retry(driver, url):
            zap_cookies(driver)
            time.sleep(2)
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                stel_match = re.search(r'(?i)(?:stelnummer|vin)[:\s]+([A-Z0-9]{17})', body_text)
                if stel_match:
                    self.data["Stelnummer"] = stel_match.group(1)
                    print(f"{C.GREEN}    ✓ Stelnummer (VIN) fundet: {self.data['Stelnummer']}{C.RESET}")

                try:
                    h1 = driver.find_element(By.TAG_NAME, "h1").text
                    self.data["Mærke_Model"] = h1.replace("Tjekbil", "").strip()
                    print(f"{C.GREEN}    ✓ Køretøj: {self.data['Mærke_Model']}{C.RESET}")
                except Exception: pass

                if "Afgemeldt" in body_text or "Afmeldt" in body_text:
                    self.data["Status"] = "Afmeldt"
                else:
                    self.data["Status"] = "Aktiv"
                print(f"{C.GREEN}    ✓ Status: {self.data['Status']}{C.RESET}")

            except Exception as e:
                print(f"{C.YELLOW}    [-] Kunne ikke udtrække alt data automatisk. Tjek manuelt: {url}{C.RESET}")
        else:
            print(f"{C.RED}    [-] Kunne ikke forbinde til motor-registret.{C.RESET}")
        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/20_VEHICLE_{self.reg}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")