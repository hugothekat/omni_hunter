# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - THE APEX ORCHESTRATOR (main.py) v3.0
📌 Formål: Centralt kontrolcenter der integrerer Vault, Nexus, Async Netværk og Dynamiske Moduler.
🔧 Features:
   - Dynamic Module Loading (Auto-Discovery menu)
   - Async Event Loop Bootstrapping (Forhindrer thread-crashes)
   - Secure Vault Initialization (Indlæser API nøgler i RAM før start)
   - Advanced CLI Pipeline (Kør flere moduler i kæde via terminal)
   - Interactive D3.js / Vis.js Case Reporter (Visuel Graf)
   - Graceful Degradation & Global Exception Hooking
"""

import os
import sys
import shutil
import argparse
import json
import asyncio
import threading
import time
from pathlib import Path
from datetime import datetime
import traceback

# --- GOLIATH CORE INTEGRATIONER ---
try:
    from core.utils import C, session, get_input, military_sanitize_input
    from core.browser import OmniHunterBrowser, BrowserConfig
    from core.logger import logger
    
    # Nye systemer (Sikrer graceful fallback hvis de ikke er oprettet endnu)
    try:
        from core.config_vault import vault
    except ImportError:
        vault = None
        logger.warning("Vault system ikke fundet. Kører i legacy mode.")

    try:
        from core.module_manager import ModuleManager
    except ImportError:
        ModuleManager = None

    try:
        from core.nexus import nexus
    except ImportError:
        nexus = None

except ImportError as e:
    print(f"\033[91m[!] KRITISK FEJL: Core-komponenter mangler. Fejl: {e}\033[0m")
    sys.exit(1)

# ==========================================
# 🔹 SYSTEM BOOTSTRAPPER & VALIDATOR
# ==========================================
class GoliathCommandCenter:
    def __init__(self):
        self.loot_dir = Path("loot_evidence")
        self.loot_dir.mkdir(exist_ok=True)
        session["loot_folder"] = str(self.loot_dir)
        
        self.module_manager = ModuleManager("modules") if ModuleManager else None
        if self.module_manager:
            self.module_manager.discover()
            
        self._check_dependencies()
        self._init_async_loop()

    def _check_dependencies(self):
        """Militært tjek af maskinrummet før opsendelse."""
        tools = {
            "rg": "Ripgrep (Offline Databaser)", 
            "tesseract": "Tesseract OCR (Billedtekst)", 
            "exiftool": "ExifTool (OPSEC)",
            "nmap": "Nmap (Aktiv Netværksscanning)"
        }
        missing = []
        for tool, desc in tools.items():
            if shutil.which(tool) is None:
                missing.append(desc)
        
        if missing:
            print(f"\n{C.YELLOW}[!] ADVARSEL: Følgende systemværktøjer mangler:{C.RESET}")
            for m in missing:
                print(f"{C.YELLOW}    - {m}{C.RESET}")
            print(f"{C.DIM}    Nogle moduler vil have nedsat funktionalitet. Kør install_deps.sh{C.RESET}\n")
            time.sleep(2)

    def _init_async_loop(self):
        """Sikrer at alle moduler har adgang til et validt event loop, selv i tråde."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        self.loop = loop

    def execute_module(self, mod_id: str, target: str):
        """Dynamisk eksekvering af moduler med isolation."""
        if not self.module_manager:
            print(f"{C.RED}[!] ModuleManager er ikke aktiv. Gå til manuel routing.{C.RESET}")
            return False

        module = self.module_manager.get_module(mod_id)
        if not module:
            print(f"{C.RED}[!] Modul {mod_id} findes ikke i systemet.{C.RESET}")
            return False

        if not module.check_requirements():
            return False

        try:
            sanitized_target = military_sanitize_input(target)
            print(f"\n{C.MAGENTA}[*] Initialiserer [{mod_id}] {module.name} mod: {sanitized_target}{C.RESET}")
            
            # Klargør Browser (Headless som standard for moduler der skal bruge det)
            browser_cfg = BrowserConfig(headless=True, anti_detection=True)
            browser = OmniHunterBrowser(browser_cfg)
            browser.start()
            
            try:
                # Moduler skal designes til at modtage (browser_instance, target)
                module.run(browser, sanitized_target)
            finally:
                browser.close()
                
            return True
            
        except Exception as e:
            logger.error(f"Kritisk fejl i modul {mod_id}", error=str(e), traceback=traceback.format_exc())
            print(f"\n{C.BG_RED}{C.WHITE} [!] NEDBRUD I MODUL {mod_id}: {str(e)} {C.RESET}")
            return False

