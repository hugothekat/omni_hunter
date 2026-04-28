# -*- coding: utf-8 -*-
import os
import sys
import shutil
import argparse
import json
from pathlib import Path
from datetime import datetime

# Importer Core-motoren
from core.utils import C, session, get_input, load_session
from core.browser import get_stealth_driver
from core.logger import logger

def check_dependencies():
    """Tjekker at maskinrummet er klar før opsendelse"""
    tools = {"rg": "Ripgrep (Offline Databaser)", "tesseract": "Tesseract OCR (Billedtekst)", "exiftool": "ExifTool (OPSEC)"}
    for tool, desc in tools.items():
        if shutil.which(tool) is None:
            print(f"{C.YELLOW}[!] System-advarsel: {desc} mangler. Nogle moduler vil have nedsat funktion.{C.RESET}")

def setup_cli():
    parser = argparse.ArgumentParser(description="PETFE GOLIATH - Professionelt OSINT Værktøj")
    parser.add_argument("-t", "--target", help="Målets navn, email eller IP")
    parser.add_argument("-m", "--module", help="Modulnummer (00-29)", type=str)
    parser.add_argument("--headless", action="store_true", help="Kør uden visuel menu")
    return parser.parse_args()

def display_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{C.WHITE}{C.BOLD}")
    print("=" * 75)
    print(" PETFE GOLIATH V8 // CENTRAL EFTERRETNINGS-KONSOL")
    print("=" * 75)
    print(f"{C.RESET}")
    
    print(f"{C.BG_RED}{C.WHITE} [00] AUTONOM EFTERFORSKNING (Indtast navn -> Få alt data automatisk) {C.RESET}\n")
    
    print(f"{C.CYAN}--- [ PERSON & VIRKSOMHED ] -----------------------------------------------{C.RESET}")
    print(f" {C.GREEN}[01]{C.RESET} Personopslag (Krak/Geo)        {C.GREEN}[02]{C.RESET} Virksomheds-OSINT (CVR/Proff)")
    print(f" {C.GREEN}[04]{C.RESET} Sociale Medier (Profil-skan)   {C.GREEN}[23]{C.RESET} Global Brugernavn-søgning (300+)")
    print(f" {C.GREEN}[07]{C.RESET} Telefonopslag (Offentlig)      {C.GREEN}[12]{C.RESET} Omvendt Telefonopslag (Skjult)")

    print(f"\n{C.CYAN}--- [ CYBER & CREDENTIALS ] -----------------------------------------------{C.RESET}")
    print(f" {C.GREEN}[03]{C.RESET} Lækkede Passwords & Databaser  {C.GREEN}[05]{C.RESET} Offline Database Søgning (Lokal)")
    print(f" {C.GREEN}[06]{C.RESET} Gæt E-mailadresser (Mønstre)   {C.GREEN}[09]{C.RESET} E-mail Sporing (IP & Lokation)")
    print(f" {C.GREEN}[17]{C.RESET} Generér Password-Wordlist      {C.GREEN}[18]{C.RESET} Tøm E-mailkonto (IMAP Ripper)")

    print(f"\n{C.CYAN}--- [ TEKNISK & INFRASTRUKTUR ] -------------------------------------------{C.RESET}")
    print(f" {C.GREEN}[10]{C.RESET} IP-adresse Analyse             {C.GREEN}[19]{C.RESET} Krypto-sporing (Blockchain)")
    print(f" {C.GREEN}[20]{C.RESET} Køretøjs-opslag & Gæld         {C.GREEN}[21]{C.RESET} Find Fysisk Lokation via MAC/WiFi")
    print(f" {C.GREEN}[22]{C.RESET} Chat & Discord Forensik        {C.GREEN}[26]{C.RESET} Virus/Malware Analyse (Threat Intel)")
    print(f" {C.GREEN}[08]{C.RESET} Mørkenet Søgning (Darkweb)     {C.GREEN}[25]{C.RESET} Arkiv-søgning (Slettede sider)")

    print(f"\n{C.CYAN}--- [ FORENSIK & ANALYSE ] ------------------------------------------------{C.RESET}")
    print(f" {C.GREEN}[11]{C.RESET} Digital Forensik (Filer)       {C.GREEN}[13]{C.RESET} Omvendt Billedsøgning")
    print(f" {C.GREEN}[16]{C.RESET} Masse-skanning af Mappe        {C.GREEN}[24]{C.RESET} Fjern Metadata (OPSEC)")
    print(f" {C.GREEN}[27]{C.RESET} AI-Assisteret Profilering")

    print(f"\n{C.CYAN}--- [ VISUALISERING & EKSPORT ] -------------------------------------------{C.RESET}")
    print(f" {C.GREEN}[28]{C.RESET} Visuelt Netværkskort (Maltego) {C.GREEN}[29]{C.RESET} 3D GPS-Kortlægning (Google Earth)")
    print(f" {C.GREEN}[14]{C.RESET} Generér HTML Sagsrapport")
    
    print(f"\n{C.DIM}" + "-" * 75 + f"{C.RESET}")
    print(f" {C.RED}[99] Afslut System{C.RESET}")

