import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from core.utils import C, session

class UsernameMatrixAnalyzer:
    def __init__(self, username):
        self.username = username.strip()
        self.data = {"Brugernavn": self.username, "Platforme": [], "Timestamp": datetime.now().isoformat()}

    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[23] Global Username Matrix (Sherlock Engine)\n{'='*60}{C.RESET}")
        print(f"[*] Skanner over 300 platforme for: {self.username} (Tillad op til 2 minutter)...")
        
        try:
            # Vi øger timeout let, men fanger fejl bedre
            process = subprocess.Popen(
                ['sherlock', self.username, '--timeout', '5', '--print-found'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Læser output live!
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if "[+]" in line:
                    site_url = line.split("[+]")[1].strip()
                    platform_name = site_url.split("://")[1].split("/")[0]
                    
                    print(f"{C.GREEN}    🔥 {platform_name.upper()}: {C.CYAN}{site_url}{C.RESET}")
                    self.data["Platforme"].append(site_url)

            process.wait()
            
            if not self.data["Platforme"]:
                print(f"{C.YELLOW}    [-] Ingen profiler fundet (eller Sherlock er ikke installeret korrekt).{C.RESET}")
                
        except FileNotFoundError:
            print(f"{C.RED}    [!] 'sherlock' er ikke installeret globalt. Kør: pip install sherlock-project{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Fejl under Matrix skanning: {e}{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        filename = f"{session['loot_folder']}/23_MATRIX_{self.username}.json"
        Path(filename).write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Matrix rapport gemt ({len(self.data['Platforme'])} hits): {filename}{C.RESET}")