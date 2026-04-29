# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - THE APEX ORCHESTRATOR & TUI SHELL (main.py) v5.0 (PET-FE EXECUTIVE)
📌 Formål: Asynkront, professionelt kontrolcenter for PETFE OSINT operationer.
🔧 Features:
   - Clean Government-Grade Interface (Rød / Klinisk)
   - Alias Engine (Nemme 1-ords kommandoer)
   - Cryptographic Compliance Audit Logging
   - Background Job Manager & Operational Workspaces
   - Bulletproof Exception Handling
"""

import os
import sys
import shutil
import argparse
import threading
import time
import requests
from pathlib import Path
from datetime import datetime
import traceback
import uuid
import importlib.util
import inspect

# --- GOLIATH CORE INTEGRATIONER ---
try:
    from core.utils import C, session, military_sanitize_input
    from core.browser import OmniHunterBrowser, BrowserConfig
    from core.logger import logger
    from core.reporter import AutomatedCaseReporter  
    
    try: from core.config_vault import vault
    except ImportError: vault = None
    
    try: from core.module_manager import ModuleManager
    except ImportError: ModuleManager = None
    
    try: from core.nexus import nexus
    except ImportError: nexus = None

except ImportError as e:
    print(f"\033[91m[!] KRITISK FEJL: Core-komponenter mangler. Fejl: {e}\033[0m")
    sys.exit(1)

# ==========================================
# 🔹 COMPLIANCE AUDIT LOGGER
# ==========================================
class ComplianceAuditLogger:
    def __init__(self):
        self.log_file = Path("compliance_audit.log")
        if not self.log_file.exists():
            self._write_log("SYSTEM BOOT", "Audit Log Initialized")

    def _write_log(self, action: str, details: str):
        timestamp = datetime.now().isoformat()
        operator = os.getlogin() if hasattr(os, 'getlogin') else "UNKNOWN_OPERATOR"
        raw_entry = f"[{timestamp}] OP:{operator} | ACT:{action} | DET:{details}"
        checksum = uuid.uuid5(uuid.NAMESPACE_OID, raw_entry).hex[:8]
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{raw_entry} | CHK:{checksum}\n")

    def log_command(self, cmd: str):
        self._write_log("COMMAND_EXECUTION", f"Command: '{cmd}'")

audit_logger = ComplianceAuditLogger()

# ==========================================
# 🔹 FALLBACK MODULE MANAGER
# ==========================================
class FallbackModuleManager:
    def __init__(self):
        self.modules = {}
        self.discover()

    def discover(self):
        mod_dir = Path("modules")
        if not mod_dir.exists(): return
        for file in mod_dir.glob("mod_*.py"):
            self.modules[file.name.split('_')[1]] = file.name

    def display_dynamic_menu(self):
        print(f"\n{C.RED}--- [ VÆRKTØJSOVERSIGT (FALLBACK) ] ---{C.RESET}")
        for mod_id, name in sorted(self.modules.items()):
            print(f" {C.WHITE}[{mod_id}]{C.RESET} {name}")
            
    def get_module(self, mod_id: str):
        print(f"{C.RED}[!] System kører i Fallback Mode. Tjek core/module_manager.py.{C.RESET}")
        return None

# ==========================================
# 🔹 DIAGNOSTICS & SYSTEM BOOT
# ==========================================
class GoliathDiagnostics:
    @staticmethod
    def run_pre_flight_checks():
        print(f"\n{C.RED}[*] Initialiserer PET FE Systemdiagnostik...{C.RESET}")
        tools = {"rg": "Ripgrep", "tesseract": "Tesseract OCR", "exiftool": "ExifTool", "nmap": "Nmap"}
        missing = [desc for tool, desc in tools.items() if shutil.which(tool) is None]
        if missing: print(f"{C.YELLOW} [!] Advarsel: Manglende systemværktøjer: {', '.join(missing)}{C.RESET}")
        else: print(f"{C.WHITE} [✓] Systemværktøjer verificeret.{C.RESET}")

        try:
            proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
            res = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=5).json()
            if res.get("IsTor"): print(f"{C.WHITE} [✓] Sikker routing aktiv (Exit: {res.get('IP')}){C.RESET}")
            else: print(f"{C.RED} [!] Sikker routing DEAKTIVERET. Tjek Tor proxy.{C.RESET}")
        except Exception:
            print(f"{C.RED} [!] Proxy-forbindelse fejlede.{C.RESET}")

        if vault: print(f"{C.WHITE} [✓] Kryptografisk Vault online.{C.RESET}")
        else: print(f"{C.RED} [!] Vault Offline. Opererer usikret.{C.RESET}")
        time.sleep(1)

# ==========================================
# 🔹 BACKGROUND JOB MANAGER
# ==========================================
class BackgroundJobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start_job(self, mod_id: str, target: str, module_instance, is_background: bool = False):
        job_id = str(uuid.uuid4())[:8]
        
        def job_runner():
            with self.lock:
                self.jobs[job_id] = {"status": "Aktiv", "module": module_instance.name, "target": target, "start": datetime.now()}
            try:
                browser_cfg = BrowserConfig(headless=True, anti_detection=True)
                browser = OmniHunterBrowser(browser_cfg)
                browser.start()
                try: module_instance.run(browser, target)
                finally: browser.close()
                
                with self.lock: self.jobs[job_id]["status"] = "Fuldført"
                if is_background: print(f"\n{C.GREEN}[+] Opgave [{job_id}] fuldført!{C.RESET}")
            except Exception as e:
                with self.lock: self.jobs[job_id]["status"] = f"Fejl: {str(e)}"
                logger.error(f"Job {job_id} fejlede: {e}\n{traceback.format_exc()}")
                print(f"\n{C.RED}[!] Opgave [{job_id}] afbrudt: {str(e)}{C.RESET}")

        thread = threading.Thread(target=job_runner, daemon=True)
        thread.start()
        
        if is_background: print(f"{C.RED}[*] Opgave startet asynkront. ID: {job_id}{C.RESET}")
        else: thread.join()

    def list_jobs(self):
        print(f"\n{C.RED}--- [ OPERATIONSOVERSIGT ] ---{C.RESET}")
        with self.lock:
            if not self.jobs: print(f"{C.DIM}Ingen aktive opgaver.{C.RESET}")
            for j_id, j_data in self.jobs.items():
                col = C.GREEN if j_data["status"] == "Fuldført" else (C.WHITE if j_data["status"] == "Aktiv" else C.RED)
                print(f"[{j_id}] {j_data['module']} -> {j_data['target']} | Status: {col}{j_data['status']}{C.RESET}")

# ==========================================
# 🔹 WORKSPACE MANAGER
# ==========================================
class WorkspaceManager:
    def __init__(self):
        self.base_dir = Path("workspaces")
        self.base_dir.mkdir(exist_ok=True)
        self.current_workspace = "standard_sag"
        self._set_workspace("standard_sag")

    def _set_workspace(self, name: str):
        safe_name = military_sanitize_input(name).replace(" ", "_").lower()
        self.current_workspace = safe_name
        ws_dir = self.base_dir / safe_name
        ws_dir.mkdir(exist_ok=True)
        session["loot_folder"] = str(ws_dir)
        session["workspace"] = safe_name
        print(f"{C.RED}[+] Operativ sag sat til: {safe_name.upper()}{C.RESET}")

    def list_workspaces(self):
        print(f"\n{C.RED}--- [ AKTIVE SAGER ] ---{C.RESET}")
        for ws in self.base_dir.iterdir():
            if ws.is_dir():
                marker = "*" if ws.name == self.current_workspace else " "
                print(f" [{marker}] {ws.name.upper()}")

# ==========================================
# 🔹 APEX COMMAND SHELL (PET FE EXECUTIVE)
# ==========================================
class GoliathShell:
    def __init__(self):
        if ModuleManager:
            self.module_manager = ModuleManager("modules")
            self.module_manager.discover()
        else:
            self.module_manager = FallbackModuleManager()
            
        self.job_manager = BackgroundJobManager()
        self.workspace_manager = WorkspaceManager()
        self.current_target = None

    def prompt(self):
        target_str = f" {C.WHITE}[{self.current_target}]{C.RESET}" if self.current_target else ""
        return f"\n{C.RED}PETFE{C.RESET}({C.DIM}{self.workspace_manager.current_workspace}{C.RESET}){target_str} > "

    def print_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        # Klinisk, autoritært PET FE banner (Ingen ASCII kunst)
        banner = f"""{C.RED}████████████████████████████████████████████████████████████████████████