def main():
    os.makedirs(session["loot_folder"], exist_ok=True)
    load_session() # Henter tidligere indtastede data
    check_dependencies()
    
    while True:
        display_menu()
        
        try:
            choice = input(f"\n{C.YELLOW}Vælg Handling [00-99]: {C.RESET}").strip()
            
            if choice == "99" or choice.lower() in ['q', 'exit', 'quit']: 
                print(f"\n{C.RED}[*] Sletter midlertidige spor. System afsluttet.{C.RESET}")
                break

            # --- DYNAMISK ROUTING MED GOLIATH V8 ALIASER ---
            
            if choice == "00" or choice == "0":
                from modules.mod_30_person_intel import PersonIntelligenceOrchestrator
                navn = get_input("Målets fulde navn", "name")
                print(f"{C.CYAN}[*] Starter autonom efterforskning (Henter kaffe, dette kan tage tid)...{C.RESET}")
                driver = get_stealth_driver()
                try: PersonIntelligenceOrchestrator(navn).run(driver)
                finally: driver.quit()

            elif choice == "01":
                from modules.mod_01_krak import DirectoryIntelligenceHunter
                driver = get_stealth_driver()
                try: DirectoryIntelligenceHunter(get_input("Navn", "name"), get_input("By", "city")).run(driver)
                finally: driver.quit()

            elif choice == "02":
                from modules.mod_02_business import BusinessIntelligenceAnalyst
                driver = get_stealth_driver()
                try: BusinessIntelligenceAnalyst(get_input("Firma eller CVR", "name")).run(driver)
                finally: driver.quit()

            elif choice == "03":
                from modules.mod_03_breach import BreachIntelligenceAnalyst
                driver = get_stealth_driver()
                try: BreachIntelligenceAnalyst(get_input("Email", "email")).run(driver)
                finally: driver.quit()

            elif choice == "04":
                from modules.mod_04_social import SocialMediaProfiler
                driver = get_stealth_driver()
                try: SocialMediaProfiler(get_input("Brugernavn", "username")).run(driver)
                finally: driver.quit()

            elif choice == "05":
                from modules.mod_05_offline import OfflineDatabaseAnalyzer
                OfflineDatabaseAnalyzer(get_input("Søgeord (Email/Navn)", "db_target"), get_input("Sti til .txt fil/mappe", "db_path")).run()

            elif choice == "06":
                from modules.mod_06_emailgen import EmailPatternGenerator
                driver = get_stealth_driver()
                try: EmailPatternGenerator(get_input("Navn", "name")).run(driver)
                finally: driver.quit()

            elif choice == "07":
                from modules.mod_07_phone import PhoneIntelligenceHunter
                driver = get_stealth_driver()
                try: PhoneIntelligenceHunter(get_input("Telefon (uden +45)", "phone")).run(driver)
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
                driver = get_stealth_driver()
                try: ReversePhoneIntelligence(get_input("Telefon (uden +45)", "phone")).run(driver)
                finally: driver.quit()

            elif choice == "13":
                from modules.mod_13_revimage import ReverseImageIntelligence
                driver = get_stealth_driver()
                try: ReverseImageIntelligence(get_input("Sti til billede", "image_path")).run(driver)
                finally: driver.quit()

            elif choice == "16":
                from modules.mod_16_titan import AutoForensicMassScanner
                folder = get_input("Sti til Mappe (f.eks. /home/user/leaks)", "dump_folder")
                driver = get_stealth_driver()
                try: AutoForensicMassScanner(folder).run(driver)
                finally: driver.quit()

            elif choice == "17":
                from modules.mod_17_sniper import SniperModule # V8 Navn
                print(f"\n{C.YELLOW}--- GOLIATH SNIPER: KONFIGURATION ---{C.RESET}")
                SniperModule(
                    name=get_input("Målets fulde navn", "name"), 
                    city=get_input("By", "city"), 
                    cpr=get_input("CPR (DDMMYY-XXXX)", "cpr"), 
                    clues=get_input("Clues (f.eks. hund, kone)", "clues")
                ).run()

            elif choice == "18":
                from modules.mod_18_mailrip import GoliathMailRipper
                GoliathMailRipper(get_input("Email", "email"), get_input("App Password", "password")).run()

            elif choice == "19":
                from modules.mod_19_crypto import CryptoLedgerAnalyzer
                CryptoLedgerAnalyzer(get_input("Krypto Adresse (BTC/ETH)", "crypto")).run(None)

            elif choice == "20":
                from modules.mod_20_vehicle import VehicleIntelligence
                driver = get_stealth_driver()
                try: VehicleIntelligence(get_input("Nummerplade (f.eks. AB12345)", "regnr")).run(driver)
                finally: driver.quit()

            elif choice == "21":
                from modules.mod_21_bssid import BSSIDGeofencer
                BSSIDGeofencer(get_input("MAC Adresse / BSSID", "bssid")).run(None)

            elif choice == "22":
                from modules.mod_22_chatapp import ChatAppIntelligence
                driver = get_stealth_driver()
                try: ChatAppIntelligence(get_input("Søgeord/Discord ID", "chat_query")).run(driver)
                finally: driver.quit()

            elif choice == "23":
                from modules.mod_23_matrix import MatrixAnalyzer # V8 Navn
                MatrixAnalyzer(get_input("Brugernavn", "username")).run(None)

            elif choice == "24":
                from modules.mod_24_opsec import OpsecSanitizer
                OpsecSanitizer(get_input("Sti til fil for rensning", "file_path")).run(None)

            elif choice == "25":
                from modules.mod_25_wayback import WaybackMachineIntelligence
                WaybackMachineIntelligence(get_input("URL til arkivering", "url")).run(None)

            elif choice == "26":
                from modules.mod_26_virustotal import VirusTotalAnalyzer
                VirusTotalAnalyzer(get_input("IP, Domæne, URL eller Hash", "ip")).run(None)

            elif choice == "27":
                from modules.mod_27_ai import TitanAIEnrichment
                ai = TitanAIEnrichment()
                res = ai.analyze_text(get_input("Tekst der skal AI-analyseres", "ai_text"))
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
                print(f"{C.RED}[!] Ukendt kommando.{C.RESET}")
                
            input(f"\n{C.DIM}Tryk ENTER for at vende tilbage til hovedmenuen...{C.RESET}")

        except KeyboardInterrupt:
            print(f"\n{C.RED}[!] Proces afbrudt af operatør (Ctrl+C).{C.RESET}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Kritisk systemfejl i menuen: {e}")
            print(f"\n{C.BG_RED}{C.WHITE}[!] KRITISK FEJL:{C.RESET} {str(e)}")
            input(f"\n{C.DIM}Tryk ENTER for at fortsætte...{C.RESET}")