# ==========================================
# 🔹 INTERACTIVE HTML CASE REPORTER (V3)
# ==========================================
class AutomatedCaseReporter:
    """GOLIATH V3: Genererer et interaktivt HTML Dashboard med D3.js netværksgrafer!"""
    def __init__(self):
        self.loot_dir = Path(session.get("loot_folder", "loot_evidence"))
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.report_file = self.loot_dir / f"SAGSRAPPORT_{self.timestamp}.html"

    def _build_graph_data(self, files) -> str:
        """Bygger Nodes og Edges til Vis.js baseret på JSON dumps og Nexus-data."""
        nodes = []
        edges = []
        node_ids = set()
        
        def add_node(n_id, label, group):
            if n_id not in node_ids:
                nodes.append({"id": n_id, "label": label, "group": group})
                node_ids.add(n_id)

        # Hvis Nexus er aktiv (Fase 2), brug dens data direkte
        if nexus and nexus.graph:
            for node_val, meta in nexus.graph.items():
                add_node(node_val, str(node_val), meta['type'])
                for link_val, relation in meta['linked_entities']:
                    add_node(link_val, str(link_val), "linked")
                    edges.append({"from": node_val, "to": link_val, "label": relation})
        else:
            # Fallback til grov fil-parsing
            target_node = session.get('name', 'Ukendt_Target')
            add_node(target_node, target_node, "Target")
            
            for f in files:
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                    if "Email" in data:
                        add_node(data["Email"], data["Email"], "Email")
                        edges.append({"from": target_node, "to": data["Email"], "label": "Ejer"})
                    if "Telefonnumre" in data:
                        for t in data["Telefonnumre"]:
                            add_node(t, t, "Phone")
                            edges.append({"from": target_node, "to": t, "label": "Bruger"})
                except: pass

        return json.dumps({"nodes": nodes, "edges": edges})

    def generate(self):
        print(f"\n{C.CYAN}[*] Kompilerer Interaktiv Sagsrapport (Vis.js Graph Engine)...{C.RESET}")
        files = list(self.loot_dir.glob("*.json"))
        
        # Samledata
        all_emails, all_phones, all_usernames = set(), set(), set()
        for f in files:
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                if "Email" in data: all_emails.add(data["Email"])
                if "Telefonnumre" in data: all_phones.update(data["Telefonnumre"])
            except: pass

        graph_json = self._build_graph_data(files)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>GOLIATH // TACTICAL DASHBOARD</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2f; color: #cfd2d9; margin: 0; padding: 20px; }}
                h1 {{ color: #00e5ff; border-bottom: 2px solid #3b3b54; padding-bottom: 10px; }}
                .grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }}
                .box {{ background: #27293d; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-left: 4px solid #00e5ff; }}
                #mynetwork {{ width: 100%; height: 600px; border: 1px solid #3b3b54; background-color: #1a1a24; border-radius: 8px; }}
                .badge {{ background: #ff007f; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ background: #1e1e2f; margin: 5px 0; padding: 10px; border-radius: 4px; border: 1px solid #3b3b54; }}
            </style>
        </head>
        <body>
            <h1>GOLIATH APEX // INTERACTIVE CASE REPORT</h1>
            <p>Genereret: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="grid">
                <div>
                    <div class="box">
                        <h2>Identifikatorer</h2>
                        <p><strong>Emails <span class="badge">{len(all_emails)}</span></strong></p>
                        <ul>{''.join([f"<li>{e}</li>" for e in all_emails]) if all_emails else "<li>Ingen data</li>"}</ul>
                        <p><strong>Telefoner <span class="badge">{len(all_phones)}</span></strong></p>
                        <ul>{''.join([f"<li>+45 {p}</li>" for p in all_phones]) if all_phones else "<li>Ingen data</li>"}</ul>
                    </div>
                    <div class="box">
                        <h2>Bevismateriale ({len(files)} filer)</h2>
                        <ul style="max-height: 250px; overflow-y: auto;">
                            {''.join([f"<li style='border-left: 2px solid #2ecc71;'>{f.name}</li>" for f in files])}
                        </ul>
                    </div>
                </div>
                
                <div class="box" style="border-left: 4px solid #ff007f;">
                    <h2>Relational Intelligence Network (Vis.js)</h2>
                    <div id="mynetwork"></div>
                </div>
            </div>

            <script type="text/javascript">
                var graphData = {graph_json};
                var container = document.getElementById('mynetwork');
                var data = {{
                    nodes: new vis.DataSet(graphData.nodes),
                    edges: new vis.DataSet(graphData.edges)
                }};
                var options = {{
                    nodes: {{ shape: 'dot', size: 20, font: {{ color: '#cfd2d9' }} }},
                    edges: {{ font: {{ color: '#cfd2d9', align: 'middle' }}, arrows: 'to' }},
                    physics: {{ stabilization: true, barnesHut: {{ springLength: 200 }} }}
                }};
                var network = new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """

        self.report_file.write_text(html_content, encoding='utf-8')
        print(f"{C.GREEN}[✓] Interaktiv Sagsrapport genereret!{C.RESET}")
        print(f"{C.CYAN}    -> Åbn filen i din browser: {self.report_file.absolute()}{C.RESET}")


# ==========================================
# 🔹 CLI & MAIN MENU ROUTING
# ==========================================
def setup_cli():
    parser = argparse.ArgumentParser(description="PETFE GOLIATH - Advanced OSINT Framework")
    parser.add_argument("-t", "--target", help="Målets navn, email eller IP", type=str)
    parser.add_argument("-m", "--modules", help="Kommasepareret liste af moduler (fx '01,04,17')", type=str)
    parser.add_argument("--auto", action="store_true", help="Kør autonom omni-pivot skanning (Modul 00/30)")
    return parser.parse_args()

def display_menu(cmd_center: GoliathCommandCenter):
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = f"""{C.WHITE}{C.BOLD}
===========================================================================
 🦅 GOLIATH APEX ORCHESTRATOR // CENTRAL INTELLIGENCE COMMAND
===========================================================================
{C.RESET}"""
    print(banner)

    if vault and vault.get("system_settings"):
        mode = vault.get("system_settings", "operator_mode")
        print(f"{C.DIM} Vault Security: ENABLED | Mode: {mode} | Core: V36 {C.RESET}\n")

    print(f"{C.BG_RED}{C.WHITE} [00] THE GRAND ORCHESTRATOR (Autonom Identitets-Opløsning) {C.RESET}\n")

    if cmd_center.module_manager:
        cmd_center.module_manager.display_dynamic_menu()
    else:
        print(f"{C.RED}[!] ModuleManager nede. Tjek core/module_manager.py.{C.RESET}")

    print(f"\n{C.CYAN}--- [ SYSTEM & REPORTING ] ------------------------------------------------{C.RESET}")
    print(f" {C.GREEN}[14]{C.RESET} Generér Interaktiv Sagsrapport (HTML/D3.js)")
    
    print(f"\n{C.DIM}" + "-" * 75 + f"{C.RESET}")
    print(f" {C.RED}[99] Afslut System{C.RESET}")

def main():
    args = setup_cli()
    cmd_center = GoliathCommandCenter()

    # --- CLI PIPELINE MODE (Hvis argumenter er givet i terminalen) ---
    if args.target:
        session["name"] = args.target
        if args.auto:
            print(f"{C.CYAN}[*] Initiating CLI Autonomous Mode against {args.target}...{C.RESET}")
            # Kald Modul 30 direkte
            cmd_center.execute_module("30", args.target)
            AutomatedCaseReporter().generate()
            return
            
        if args.modules:
            mod_list = [m.strip() for m in args.modules.split(",")]
            for m_id in mod_list:
                cmd_center.execute_module(m_id, args.target)
            AutomatedCaseReporter().generate()
            return

    # --- INTERACTIVE MENU MODE ---
    while True:
        display_menu(cmd_center)
        
        try:
            choice = input(f"\n{C.YELLOW}Vælg Handling [00-99]: {C.RESET}").strip()
            
            if choice == "99" or choice.lower() in ['q', 'exit', 'quit']: 
                print(f"\n{C.RED}[*] Gemmer Vault State. Sletter midlertidige spor. System afsluttet.{C.RESET}")
                break

            if choice in ["00", "0"]:
                target = get_input("Målets fulde navn/ID", "name")
                cmd_center.execute_module("30", target) # Auto-ruter til Modul 30 Orchestrator

            elif choice == "14":
                AutomatedCaseReporter().generate()

            else:
                # Dynamisk routing til det valgte modul
                target_map = {
                    "01": "Navn/By", "02": "Firma/CVR", "03": "Email", "04": "Brugernavn",
                    "10": "IP/Domæne", "12": "Telefon", "19": "Krypto Adresse", "20": "Nummerplade",
                    "21": "MAC Adresse"
                }
                
                # Prøv at hente target beskrivelse, ellers brug "Target"
                target_prompt = target_map.get(choice, "Indtast Mål/Target")
                target = get_input(target_prompt, "target")
                
                success = cmd_center.execute_module(choice, target)
                if not success:
                    print(f"{C.RED}[!] Kunne ikke eksekvere modul (Findes det, eller opstod en fejl?){C.RESET}")

            input(f"\n{C.DIM}Tryk ENTER for at vende tilbage til kontrolcenteret...{C.RESET}")

        except KeyboardInterrupt:
            print(f"\n{C.RED}[!] Proces afbrudt af operatør (Ctrl+C). Standser asynkrone tråde.{C.RESET}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Kritisk systemfejl i menuen: {e}")
            print(f"\n{C.BG_RED}{C.WHITE}[!] KRITISK ORCHESTRATOR FEJL:{C.RESET} {str(e)}")
            input(f"\n{C.DIM}Tryk ENTER for at genindlæse miljøet...{C.RESET}")

if __name__ == "__main__":
    main()