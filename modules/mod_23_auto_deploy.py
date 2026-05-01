# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V42: SECURE AUTO-DEPLOY ENGINE
📌 Formål: Sikker kloning af repositories via Modul 22, med automatisk venv provisionering.
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, datalake
# Vi genbruger direkte Siterip modulet til den sikre kloning (Expansion Mode)
from modules.mod_22_siterip import SiteripModule

class SecureAutoDeploy(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "SECURE AUTO-DEPLOY & VENV BUILDER"
        self.description = "Integrerer Modul 22 for kloning og bygger automatisk python 3.8 venv."
        self.category = ModuleCategory.NETWORK
        self.data = {
            "Target": "",
            "Loot_Dir": "",
            "Venv_Status": "Pending",
            "Pip_Status": "Pending",
            "Docker_Status": "Pending",
            "Timestamp": datetime.now().isoformat()
        }

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        target = target.strip()
        # Auto-Correction: Hvis målet ikke ligner en URL (f.eks. input-fejlen "26")
        if not target.startswith("http") and not target.endswith(".git"):
            print(f"{C.YELLOW}[*] Ugyldigt mål '{target}' detekteret. Tvinger fallback til Reprohack repo...{C.RESET}")
            target = "https://github.com/reprohack/reprohack_site.git"
            
        self.data["Target"] = target
        
        print(f"\n{C.CYAN}{'='*60}\n[26] SECURE AUTO-DEPLOY ENGINE V42\n{'='*60}{C.RESET}")
        
        # 1. Klon repo og scan for secrets via eksisterende Siterip modul
        print(f"{C.YELLOW}[*] FASE 1: Delegerer kloning og OPSEC secret-scanning til Modul 22...{C.RESET}")
        siterip = SiteripModule(target)
        siterip_result = siterip.run(driver, target)
        
        repo_dir = siterip_result.get("Loot_Directory")
        if not repo_dir or not os.path.exists(repo_dir):
            print(f"{C.RED}[!] Kloning fejlede eller blev afbrudt. Kan ikke fortsætte.{C.RESET}")
            return self.data
            
        self.data["Loot_Dir"] = repo_dir

        # NYT V43: Docker Auto-Detect (Expansion Mode)
        dockerfile_path = os.path.join(repo_dir, "Dockerfile")
        if os.path.exists(dockerfile_path):
            print(f"\n{C.MAGENTA}[*] FASE 2: Dockerfile detekteret! Skifter til Container-Build Mode...{C.RESET}")
            image_name = f"omni_deploy_{os.path.basename(repo_dir).lower()}"
            try:
                subprocess.run(["docker", "build", "-t", image_name, "."], cwd=repo_dir, check=True)
                self.data["Docker_Status"] = "Success"
                print(f"{C.GREEN}    ✓ Docker image '{image_name}' bygget succesfuldt! Afslutter.{C.RESET}")
                datalake.ingest(self.name, target, self.data)
                return self.data
            except subprocess.CalledProcessError as e:
                self.data["Docker_Status"] = "Failed"
                print(f"{C.RED}    [!] Docker build fejlede: {e}. Prøver Venv fallback...{C.RESET}")
        
        # 2. Opret Virtual Environment (Dynamisk Fallback)
        print(f"\n{C.YELLOW}[*] FASE 2: Provisionerer Virtual Environment i {repo_dir}...{C.RESET}")
        venv_path = os.path.join(repo_dir, ".virtualenv")
        python_bin = shutil.which("python3.8") or sys.executable
        try:
            # Kører virtualenv sikkert via subprocess
            subprocess.run(
                [python_bin, "-m", "virtualenv", venv_path],
                cwd=repo_dir, check=True, capture_output=True
            )
            self.data["Venv_Status"] = "Success"
            print(f"{C.GREEN}    ✓ Virtualenv (.virtualenv) oprettet succesfuldt!{C.RESET}")
        except subprocess.CalledProcessError as e:
            self.data["Venv_Status"] = "Failed"
            print(f"{C.RED}    [!] Fejl ved oprettelse af venv: {e.stderr.decode('utf-8', errors='ignore')}{C.RESET}")
            return self.data

        # 3. Installer dependencies
        print(f"\n{C.YELLOW}[*] FASE 3: Installerer afhængigheder fra requirements/production.txt...{C.RESET}")
        pip_executable = os.path.join(venv_path, "bin", "pip")
        req_file = os.path.join(repo_dir, "requirements", "production.txt")
        
        if os.path.exists(req_file):
            try:
                subprocess.run([pip_executable, "install", "-r", req_file], cwd=repo_dir, check=True)
                self.data["Pip_Status"] = "Success"
                print(f"{C.GREEN}    ✓ Produktion-afhængigheder installeret i isoleret miljø!{C.RESET}")
            except subprocess.CalledProcessError:
                self.data["Pip_Status"] = "Failed"
                print(f"{C.RED}    [!] Pip installation fejlede. Der kan være ukompatible pakker i requirements.{C.RESET}")
        else:
            self.data["Pip_Status"] = "Not Found"
            print(f"{C.DIM}    [-] BEMÆRK: Fandt ikke {req_file}.{C.RESET}")

        print(f"\n{C.GREEN}[✓] Auto-Deploy Fuldført! Applikationen er klar i: {repo_dir}{C.RESET}")
        datalake.ingest(self.name, target, self.data)
        return self.data