class AutomatedCaseReporter:
    """GOLIATH V8: Genererer et professionelt interaktivt HTML Dashboard over sagen"""
    def __init__(self):
        self.loot_dir = session.get("loot_folder", "loot_evidence")
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.report_file = os.path.join(self.loot_dir, f"SAGSRAPPORT_{self.timestamp}.html")

    def generate(self):
        print(f"\n{C.CYAN}[*] Kompilerer Sagsrapport...{C.RESET}")
        files = list(Path(self.loot_dir).glob("*.json"))
        
        # Samledata
        all_cpr, all_bank, all_emails, all_phones, all_usernames = set(), set(), set(), set(), set()
        master_score = "Ikke beregnet"
        
        for file in files:
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                
                # Hvis vi fanger Modul 30 Master filen
                if "Confidence_Score" in data:
                    master_score = f"{data['Confidence_Score']}/100"
                    all_emails.update(data.get("Emails", []))
                    all_usernames.update(data.get("Brugernavne", []))
                    all_phones.update(data.get("Telefonnumre", []))
                    all_cpr.update(data.get("CPR_Fragments", []))
                    
                # Fra Modul 16 (TITAN)
                if "Case_Intelligence" in data:
                    intel = data["Case_Intelligence"]
                    all_cpr.update(intel.get("ID_Documents", {}).get("CPR_Numre", []))
                    all_bank.update(intel.get("Financial_Leads", {}).get("Bankkonti", []))
                    all_emails.update(intel.get("Digital_Footprint", {}).get("Emails", {}).keys())
                    
                # Fra Modul 03 (Breach)
                if "Eksponerede_Passwords" in data:
                    all_emails.add(data.get("Email", ""))
            except Exception: continue

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SAGSRAPPORT // PETFE</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom: 10px; font-weight: 600; letter-spacing: 1px; }}
                h2 {{ color: #2980b9; margin-top: 30px; font-size: 1.2em; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                .box {{ background-color: #ffffff; border: 1px solid #ddd; padding: 20px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                .badge {{ background-color: #34495e; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px; }}
                .badge-red {{ background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ margin-bottom: 8px; background: #ecf0f1; padding: 8px; border-radius: 4px; border-left: 3px solid #3498db; }}
                .header-stats {{ display: flex; justify-content: space-between; background: #ffffff; padding: 15px; border-radius: 6px; margin-bottom: 30px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>SAGSRAPPORT // DIGITAL EFTERFORSKNING</h1>
            
            <div class="header-stats">
                <div><strong>Udskrevet:</strong> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</div>
                <div><strong>Mål:</strong> <span style="color: #c0392b; font-weight: bold;">{session.get('name', 'Ikke angivet').upper()}</span></div>
                <div><strong>Datamatch Score:</strong> <span class="badge-red">{master_score}</span></div>
            </div>
            
            <div class="grid">
                <div class="box">
                    <h2>Kritiske Identifikatorer</h2>
                    <p><strong>Personnumre (CPR) <span class="badge">{len(all_cpr)}</span></strong></p>
                    <ul>{''.join([f"<li>{c}</li>" for c in all_cpr]) if all_cpr else "<li>Ingen data</li>"}</ul>
                    
                    <p><strong>Telefonnumre <span class="badge">{len(all_phones)}</span></strong></p>
                    <ul>{''.join([f"<li>+45 {b}</li>" for b in all_phones]) if all_phones else "<li>Ingen data</li>"}</ul>
                </div>
                
                <div class="box">
                    <h2>Digitalt Fodspor</h2>
                    <p><strong>Email Adresser <span class="badge">{len(all_emails)}</span></strong></p>
                    <ul>{''.join([f"<li>{e}</li>" for e in all_emails]) if all_emails else "<li>Ingen data</li>"}</ul>
                    
                    <p><strong>Brugernavne / Aliaser <span class="badge">{len(all_usernames)}</span></strong></p>
                    <ul>{''.join([f"<li>@{u}</li>" for u in all_usernames]) if all_usernames else "<li>Ingen data</li>"}</ul>
                </div>
            </div>
            
            <div class="box" style="margin-top: 20px;">
                <h2>Bevismateriale i Sagsmappen ({len(files)} filer)</h2>
                <ul style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                    {''.join([f"<li style='border-left: 3px solid #2ecc71; font-size: 0.9em;'>{f.name}</li>" for f in files])}
                </ul>
            </div>
        </body>
        </html>
        """

        Path(self.report_file).write_text(html_content, encoding='utf-8')
        print(f"{C.GREEN}[✓] Sagsrapport genereret succesfuldt!{C.RESET}")
        print(f"{C.CYAN}    -> Åbn filen: {self.report_file}{C.RESET}")

if __name__ == "__main__":
    args = setup_cli()
    if args.headless: print("Kører i baggrunden uden menu.")
    else: main()