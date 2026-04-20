# main.py
import os
import sys
import shutil
import argparse
import json
from pathlib import Path
from datetime import datetime
from core.utils import C, session, get_input
from core.browser import get_stealth_driver
from core.logger import logger
from modules.mod_30_person_intel import PersonIntelligenceOrchestrator

def check_dependencies():
    print(f"{C.CYAN}[*] Udfører system-tjek for OMNI-HUNTER v52.0...{C.RESET}")
    tools = {"rg": "Ripgrep", "tesseract": "Tesseract OCR", "holehe": "Holehe Tracker"}
    for tool, desc in tools.items():
        if shutil.which(tool) is None:
            print(f"{C.RED}    [!] ADVARSEL: {desc} mangler på systemet!{C.RESET}")
        else:
            print(f"{C.GREEN}    [✓] System-Værktøj OK: {tool}{C.RESET}")

def setup_cli():
    parser = argparse.ArgumentParser(description="OMNI-HUNTER OSINT Framework")
    parser.add_argument("-t", "--target", help="Målets navn eller email")
    parser.add_argument("-m", "--module", help="Modulnummer", type=str)
    parser.add_argument("--headless", action="store_true", help="Kør uden menu")
    return parser.parse_args()

def main():
    os.makedirs(session["loot_folder"], exist_ok=True)
    check_dependencies()
    
    while True:
        print(f"{C.CYAN}{'='*70}{C.RESET}")
        print(f"  {C.YELLOW}OSINT Final - Suite for OSINT{C.RESET}")
        print(f"  {C.RED}PETFE // Politi - Efterretningsværktøj{C.RESET}")
        print(f"{C.CYAN}{'='*70}{C.RESET}")
        
        print(f"  {C.GREEN}[00] TOTAL PERSON PIVOT (Full Identity Reconstruction){C.RESET}")

        print(f"{C.CYAN}[01]{C.RESET} Personregister (Krak)          {C.CYAN}[02]{C.RESET} Erhverv (CVR API)")
        print(f"{C.CYAN}[03]{C.RESET} Lækage-analyse (Breach)        {C.CYAN}[04]{C.RESET} Social Media Profiler")
        print(f"{C.CYAN}[05]{C.RESET} Offline DB (Ripgrep)           {C.CYAN}[06]{C.RESET} E-mail Mønstre")
        print(f"{C.CYAN}[07]{C.RESET} Telefon-efterretning           {C.CYAN}[08]{C.RESET} Mørkenet (Ahmia)")
        print(f"{C.CYAN}[09]{C.RESET} E-mail Tracker (Dyb)           {C.CYAN}[10]{C.RESET} IP/Netværk (API)")
        print(f"{C.CYAN}[11]{C.RESET} Udtræk data fra billeder       {C.CYAN}[12]{C.RESET} Omvendt Telefonopslag")
        print(f"{C.CYAN}[13]{C.RESET} Omvendt Billedsøgning          {C.CYAN}[16]{C.RESET} Auto-Forensisk (TITAN)")
        print(f"{C.CYAN}[17]{C.RESET} Goliath Final Strike           {C.CYAN}[18]{C.RESET} Mail-Ripper (IMAP)")
        print(f"{C.CYAN}[19]{C.RESET} Crypto Ledger Tracker          {C.CYAN}[20]{C.RESET} Køretøjs-OSINT")
        print(f"{C.CYAN}[21]{C.RESET} BSSID Geofencer (MAC -> GPS)   {C.CYAN}[22]{C.RESET} Chat App Intelligence")
        print(f"{C.CYAN}[23]{C.RESET} Global Username Matrix         {C.CYAN}[24]{C.RESET} OPSEC Sanitizer")
        print(f"{C.CYAN}[25]{C.RESET} Wayback Machine                {C.CYAN}[26]{C.RESET} VirusTotal Threat Intel")
        print(f"{C.CYAN}[27]{C.RESET} AI Profilering (LLM)           {C.CYAN}[28]{C.RESET} Graph Exporter (Maltego)")
        print(f"{C.CYAN}[29]{C.RESET} Google Earth (KML Eksport)")
        
        print(f"{C.CYAN}{'-' * 70}{C.RESET}")
        print(f"{C.GREEN}[14]{C.RESET} Generer HTML Dashboard")
        print(f"{C.RED}[15]{C.RESET} Afslut Session")
        print(f"{C.CYAN}{'='*70}{C.RESET}")
        
        choice = input(f"\n{C.YELLOW}Vælg Modul [01-29]: {C.RESET}").strip()
        
        if choice == "15": 
            print(f"\n{C.RED}[*] Session afsluttet. God jagt.{C.RESET}")
            break

        # --- DYNAMISK ROUTING MED INTELLIGENT BROWSER-STYRING ---
        try:
            if choice == "00" or choice == "0":
                navn = get_input("Målets fulde navn", "name")
                print(f"{C.CYAN}[*] Starter GOLIATH PIVOT ENGINE...{C.RESET}")
                driver = get_stealth_driver()
                try:
                    PersonIntelligenceOrchestrator(navn).run(driver)
                finally:
                    driver.quit()

            elif choice == "01":
                from modules.mod_01_krak import DirectoryIntelligenceHunter
                navn = get_input("Navn", "name")
                by = get_input("By", "city")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: DirectoryIntelligenceHunter(navn, by).run(driver)
                finally: driver.quit()

            elif choice == "02":
                from modules.mod_02_business import BusinessIntelligenceAnalyst
                navn = get_input("Navn/Firma", "name")
                BusinessIntelligenceAnalyst(navn).run(None)

            elif choice == "03":
                from modules.mod_03_breach import BreachIntelligenceAnalyst
                email = get_input("Email", "email")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: BreachIntelligenceAnalyst(email).run(driver)
                finally: driver.quit()

            elif choice == "04":
                from modules.mod_04_social import SocialMediaProfiler
                username = get_input("Brugernavn", "username")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: SocialMediaProfiler(username).run(driver)
                finally: driver.quit()

            elif choice == "05":
                from modules.mod_05_offline import OfflineDatabaseAnalyzer
                OfflineDatabaseAnalyzer(get_input("Søgeord", "db_target"), get_input("Sti til .txt", "db_path")).run()

            elif choice == "06":
                from modules.mod_06_emailgen import EmailPatternGenerator
                navn = get_input("Navn", "name")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: EmailPatternGenerator(navn).run(driver)
                finally: driver.quit()

            elif choice == "07":
                from modules.mod_07_phone import PhoneIntelligenceHunter
                phone = get_input("Telefon (uden +45)", "phone")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: PhoneIntelligenceHunter(phone).run(driver)
                finally: driver.quit()

            elif choice == "08":
                from modules.mod_08_darkweb import DarkWebIntelligence
                DarkWebIntelligence(get_input("Søgeord", "dark_query")).run(None)

            elif choice == "09":
                from modules.mod_09_emailtrack import EmailTracker
                EmailTracker(get_input("Email", "email")).run(None)

            elif choice == "10":
                from modules.mod_10_ip import IPNetworkAnalyzer
                IPNetworkAnalyzer(get_input("IP Adresse", "ip")).run(None)

            elif choice == "11":
                from modules.mod_11_forensics import DigitalForensicsExaminer
                DigitalForensicsExaminer(get_input("Sti til billede/fil", "file_path")).run()

            elif choice == "12":
                from modules.mod_12_revphone import ReversePhoneIntelligence
                phone = get_input("Ukendt Telefon (uden +45)", "phone")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: ReversePhoneIntelligence(phone).run(driver)
                finally: driver.quit()

            elif choice == "13":
                from modules.mod_13_revimage import ReverseImageIntelligence
                img_path = get_input("Sti til billede", "image_path")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: ReverseImageIntelligence(img_path).run(driver)
                finally: driver.quit()

            elif choice == "16":
                from modules.mod_16_titan import AutoForensicMassScanner
                folder = get_input("Sti til Mappe (f.eks. /home/user/leaks)", "dump_folder")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: AutoForensicMassScanner(folder).run(driver)
                finally: driver.quit()

            elif choice == "17":
                from modules.mod_17_sniper import GoliathSniperEngine
                print(f"\n{C.YELLOW}--- GOLIATH SNIPER: KONFIGURATION ---{C.RESET}")
                name = get_input("Målets fulde navn", "name")
                city = get_input("By", "city")
                cpr = get_input("CPR (DDMMYY-XXXX)", "cpr") if input(f"{C.CYAN}Brug CPR? (j/n): {C.RESET}").lower() == 'j' else ""
                clues = get_input("Clues (f.eks. hund, børn)", "clues")
                GoliathSniperEngine(name, city, cpr, clues, session["loot_folder"]).generate()

            elif choice == "18":
                from modules.mod_18_mailrip import GoliathMailRipper
                print(f"\n{C.YELLOW}--- GOLIATH MAIL-RIPPER ---{C.RESET}")
                GoliathMailRipper(get_input("Email", "email"), get_input("App Password", "password")).run()

            elif choice == "19":
                from modules.mod_19_crypto import CryptoLedgerAnalyzer
                CryptoLedgerAnalyzer(get_input("Krypto Adresse (BTC/ETH)", "crypto")).run(None)

            elif choice == "20":
                from modules.mod_20_vehicle import VehicleIntelligence
                regnr = get_input("Nummerplade (f.eks. AB12345)", "regnr")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: VehicleIntelligence(regnr).run(driver)
                finally: driver.quit()

            elif choice == "21":
                from modules.mod_21_bssid import BSSIDGeofencer
                BSSIDGeofencer(get_input("MAC Adresse / BSSID (xx:xx:xx:xx:xx)", "bssid")).run(None)

            elif choice == "22":
                from modules.mod_22_chatapp import ChatAppIntelligence
                chat_query = get_input("Søgeord/Brugernavn", "chat_query")
                print(f"{C.CYAN}[*] Starter sikker browser-session...{C.RESET}")
                driver = get_stealth_driver()
                try: ChatAppIntelligence(chat_query).run(driver)
                finally: driver.quit()

            elif choice == "23":
                from modules.mod_23_matrix import UsernameMatrixAnalyzer
                UsernameMatrixAnalyzer(get_input("Brugernavn", "username")).run(None)

            elif choice == "24":
                from modules.mod_24_opsec import OpsecSanitizer
                OpsecSanitizer(get_input("Sti til fil", "file_path")).run(None)

            elif choice == "25":
                from modules.mod_25_wayback import WaybackMachineIntelligence
                WaybackMachineIntelligence(get_input("URL", "url")).run(None)

            elif choice == "26":
                from modules.mod_26_virustotal import VirusTotalAnalyzer
                VirusTotalAnalyzer(get_input("IP eller Hash", "ip")).run(None)

            elif choice == "27":
                from modules.mod_27_ai import TitanAIEnrichment
                ai = TitanAIEnrichment()
                res = ai.analyze_text(get_input("Tekst der skal analyseres", "ai_text"))
                print(f"\n{C.GREEN}[✓] AI Resultat:\n{json.dumps(res, indent=4, ensure_ascii=False)}{C.RESET}")

            elif choice == "28":
                from modules.mod_28_graph import GoliathGraphExporter
                GoliathGraphExporter().generate()

            elif choice == "29":
                from modules.mod_29_kml import GoogleEarthExporter
                GoogleEarthExporter().generate()

            elif choice == "14":
                AutomatedCaseReporter().generate()

            else:
                print(f"{C.YELLOW}[!] Modul {choice} er tomt pt. eller findes ikke.{C.RESET}")

        except Exception as e:
            print(f"\n{C.RED}[!] Fejl i modul: {str(e)}{C.RESET}")