[ PET FE ] POLITIETS EFTERRETNINGSTJENESTE - FREMSKUDT EFTERFORSKNING
========================================================================
SYSTEM: OMNI_HUNTER ORCHESTRATOR 
STATUS: RESTRICTED // AUTHORIZED PERSONNEL ONLY
████████████████████████████████████████████████████████████████████████{C.RESET}"""
        print(banner)

    def cmd_loop(self):
        self.print_banner()
        GoliathDiagnostics.run_pre_flight_checks()
        
        while True:
            try:
                cmd_raw = input(self.prompt()).strip()
                if not cmd_raw: continue
                
                audit_logger.log_command(cmd_raw)
                
                cmd_input = cmd_raw.split()
                cmd = cmd_input[0].lower()
                args = cmd_input[1:]

                # --- ALIAS ENGINE (NEMMERE KOMMANDOER) ---
                if cmd in ["exit", "quit", "q"]:
                    print(f"{C.RED}[*] Sikrer databaser og afslutter system...{C.RESET}")
                    break
                elif cmd == "help":
                    self.show_help()
                elif cmd == "clear":
                    self.print_banner()
                elif cmd in ["modules", "tools", "ls"]:
                    self.module_manager.display_dynamic_menu()
                elif cmd == "target":
                    if not args:
                        print(f"{C.YELLOW}[!] Fejl: Angiv et mål. Eksempel: target John Doe{C.RESET}")
                        continue
                    self.current_target = military_sanitize_input(" ".join(args))
                    session["name"] = self.current_target
                    print(f"{C.RED}[+] Mål fastlåst: {self.current_target}{C.RESET}")
                elif cmd == "case" or cmd == "workspace":
                    if args: self.workspace_manager._set_workspace(args[0])
                    else: self.workspace_manager.list_workspaces()
                elif cmd == "jobs":
                    self.job_manager.list_jobs()
                elif cmd == "scan":
                    # Alias for 'run auto'
                    args.insert(0, "auto")
                    self.execute_cmd(args)
                elif cmd == "run":
                    self.execute_cmd(args)
                elif cmd == "report":
                    print(f"{C.RED}[*] Genererer analyserapport for sag: {self.workspace_manager.current_workspace}...{C.RESET}")
                    AutomatedCaseReporter().generate()
                else:
                    print(f"{C.YELLOW}[!] Ukendt kommando. Skriv 'help'.{C.RESET}")

            except KeyboardInterrupt:
                print(f"\n{C.YELLOW}[*] Afbrudt. Skriv 'exit' for at lukke ned.{C.RESET}")
            except Exception as e:
                logger.error(f"Shell Fejl: {e}\n{traceback.format_exc()}")
                print(f"{C.RED}[!] Systemfejl: {e}{C.RESET}")

    def show_help(self):
        print(f"\n{C.RED}--- [ KOMMANDOOVERSIGT ] ---{C.RESET}")
        print(f" {C.WHITE}target <navn>{C.RESET}  Fastlås mål (Navn, IP, CVR, Email)")
        print(f" {C.WHITE}scan{C.RESET}           Start autonom kortlægning på fastlåst mål")
        print(f" {C.WHITE}scan -bg{C.RESET}       Kør scanning asynkront i baggrunden")
        print(f" {C.WHITE}modules{C.RESET}        Viser alle manuelle indsamlingsværktøjer")
        print(f" {C.WHITE}run <id>{C.RESET}       Start specifikt modul (eks: 'run 04')")
        print(f" {C.WHITE}case <navn>{C.RESET}    Opret eller skift sagsmappe (workspace)")
        print(f" {C.WHITE}jobs{C.RESET}           Se status på baggrundsopgaver")
        print(f" {C.WHITE}report{C.RESET}         Generér interaktiv efterretningsrapport (HTML)")

    def execute_cmd(self, args):
        if not args:
            print(f"{C.YELLOW}[!] Angiv hvad der skal køres.{C.RESET}")
            return

        mod_id = args[0]
        is_bg = "-bg" in args or "--bg" in args

        if not self.current_target:
            print(f"{C.YELLOW}[!] Intet mål valgt. Brug 'target <navn>' først.{C.RESET}")
            return

        if mod_id.lower() == "auto": mod_id = "30"

        if isinstance(self.module_manager, FallbackModuleManager):
            print(f"{C.RED}[!] Fallback Mode: Modul-eksekvering kræver core/module_manager.py.{C.RESET}")
            return

        module = self.module_manager.get_module(mod_id)
        if not module:
            print(f"{C.YELLOW}[!] Værktøj '{mod_id}' findes ikke.{C.RESET}")
            return
        if not module.check_requirements(): return

        self.job_manager.start_job(mod_id, self.current_target, module, is_background=is_bg)

# ==========================================
# 🔹 CLI PIPELINE
# ==========================================
def run_pipeline(args):
    ws = WorkspaceManager()
    jm = BackgroundJobManager()
    mm = ModuleManager("modules") if ModuleManager else None
    if not mm: return
        
    mm.discover()
    target = military_sanitize_input(args.target)
    session["name"] = target

    mod_list = ["30"] if args.auto else [m.strip() for m in args.modules.split(",")]
    
    for m_id in mod_list:
        module = mm.get_module(m_id)
        if module and module.check_requirements():
            jm.start_job(m_id, target, module, is_background=False)
            
    AutomatedCaseReporter().generate()

def main():
    parser = argparse.ArgumentParser(description="PET FE - OSINT Framework")
    parser.add_argument("-t", "--target", help="Mål", type=str)
    parser.add_argument("-m", "--modules", help="Moduler (fx '01,04')", type=str)
    parser.add_argument("--auto", action="store_true", help="Kør autonom scanning")
    args = parser.parse_args()

    if args.target and (args.modules or args.auto): run_pipeline(args)
    else:
        shell = GoliathShell()
        shell.cmd_loop()

if __name__ == "__main__":
    main()