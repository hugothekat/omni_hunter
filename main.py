# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - THE APEX ORCHESTRATOR & TUI SHELL (main.py) v6.0 (PET-FE EXECUTIVE)
📌 Formål: Asynkront, professionelt kontrolcenter for PETFE OSINT operationer.
🔧 Features (V6.0 OVERHAUL):
   - Government-Grade 'Rich' TUI (Tables, Panels, Live Layouts)
   - Prompt-Toolkit Auto-Completion & Command History
   - Cryptographic Blockchain Audit Logging (SHA-256 Chain of Custody)
   - Real-time System Telemetry (CPU, RAM, Tor Status)
   - Thread-safe Background Job Manager med visuel status
"""

import os
import sys
import shutil
import argparse
import threading
import time
import requests
import hashlib
import uuid
import importlib.util
import inspect
import traceback
from pathlib import Path
from datetime import datetime

# --- AUTO-HEAL DEPENDENCY INJECTION FOR UI ---
def ensure_ui_deps():
    missing = []
    try: import rich
    except ImportError: missing.append("rich")
    try: import prompt_toolkit
    except ImportError: missing.append("prompt_toolkit")
    try: import psutil
    except ImportError: missing.append("psutil")
    
    if missing:
        print(f"\033[93m[*] Auto-installerer kritiske UI-afhængigheder: {', '.join(missing)}\033[0m")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing], stdout=subprocess.DEVNULL)
ensure_ui_deps()

# --- IMPORTER UI BIBLIOTEKER ---
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich import print as rprint
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
import psutil

# Instansier global Rich Console
console = Console()

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
    console.print(Panel(f"[bold red]KRITISK FEJL: Core-komponenter mangler.[/bold red]\nFejl: {e}", title="SYSTEM FAILURE"))
    sys.exit(1)

# ==========================================
# 🔹 COMPLIANCE AUDIT LOGGER (V6.0: SHA-256 CHAIN OF CUSTODY)
# ==========================================
class ComplianceAuditLogger:
    """Sikrer en ubrudt, kryptografisk kæde af operatørens handlinger."""
    def __init__(self):
        self.log_file = Path("compliance_audit.log")
        self.last_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        
        if not self.log_file.exists():
            self._write_log("SYSTEM_BOOT", "Audit Log Initialized (V6.0 Cryptographic Mode)")
        else:
            # Læs den sidste hash for at bevare blockchain-kæden
            try:
                with open(self.log_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        self.last_hash = last_line.split(" | CHK:")[-1].strip()
            except: pass

    def _write_log(self, action: str, details: str):
        timestamp = datetime.now().isoformat()
        operator = os.getlogin() if hasattr(os, 'getlogin') else "UNKNOWN_OPERATOR"
        
        raw_entry = f"[{timestamp}] OP:{operator} | ACT:{action} | DET:{details}"
        # SHA-256 Hash chaining (som blockchain) sikrer mod sletning af midterste logs
        hash_input = f"{self.last_hash}{raw_entry}".encode('utf-8')
        checksum = hashlib.sha256(hash_input).hexdigest()
        self.last_hash = checksum
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{raw_entry} | CHK:{checksum}\n")

    def log_command(self, cmd: str):
        self._write_log("COMMAND_EXECUTION", f"Command: '{cmd}'")

audit_logger = ComplianceAuditLogger()

# ==========================================
# 🔹 DIAGNOSTICS & SYSTEM BOOT
# ==========================================
class GoliathDiagnostics:
    @staticmethod
    def run_pre_flight_checks():
        table = Table(title="PET FE DIAGNOSTIC CHECK", style="cyan")
        table.add_column("Komponent", justify="left", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Detaljer", justify="left", style="dim")

        # Systemværktøjer
        tools = {"rg": "Ripgrep", "tesseract": "Tesseract OCR", "exiftool": "ExifTool", "nmap": "Nmap"}
        missing = [desc for tool, desc in tools.items() if shutil.which(tool) is None]
        if missing:
            table.add_row("System Værktøjer", "[red]ADVARSEL[/red]", f"Mangler: {', '.join(missing)}")
        else:
            table.add_row("System Værktøjer", "[green]VERIFICERET[/green]", "Alle OSINT binaries til stede")

        # Routing (Tor)
        try:
            proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
            res = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=5).json()
            if res.get("IsTor"):
                table.add_row("Sikker Routing", "[green]AKTIV[/green]", f"Exit Node IP: {res.get('IP')}")
            else:
                table.add_row("Sikker Routing", "[red]DEAKTIVERET[/red]", "Trafik rutes via ClearNet")
        except Exception:
            table.add_row("Sikker Routing", "[red]OFFLINE[/red]", "Proxy forbindelse fejlede")

        # Vault
        if vault:
            table.add_row("Kryptografisk Vault", "[green]ONLINE[/green]", "AES-256 Kryptering Aktiv")
        else:
            table.add_row("Kryptografisk Vault", "[red]OFFLINE[/red]", "Opererer med usikret klartekst")

        console.print(table)
        time.sleep(1)

# ==========================================
# 🔹 BACKGROUND JOB MANAGER
# ==========================================
class BackgroundJobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start_job(self, mod_id: str, target: str, module_instance, is_background: bool = False):
        job_id = str(uuid.uuid4())[:6].upper()
        
        def job_runner():
            with self.lock:
                self.jobs[job_id] = {"status": "[yellow]Kører[/yellow]", "module": module_instance.name, "target": target, "start": datetime.now()}
            try:
                browser_cfg = BrowserConfig(headless=True, anti_detection=True)
                browser = OmniHunterBrowser(browser_cfg)
                browser.start()
                try: module_instance.run(browser, target)
                finally: browser.close()
                
                with self.lock: self.jobs[job_id]["status"] = "[green]Fuldført[/green]"
                if is_background: console.print(f"\n[bold green]\[+] Opgave \\[{job_id}] fuldført![/bold green]")
            except Exception as e:
                with self.lock: self.jobs[job_id]["status"] = f"[red]Fejl[/red]"
                logger.error(f"Job {job_id} fejlede: {e}\n{traceback.format_exc()}")
                if is_background: console.print(f"\n[bold red]\[!] Opgave \\[{job_id}] afbrudt: {str(e)}[/bold red]")

        thread = threading.Thread(target=job_runner, daemon=True)
        thread.start()
        
        if is_background: 
            console.print(f"[bold cyan][*] Opgave startet asynkront. ID: {job_id}[/bold cyan]")
        else: 
            thread.join()

    def display_jobs(self):
        table = Table(title="AKTIVE OPERATIONER", style="magenta")
        table.add_column("Job ID", style="cyan")
        table.add_column("Modul", style="white")
        table.add_column("Target", style="yellow")
        table.add_column("Status", justify="center")

        with self.lock:
            if not self.jobs:
                console.print(Panel("[dim]Ingen aktive baggrundsopgaver.[/dim]", border_style="dim"))
                return
            for j_id, j_data in self.jobs.items():
                table.add_row(j_id, j_data['module'], j_data['target'], j_data['status'])
        
        console.print(table)

# ==========================================
# 🔹 WORKSPACE MANAGER
# ==========================================
class WorkspaceManager:
    def __init__(self):
        self.base_dir = Path("workspaces")
        self.base_dir.mkdir(exist_ok=True)
        self.current_workspace = "standard_sag"
        self._set_workspace("standard_sag", quiet=True)

    def _set_workspace(self, name: str, quiet=False):
        safe_name = military_sanitize_input(name).replace(" ", "_").lower()
        self.current_workspace = safe_name
        ws_dir = self.base_dir / safe_name
        ws_dir.mkdir(exist_ok=True)
        session["loot_folder"] = str(ws_dir)
        session["workspace"] = safe_name
        if not quiet:
            console.print(f"[bold green]\[+] Operativ sag sat til:[/bold green] [bold white]{safe_name.upper()}[/bold white]")

    def list_workspaces(self):
        table = Table(title="Sagsmapper (Workspaces)", style="blue")
        table.add_column("Status", justify="center")
        table.add_column("Sagsnavn", style="white")
        table.add_column("Sti", style="dim")

        for ws in sorted(self.base_dir.iterdir()):
            if ws.is_dir():
                marker = "[bold green]AKTIV[/bold green]" if ws.name == self.current_workspace else "[dim]Inaktiv[/dim]"
                table.add_row(marker, ws.name.upper(), str(ws.absolute()))
                
        console.print(table)

# ==========================================
# 🔹 APEX COMMAND SHELL (PET FE EXECUTIVE)
# ==========================================
class GoliathShell:
    def __init__(self):
        if ModuleManager:
            self.module_manager = ModuleManager("modules")
            self.module_manager.discover()
        else:
            console.print("[bold red][!] Core ModuleManager mangler. System ustabilt.[/bold red]")
            sys.exit(1)
            
        self.job_manager = BackgroundJobManager()
        self.workspace_manager = WorkspaceManager()
        self.current_target = None
        
        # Opretter en intelligent WordCompleter til TUI'en
        commands = ['target', 'scan', 'modules', 'run', 'case', 'workspace', 'jobs', 'report', 'clear', 'exit', 'help']
        self.completer = WordCompleter(commands, ignore_case=True)
        
        # Prompt Style
        self.style = Style.from_dict({
            'prompt': 'ansired bold',
            'workspace': 'ansicyan',
            'target': 'ansiyellow bold',
            'pointer': 'ansiwhite bold'
        })
        self.prompt_session = PromptSession(completer=self.completer, style=self.style)

    def render_system_header(self):
        """Tegner det professionelle dashboard i toppen af skærmen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Telemetry
        ram_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        ram_color = "red" if ram_usage > 85 else "green"
        cpu_color = "red" if cpu_usage > 85 else "green"
        
        target_display = self.current_target if self.current_target else "INTET MÅL LÅST"
        target_color = "bold yellow" if self.current_target else "dim"

        header_text = f"""[bold red]████████████████████████████████████████████████████████████████████████[/bold red]
[bold white]POLITIETS EFTERRETNINGSTJENESTE[/bold white] [dim]- FREMSKUDT EFTERFORSKNING (PET FE)[/dim]
[bold red]████████████████████████████████████████████████████████████████████████[/bold red]

[cyan]SYSTEM:[/cyan] GOLIATH OMNI_HUNTER V6.0
[cyan]SAGSMAPPE:[/cyan] [bold white]{self.workspace_manager.current_workspace.upper()}[/bold white]
[cyan]FASTLÅST MÅL:[/cyan] [{target_color}]{target_display}[/{target_color}]
[cyan]TELEMETRI:[/cyan] CPU: [{cpu_color}]{cpu_usage}%[/{cpu_color}] | RAM: [{ram_color}]{ram_usage}%[/{ram_color}] | VÆRKTØJER: [green]{len(self.module_manager.modules)} Aktive[/green]"""

        console.print(Panel(header_text, border_style="red", padding=(0, 2)))

    def get_prompt_text(self):
        # Bygger en farvekodet prompt line
        target_str = f" [{self.current_target}]" if self.current_target else ""
        return [
            ('class:prompt', 'PETFE'),
            ('class:pointer', '('),
            ('class:workspace', f'{self.workspace_manager.current_workspace}'),
            ('class:pointer', ')'),
            ('class:target', target_str),
            ('class:pointer', ' > ')
        ]

    def cmd_loop(self):
        self.render_system_header()
        GoliathDiagnostics.run_pre_flight_checks()
        
        while True:
            try:
                # Anvender PromptSession til autocompletion og command history
                cmd_raw = self.prompt_session.prompt(self.get_prompt_text())
                if not cmd_raw.strip(): continue
                
                audit_logger.log_command(cmd_raw)
                
                cmd_input = cmd_raw.split()
                cmd = cmd_input[0].lower()
                args = cmd_input[1:]

                # --- COMMAND DISPATCHER ---
                if cmd in ["exit", "quit", "q"]:
                    console.print("[bold red][*] Sikrer databaser og afslutter system...[/bold red]")
                    break
                elif cmd == "help":
                    self.show_help()
                elif cmd == "clear":
                    self.render_system_header()
                elif cmd in ["modules", "tools", "ls"]:
                    self._render_modules_table()
                elif cmd == "target":
                    if not args:
                        console.print("[bold yellow][!] Fejl: Angiv et mål. Eksempel: target John Doe[/bold yellow]")
                        continue
                    self.current_target = military_sanitize_input(" ".join(args))
                    session["name"] = self.current_target
                    console.print(f"[bold green]\[+] Mål fastlåst:[/bold green] [bold white]{self.current_target}[/bold white]")
                    self.render_system_header() # Opdaterer visuelt
                elif cmd in ["case", "workspace"]:
                    if args: 
                        self.workspace_manager._set_workspace(args[0])
                        self.render_system_header()
                    else: 
                        self.workspace_manager.list_workspaces()
                elif cmd == "jobs":
                    self.job_manager.display_jobs()
                elif cmd == "scan":
                    args.insert(0, "auto")
                    self.execute_cmd(args)
                elif cmd == "run":
                    self.execute_cmd(args)
                elif cmd == "report":
                    console.print(f"[bold cyan][*] Genererer analyserapport for sag: {self.workspace_manager.current_workspace}...[/bold cyan]")
                    AutomatedCaseReporter().generate()
                else:
                    console.print(f"[bold yellow][!] Ukendt kommando '{cmd}'. Skriv 'help' for oversigt.[/bold yellow]")

            except KeyboardInterrupt:
                console.print("\n[dim][*] Tryk Ctrl+D eller skriv 'exit' for at lukke ned.[/dim]")
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Shell Fejl: {e}\n{traceback.format_exc()}")
                console.print(f"[bold red][!] Kritisk Systemfejl: {e}[/bold red]")

    def _render_modules_table(self):
        """Viser moduler i en flot, professionel tabel"""
        table = Table(title="OPERATIONELT VÆRKTØJSARSENAL", style="red")
        table.add_column("ID", style="cyan", justify="center")
        table.add_column("Modul Navn", style="white")
        table.add_column("Status", justify="center")

        for mod_id, data in sorted(self.module_manager.modules.items()):
            table.add_row(mod_id, data['name'], "[green]AKTIV[/green]")
            
        console.print(table)
        
        if self.module_manager.quarantine:
            q_table = Table(title="VÆRKTØJER I KARANTÆNE", style="yellow")
            q_table.add_column("ID", style="red", justify="center")
            q_table.add_column("Fil", style="white")
            q_table.add_column("Fejlbeskrivelse", style="dim")
            
            for mod_id, data in sorted(self.module_manager.quarantine.items()):
                q_table.add_row(mod_id, data['file'], data['error'])
            
            console.print(q_table)

    def show_help(self):
        table = Table(title="KOMMANDOOVERSIGT", show_header=True, header_style="bold magenta")
        table.add_column("Kommando", style="cyan")
        table.add_column("Beskrivelse", style="white")
        
        table.add_row("target <navn>", "Fastlås mål (Navn, IP, CVR, Email)")
        table.add_row("scan", "Start autonom kortlægning (Orchestrator) på fastlåst mål")
        table.add_row("scan -bg", "Kør scanning asynkront i baggrunden")
        table.add_row("modules", "Viser alle aktive og karantæneramte moduler")
        table.add_row("run <id>", "Start specifikt modul manuelt (eks: 'run 04')")
        table.add_row("case <navn>", "Opret eller skift operativ sagsmappe (workspace)")
        table.add_row("jobs", "Se status på asynkrone baggrundsopgaver")
        table.add_row("report", "Generér interaktiv HTML efterretningsrapport")
        table.add_row("clear", "Rens skærmen og genindlæs dashboard")
        table.add_row("exit", "Sikr databaser og afslut")
        
        console.print(table)

    def execute_cmd(self, args):
        if not args:
            console.print("[bold yellow][!] Angiv hvilket modul der skal køres (eks. 'run 04' eller 'scan').[/bold yellow]")
            return

        mod_id = args[0]
        is_bg = "-bg" in args or "--bg" in args

        if not self.current_target:
            console.print("[bold yellow][!] Intet mål valgt. Brug 'target <navn>' først for at låse et mål.[/bold yellow]")
            return

        if mod_id.lower() == "auto": mod_id = "30"

        module = self.module_manager.get_module(mod_id)
        if not module:
            console.print(f"[bold yellow][!] Værktøj '{mod_id}' findes ikke eller er i karantæne.[/bold yellow]")
            return
            
        if not module.check_requirements(): 
            return

        self.job_manager.start_job(mod_id, self.current_target, module, is_background=is_bg)

# ==========================================
# 🔹 CLI PIPELINE (For Headless Execution)
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
    parser.add_argument("-t", "--target", help="Mål for headless kørsel", type=str)
    parser.add_argument("-m", "--modules", help="Moduler (fx '01,04')", type=str)
    parser.add_argument("--auto", action="store_true", help="Kør autonom scanning headless")
    args = parser.parse_args()

    if args.target and (args.modules or args.auto): 
        run_pipeline(args)
    else:
        shell = GoliathShell()
        shell.cmd_loop()

if __name__ == "__main__":
    main()