class AutomatedCaseReporter:
    """Genererer et professionelt interaktivt HTML Dashboard over alle beviser"""
    def __init__(self):
        self.loot_dir = session["loot_folder"]
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.report_file = f"FINAL_REPORT_{self.timestamp}.html"

    def generate(self):
        files = list(Path(self.loot_dir).glob("*.json"))
        all_cpr, all_bank, all_emails = set(), set(), set()
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                if "Intelligence" in data:
                    intel = data["Intelligence"]
                    all_cpr.update(intel.get("CPR", []))
                    all_bank.update(intel.get("Bank_Accounts", []))
                    all_emails.update(intel.get("Emails", []))
                if "HIBP_Breaches" in data or "Data_Leaks" in data:
                    all_emails.add(data.get("Email", ""))
            except Exception: continue

        html_content = f"""
        <html>
        <head>
            <title>OSINT MISSION REPORT</title>
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; background-color: #0d1117; color: #c9d1d9; margin: 40px; }}
                h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
                h2 {{ color: #ff7b72; margin-top: 30px; }}
                .box {{ background-color: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 6px; margin-bottom: 20px; }}
                .badge {{ background-color: #238636; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; }}
                ul {{ list-style-type: square; }}
                li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <h1>OMNI-HUNTER // INTELLIGENCE DASHBOARD</h1>
            <p><strong>Genereret:</strong> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</p>
            <p><strong>Mål/Sag:</strong> {session.get('name', 'Ukendt')}</p>
            
            <div class="box">
                <h2>🚨 KRITISKE IDENTIFIKATORER</h2>
                <p><strong>CPR Numre <span class="badge">{len(all_cpr)}</span></strong></p>
                <ul>{''.join([f"<li>{c}</li>" for c in all_cpr]) if all_cpr else "<li>Ingen fundet</li>"}</ul>
                
                <p><strong>Bankkonti <span class="badge">{len(all_bank)}</span></strong></p>
                <ul>{''.join([f"<li>{b}</li>" for b in all_bank]) if all_bank else "<li>Ingen fundet</li>"}</ul>
                
                <p><strong>Email Adresser <span class="badge">{len(all_emails)}</span></strong></p>
                <ul>{''.join([f"<li>{e}</li>" for e in all_emails]) if all_emails else "<li>Ingen fundet</li>"}</ul>
            </div>
            
            <div class="box">
                <h2>📁 RÅ BEVIS-FILER I SAGSMAPPEN</h2>
                <ul>{''.join([f"<li>{f.name}</li>" for f in files])}</ul>
            </div>
        </body>
        </html>
        """

        Path(self.report_file).write_text(html_content, encoding='utf-8')
        print(f"\n{C.GREEN}[✓✓✓] MISSION DASHBOARD GENERERET! Åbn denne fil i din browser: {self.report_file}{C.RESET}")

if __name__ == "__main__":
    args = setup_cli()
    if args.headless: print("Headless mode aktiveret.")
    else: main()