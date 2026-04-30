# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import urllib.parse
import requests
import re
from datetime import datetime
from pathlib import Path

from core.utils import C, session, REGEX_EMAIL, extract_danish_phones
from core.utils import REGEX_BTC, REGEX_ETH, REGEX_IBAN, REGEX_IPV4
from core.network import http, CONFIG, omni_dork_search, safe_get_with_retry
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BusinessIntelligenceAnalyst:
    """PETFE GOLIATH V10 - Corporate Juggernaut & Threat Intel Engine"""
    
    def __init__(self, name_or_cvr):
        self.input_query = name_or_cvr.strip()
        self.is_cvr = bool(re.match(r'^\d{8}$', self.input_query))
        self.name = "Ukendt Virksomhed" if self.is_cvr else self.input_query
        self.official_domain = None
        
        self.api_key = CONFIG.get("api_keys", {}).get("hunter_io", "")
        self.results = {
            "Søgekriterie": self.input_query,
            "Søgetype": "CVR-Nummer" if self.is_cvr else "Virksomhedsnavn",
            "Mål": self.name, 
            "Domæne": None,
            "CVR_Intel": [], 
            "Hunter_Data": {}, 
            "Proff_Links": [],
            "Erhvervs_Netværk": [],
            "Tilknyttede_Selskaber": [],      # NY V10: Skraber andre CVR numre på siden
            "Statstidende_Hits": [],          
            "Trustpilot_Social_Hits": [],
            "DevOps_GitHub_Leaks": [],        
            "Eksponerede_Dokumenter": [],     
            "BBR_Ejendoms_Spor": [],          # NY V10: Er det en privat adresse?
            "Finans_Krypto_Spor": [],         # NY V10: Hvidvask/Krypto detektion
            "Deep_Scrape_Telefoner": [],      
            "Deep_Scrape_Emails": [],         
            "Deep_Scrape_Adresser": [],
            "Maps_Links": [],                 
            "Wayback_Machine": [],            
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        sys.stdout.write("\r" + " " * 85 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        self.driver_ref = driver 
        print(f"\n{C.CYAN}{'='*80}\n[02] CORPORATE INTELLIGENCE (GOLIATH V10 JUGGERNAUT)\n{'='*80}{C.RESET}")
        print(f"[*] Starter massiv virksomheds-analyse for CVR/Firma: {C.WHITE}{self.input_query}{C.RESET}\n")
        
        # FASE 1: Identitets-opløsning
        self._update_progress(5, "Opløser Virksomhedsidentitet (Multi-API Fallback)")
        self._resolve_identity()
        
        if self.name == "Ukendt Virksomhed" and self.is_cvr and driver:
            self._force_name_extraction(driver)
            
        print(f"\n{C.MAGENTA}    -> Låst Mål: {self.name}{C.RESET}")

        # FASE 2: Domæne-opsporing
        self._update_progress(15, "Opsporer Officielt Corporate Domain")
        self._hunt_corporate_domain(driver)

        # FASE 3: Scrape & Profil-injektion
        if self.is_cvr:
            self._bypass_google_dorking()
        else:
            self._update_progress(20, "Dorking Virksomhedsregistre (Proff, Ownr, Virk)")
            self._check_proff(driver)
            self._google_broad_fallback(driver)
            self._bypass_google_dorking()
        
        # FASE 4: DEEP SCRAPE (Rå HTML ekstraktion)
        self._update_progress(35, "Infiltrerer CVR-profiler (Deep DOM Scrape)")
        self._deep_scrape_company_links(driver)
        
        # FASE 5: Corporate Mail & Ansatte
        self._update_progress(50, "Infiltrerer Email-Infrastruktur (Hunter.io)")
        self._check_hunter()
        
        if self.official_domain and driver:
            self._update_progress(60, "Kortlægger Ansatte via LinkedIn Pivot")
            self._linkedin_pivot(driver)
            
        # FASE 6: Dev-Ops & Leaks
        if driver:
            self._update_progress(65, "Scanner DevOps & Cloud-miljøer (GitHub/Trello)")
            self._hunt_devops_footprint(driver)
            
            self._update_progress(70, "Søger efter eksponerede dokumenter (PDF/DOCX)")
            self._hunt_exposed_documents(driver)

            self._update_progress(75, "Scanner Finansielle Footprints (Krypto/Hvidvask)")
            self._hunt_financial_footprint(driver)
        
        # FASE 7: Jura, Omdømme & BBR
        self._update_progress(80, "Søger i Statstidende (Konkurser/Jura)")
        self._check_statstidende(driver)
        
        self._update_progress(85, "Scanner Sociale Medier via Netværk/Tlf")
        self._check_trustpilot_and_socials(driver)

        self._update_progress(90, "Krydstjekker BBR for Privatbolig-registrering")
        self._check_bbr_estate(driver)

        # FASE 8: GEOINT & Historik
        self._update_progress(95, "Genererer Tactical GEOINT & Street View Links")
        self._generate_maps_links()
        
        self._update_progress(98, "Henter historiske slettede sider (Wayback Machine)")
        self._check_wayback_machine()

        sys.stdout.write("\r" + " " * 85 + "\r")
        print(f"\n{C.GREEN}[✓] CORPORATE INTELLIGENCE MISSION FULDFØRT.{C.RESET}")
        
        self._print_final_summary()
        self._massive_omni_pivot_trigger(driver)

    def _resolve_identity(self):
        sys.stdout.write("\r" + " " * 85 + "\r")
        headers = {"User-Agent": "PETFE-OSINT-Tool - admin@localhost.com"}
        url_cvrapi = f"https://cvrapi.dk/api?search={urllib.parse.quote(self.input_query)}&country=dk"
        
        try:
            res = http.get(url_cvrapi, headers=headers, timeout=5)
            if res.status_code == 200 and "error" not in res.text:
                data = res.json()
                self._apply_api_data(data)
                return
        except Exception: pass
        print(f"{C.DIM}    [-] CVR API fejlede. Skifter til Fallback Scraper...{C.RESET}")
        
    def _apply_api_data(self, raw_data):
        if self.is_cvr and raw_data.get("name"):
            self.name = raw_data.get("name")
            self.results["Mål"] = self.name

        clean_intel = {
            "Virksomhed": raw_data.get("name"),
            "CVR": raw_data.get("vat"),
            "Status": raw_data.get("status", "Aktiv"),
            "Hovedadresse": f"{raw_data.get('address')}, {raw_data.get('city')}",
        }
        print(f"{C.GREEN}    ✓ Virksomhed identificeret: {clean_intel['Virksomhed']} (CVR: {clean_intel['CVR']}){C.RESET}")
        self.results["CVR_Intel"].append(clean_intel)

    def _force_name_extraction(self, driver):
        print(f"{C.YELLOW}    [*] API nede. Tvinger DOM-ekstraktion af firmanavn via Ownr.dk...{C.RESET}")
        url = f"https://ownr.dk/companies/public-profile/{self.input_query}"
        if safe_get_with_retry(driver, url):
            try:
                name_el = driver.find_element(By.CSS_SELECTOR, "h1.company-title, h1")
                if name_el and len(name_el.text) > 2:
                    self.name = name_el.text.strip()
                    self.results["Mål"] = self.name
                    print(f"{C.GREEN}    ✓ Navn reddet via Stealth Scrape: {self.name}{C.RESET}")
            except Exception: pass

    def _hunt_corporate_domain(self, driver):
        if not driver or self.name == "Ukendt Virksomhed": return
        dork = f'"{self.name}" "kontakt"'
        links = omni_dork_search(driver, dork, max_links=5)
        bad_domains = ["virk.dk", "ownr.dk", "proff.dk", "facebook.com", "krak.dk", "degulesider.dk", "linkedin.com", "instagram.com", "trustpilot.com", "eniro.dk"]
        
        for link in links:
            url = link['url']
            try:
                domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
                if domain and not any(bad in domain for bad in bad_domains):
                    self.official_domain = domain
                    self.results["Domæne"] = domain
                    print(f"{C.GREEN}    ✓ Officielt Corporate Domain identificeret: {self.official_domain}{C.RESET}")
                    break
            except: continue

    def _check_hunter(self):
        if not self.api_key: return
        if not self.official_domain:
            for email in self.results.get("Deep_Scrape_Emails", []):
                domain = email.split('@')[-1].lower()
                if domain not in ["gmail.com", "yahoo.com", "hotmail.com", "icloud.com"]:
                    self.official_domain = domain
                    break
        if not self.official_domain:
            self.official_domain = self.name.lower().replace(' ', '').replace(',', '') + ".dk"
            print(f"{C.DIM}    [*] Gætter domæne til Hunter: {self.official_domain}{C.RESET}")

        print(f"{C.YELLOW}    [*] Forespørger Hunter.io for {self.official_domain}...{C.RESET}")
        url = f"https://api.hunter.io/v2/domain-search?domain={self.official_domain}&api_key={self.api_key}"
        try:
            res = requests.get(url, timeout=10).json()
            if "data" in res and "emails" in res["data"] and len(res["data"]["emails"]) > 0:
                emails = res["data"]["emails"]
                print(f"{C.RED}    🔥 BREACH: Fandt {len(emails)} ansatte/e-mails tilknyttet domænet!{C.RESET}")
                clean_emails = []
                for emp in emails[:15]:
                    first, last, pos = emp.get("first_name", ""), emp.get("last_name", ""), emp.get("position", "")
                    clean_emails.append({"Email": emp.get("value"), "Navn": f"{first} {last}".strip(), "Stilling": pos})
                    print(f"{C.CYAN}      -> {emp.get('value')} | {first} {last} ({pos}){C.RESET}")
                    if emp.get("value") not in self.results["Deep_Scrape_Emails"]:
                        self.results["Deep_Scrape_Emails"].append(emp.get("value"))
                self.results["Hunter_Data"] = {"Emails": clean_emails}
            else:
                print(f"{C.DIM}    [-] Ingen Hunter.io data for dette domæne.{C.RESET}")
        except Exception: pass

    def _linkedin_pivot(self, driver):
        firma_navn = self.name.split(' ')[0] if self.name != "Ukendt Virksomhed" else self.official_domain.split('.')[0]
        dork = f'site:linkedin.com/in "{firma_navn}"'
        links = omni_dork_search(driver, dork, max_links=4)
        if links:
            print(f"{C.GREEN}    ✓ Identificerede LinkedIn-ansatte!{C.RESET}")
            for link in links: print(f"      -> {link['url']}")

    def _hunt_devops_footprint(self, driver):
        query = self.input_query if self.is_cvr else f'"{self.name}"'
        dork = f'{query} site:github.com OR site:trello.com OR site:pastebin.com'
        links = omni_dork_search(driver, dork, max_links=4)
        if links:
            print(f"{C.RED}    [!] ADVARSEL: Potentielle DevOps Leaks fundet! (Kildekode / Boards){C.RESET}")
            for link in links:
                print(f"      -> {link['url']}")
                self.results["DevOps_GitHub_Leaks"].append(link['url'])

    def _hunt_exposed_documents(self, driver):
        if self.name == "Ukendt Virksomhed": return
        dork = f'"{self.name}" ext:pdf OR ext:docx OR ext:xlsx'
        links = omni_dork_search(driver, dork, max_links=4)
        if links:
            print(f"{C.RED}    [!] ADVARSEL: Eksponerede virksomhedsdokumenter fundet!{C.RESET}")
            for link in links:
                print(f"      -> {link['url']}")
                self.results["Eksponerede_Dokumenter"].append(link['url'])

    def _hunt_financial_footprint(self, driver):
        """V10: Søger efter CVR nummer eller email associeret med kryptovaluta og hvidvask fora"""
        query = self.input_query if self.is_cvr else f'"{self.name}"'
        dork = f'{query} (bitcoin OR crypto OR wallet OR usdt OR eth OR xmr) -news -nyheder'
        links = omni_dork_search(driver, dork, max_links=3)
        if links:
            print(f"{C.RED}    [!] KRYPTO SPOR: Forbindelse mellem virksomhed og kryptovaluta fundet!{C.RESET}")
            for link in links:
                print(f"      -> {link['url']}")
                self.results["Finans_Krypto_Spor"].append(link['url'])

    def _check_bbr_estate(self, driver):
        """V10: Tjekker om firmaadressen optræder på boligsider (hvilket indikerer at det er ejerens privatadresse)"""
        if not self.results["Deep_Scrape_Adresser"] or not driver: return
        
        vej = self.results["Deep_Scrape_Adresser"][0].split(',')[0].strip()
        dork = f'"{vej}" site:dingeo.dk OR site:boliga.dk OR site:bbr.dk'
        links = omni_dork_search(driver, dork, max_links=2)
        if links:
            print(f"{C.YELLOW}    [*] BBR MATCH: Virksomhedsadressen ser ud til at være en privatbolig!{C.RESET}")
            for link in links:
                self.results["BBR_Ejendoms_Spor"].append(link['url'])

    def _bypass_google_dorking(self):
        if self.is_cvr:
            ownr_url = f"https://ownr.dk/companies/public-profile/{self.input_query}"
            virk_url = f"https://datacvr.virk.dk/enhed/virksomhed/{self.input_query}"
            for url in [ownr_url, virk_url]:
                if url not in self.results["Proff_Links"]:
                    self.results["Proff_Links"].append(url)

    def _check_proff(self, driver):
        if driver:
            dork = f'site:proff.dk OR site:ownr.dk OR site:virk.dk "{self.name}"'
            links = omni_dork_search(driver, dork, max_links=5)
            for link in links: self.results["Proff_Links"].append(link['url'])

    def _google_broad_fallback(self, driver):
        if driver:
            dork = f'"{self.input_query}" OR "cvr: {self.input_query}"'
            links = omni_dork_search(driver, dork, max_links=3)
            for link in links:
                if any(x in link['url'] for x in ["ownr", "virk", "proff"]):
                    self.results["Proff_Links"].append(link['url'])

    def _check_statstidende(self, driver):
        if not driver: return
        search_term = self.input_query if self.is_cvr else f'"{self.name}"'
        dork = f'site:statstidende.dk {search_term}'
        links = omni_dork_search(driver, dork, max_links=3)
        real_hits = [l for l in links if "robots.txt" not in l['url'] and len(l['url']) > 35]
        if real_hits:
            print(f"{C.RED}    [!] ADVARSEL: Juridiske sager / Konkurser i Statstidende!{C.RESET}")
            for link in real_hits:
                print(f"      -> {link['url']}")
                self.results["Statstidende_Hits"].append(link['url'])

    def _check_trustpilot_and_socials(self, driver):
        if not driver: return
        raw_queries = []
        if self.results["Erhvervs_Netværk"]: raw_queries.append(self.results["Erhvervs_Netværk"][0])
        if self.results["Deep_Scrape_Telefoner"]: raw_queries.append(self.results["Deep_Scrape_Telefoner"][0])
        if self.results["Deep_Scrape_Emails"]: raw_queries.append(self.results["Deep_Scrape_Emails"][0])
        
        raw_queries = list(set(raw_queries))
        if not raw_queries: return
            
        combined_query_str = " OR ".join([f'"{q}"' for q in raw_queries])
        dork = f'(site:facebook.com OR site:trustpilot.com OR site:instagram.com) ({combined_query_str})'
        
        links = omni_dork_search(driver, dork, max_links=4)
        if links:
            print(f"{C.GREEN}    🔥 Fandt Social/Trustpilot hits associeret med virksomheden!{C.RESET}")
            for link in links:
                print(f"      -> {link['url']}")
                self.results["Trustpilot_Social_Hits"].append(link['url'])

    def _generate_maps_links(self):
        for addr in self.results.get("Deep_Scrape_Adresser", []):
            encoded = urllib.parse.quote(addr)
            link = f"https://www.google.com/maps/search/?api=1&query={encoded}"
            if link not in self.results["Maps_Links"]:
                self.results["Maps_Links"].append(link)
                print(f"{C.CYAN}      -> Kort-Link: {link}{C.RESET}")

    def _check_wayback_machine(self):
        if not self.official_domain: return
        print(f"\n{C.YELLOW}[*] Tjekker Wayback Machine for historiske snapshots af '{self.official_domain}'...{C.RESET}")
        url = f"http://archive.org/wayback/available?url={self.official_domain}"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get("archived_snapshots", {}).get("closest"):
                snap = res["archived_snapshots"]["closest"]["url"]
                self.results["Wayback_Machine"].append(snap)
                print(f"{C.GREEN}    🔥 Fandt historisk snapshot! Sikrer slettede data: {snap}{C.RESET}")
        except: pass

    def _deep_scrape_company_links(self, driver):
        if not driver: return
        
        for url in list(set(self.results.get("Proff_Links", [])))[:4]:
            print(f"{C.DIM}    -> Infiltrerer og scraper: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(3)
                
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["accept", "tillad", "godkend"]):
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1)
                            break
                except: pass
                
                html_source = driver.page_source
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                # EMAIL EXTRACTION
                bad_email_domains = ["ownr.dk", "virk.dk", "proff.dk", "sentry.io", "w3.org", "google.com"]
                for em in REGEX_EMAIL.findall(html_source):
                    em = em.lower()
                    if em not in self.results["Deep_Scrape_Emails"] and not any(ext in em for ext in bad_email_domains):
                        self.results["Deep_Scrape_Emails"].append(em)
                        print(f"{C.CYAN}      ✓ Email Extracted: {em}{C.RESET}")

                # TELEFON EXTRACTION
                bad_phones = [self.input_query, "36408820", "70200000", "72200000"]
                for ph in extract_danish_phones(html_source):
                    if ph not in self.results["Deep_Scrape_Telefoner"] and ph not in bad_phones:
                        self.results["Deep_Scrape_Telefoner"].append(ph)
                        print(f"{C.CYAN}      ✓ Telefon Extracted: {ph}{C.RESET}")

                # ANDRE SELSKABER EXTRACTION (V10)
                cvr_matches = re.findall(r'\b[1-9]\d{7}\b', page_text)
                for cvr in set(cvr_matches):
                    if cvr != self.input_query and cvr not in self.results["Tilknyttede_Selskaber"]:
                        self.results["Tilknyttede_Selskaber"].append(cvr)
                        print(f"{C.MAGENTA}      ✓ Relateret CVR Extracted: {cvr}{C.RESET}")
                
                # NETVÆRK & EJER EXTRACTION
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                bad_names = ["se selskabsdiagram", "legale ejere", "reelle ejere", "ejerhistorik", 
                             "dk", "direktion", "bestyrelse", "log ind", "opret", "vis mere", 
                             "ejerandel", "fuldt ansvarlig", "registreret på cvr", "et resumé", 
                             "deltager", "resume", "nej", "ja", "ownr holder", "følg selskab", 
                             "print", "del", "kopier link", "enhedsvisning", self.name.lower()]
                
                for i, line in enumerate(lines):
                    if any(x in line.lower() for x in ["ejerandel", "fuldt ansvarlig", "reelle ejere", "direktør", "stifter", "ejer"]):
                        for j in range(i-1, max(-1, i-10), -1):
                            pot_name = lines[j]
                            if " " in pot_name and not any(c.isdigit() for c in pot_name) and not any(bad in pot_name.lower() for bad in bad_names) and not pot_name.isupper():
                                if pot_name not in self.results["Erhvervs_Netværk"]:
                                    self.results["Erhvervs_Netværk"].append(pot_name)
                                    print(f"{C.MAGENTA}      ✓ Ejer/Person udtrukket: {pot_name}{C.RESET}")
                                break 

                # ADRESSE EXTRACTION
                for i, line in enumerate(lines):
                    zip_match = re.search(r'\b(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ]+)\b', line)
                    if zip_match:
                        zip_city = zip_match.group(0)
                        street = lines[i-1] if i > 0 else ""
                        
                        if len(street) > 3 and not any(x in street.lower() for x in bad_names):
                            full_addr = f"{street}, {zip_city}"
                            if full_addr not in self.results["Deep_Scrape_Adresser"]:
                                self.results["Deep_Scrape_Adresser"].append(full_addr)
                                print(f"{C.GREEN}      ✓ Adresse Extracted: {full_addr}{C.RESET}")

            except Exception: pass

    def _print_final_summary(self):
        print(f"\n{C.CYAN}--- GOLIATH V10: CORPORATE SUMMARY FOR {self.results['Mål'].upper()} ---{C.RESET}")
        
        if self.results['Deep_Scrape_Adresser']: print(f"{C.GREEN}[+] Adresser: {', '.join(self.results['Deep_Scrape_Adresser'])}{C.RESET}")
        if self.results['BBR_Ejendoms_Spor']: print(f"{C.YELLOW}[!] Mulig Privatbolig (BBR): Ja, tjekket på DinGeo/Boliga{C.RESET}")
        if self.results['Deep_Scrape_Telefoner']: print(f"{C.GREEN}[+] Telefoner: {', '.join(self.results['Deep_Scrape_Telefoner'])}{C.RESET}")
        if self.results['Deep_Scrape_Emails']: print(f"{C.GREEN}[+] Emails: {', '.join(self.results['Deep_Scrape_Emails'])}{C.RESET}")
        if self.results['Erhvervs_Netværk']: print(f"{C.MAGENTA}[+] Direktion/Ejere: {', '.join(self.results['Erhvervs_Netværk'])}{C.RESET}")
        if self.results['Tilknyttede_Selskaber']: print(f"{C.MAGENTA}[+] Relaterede CVR Netværk: {', '.join(self.results['Tilknyttede_Selskaber'])}{C.RESET}")
        if self.official_domain: print(f"{C.MAGENTA}[+] Corporate Domain: {self.official_domain}{C.RESET}")
        if self.results['DevOps_GitHub_Leaks']: print(f"{C.RED}[!] Potentielle Code Leaks (GitHub/Trello): {len(self.results['DevOps_GitHub_Leaks'])} fundet!{C.RESET}")
        if self.results['Eksponerede_Dokumenter']: print(f"{C.RED}[!] Eksponerede Filer (PDF/DOC): {len(self.results['Eksponerede_Dokumenter'])} fundet!{C.RESET}")
        if self.results['Finans_Krypto_Spor']: print(f"{C.RED}[!] Krypto/Finans Spor: {len(self.results['Finans_Krypto_Spor'])} fundet!{C.RESET}")
        if self.results['Statstidende_Hits']: print(f"{C.RED}[!] ADVARSEL: Juridiske sager (Statstidende) fundet!{C.RESET}")

    def _massive_omni_pivot_trigger(self, driver):
        """V10 THE GRAND OMNI-PIVOT: SKYDER PÅ ALT!"""
        netvaerk = self.results.get('Erhvervs_Netværk', [])
        telefoner = self.results.get('Deep_Scrape_Telefoner', [])
        emails = self.results.get('Deep_Scrape_Emails', [])
        domaene = self.official_domain
        
        if not (netvaerk or telefoner or emails or domaene): return
        
        valg = input(f"\n{C.YELLOW}[?] BEKRÆFT OMNI-PIVOT? Tryk ENTER for at affyre samtlige PETFE-moduler mod {self.results['Mål']} (eller 'n'): {C.RESET}").strip().lower()
        if valg in ['n', 'nej', 'no']:
            self.save()
            return
            
        print(f"\n{C.BG_RED}{C.WHITE} 💥 INITIERER GOLIATH V10 MASSIVE OMNI-PIVOT (CROSS-MODULE DOMINATION) 💥 {C.RESET}\n")
        self.results["Samlet_Pivot_Data"] = {}
        
        ejer_navn = netvaerk[0] if netvaerk else self.name
        ejer_email = emails[0] if emails else None
        ejer_telefon = telefoner[0] if telefoner else None

        # --- MODUL 03: BREACH PIVOT ---
        if ejer_email:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 03 (Breach Analyse) på: {ejer_email}{C.RESET}")
            try:
                from modules.mod_03_breach import BreachIntelligenceAnalyst
                breach = BreachIntelligenceAnalyst(ejer_email)
                breach.run(driver)
                self.results["Samlet_Pivot_Data"]["Breach_Data"] = breach.data if hasattr(breach, 'data') else "Fuldført"
                print(f"{C.GREEN}  ✓ Modul 03 data tilføjet.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 03 overprunget: {e}{C.RESET}")

        # --- MODUL 04: SOCIAL STALKER PIVOT ---
        if ejer_navn:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 04 (Social Media Stalker) på: {ejer_navn}{C.RESET}")
            try:
                from modules.mod_02_social import SocialMediaProfiler
                soc = SocialMediaProfiler(ejer_navn)
                soc.run(driver)
                self.results["Samlet_Pivot_Data"]["Social_Media"] = soc.data if hasattr(soc, 'data') else "Fuldført"
                print(f"{C.GREEN}  ✓ Modul 04 data tilføjet.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 04 overprunget: {e}{C.RESET}")

        # --- MODUL 05: OFFLINE DB PIVOT ---
        if ejer_navn or ejer_email:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 05 (Offline DB) på: {ejer_navn} / {ejer_email}{C.RESET}")
            try:
                from modules.mod_03_offline import OfflineDatabaseAnalyzer
                off_query = ejer_email if ejer_email else ejer_navn
                # Kræver en sti, antager standard sti eller skipper
                off_db = OfflineDatabaseAnalyzer(off_query, "/home/hugo/omni_hunter/loot_evidence")
                off_db.run()
                print(f"{C.GREEN}  ✓ Modul 05 data tilføjet.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 05 overprunget: {e}{C.RESET}")

        # --- MODUL 07: PHONE PIVOT ---
        if ejer_telefon:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 07 (Telefon-Opslag) på: {ejer_telefon}{C.RESET}")
            try:
                from modules.mod_04_phone import PhoneIntelligenceHunter
                phone_check = PhoneIntelligenceHunter(ejer_telefon)
                phone_check.run(driver)
                print(f"{C.GREEN}  ✓ Telefon data tilføjet.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 07 overprunget: {e}{C.RESET}")

        # --- MODUL 10: IP / DOMAIN PIVOT ---
        if domaene:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 10 (IP & Server Analyse) på: {domaene}{C.RESET}")
            try:
                from modules.mod_06_ip import IPNetworkAnalyzer 
                ip_scan = IPNetworkAnalyzer(domaene)
                ip_scan.run(None)
                print(f"{C.GREEN}  ✓ Modul 10 data tilføjet.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 10 overprunget: {e}{C.RESET}")

        # --- MODUL 17: SNIPER PIVOT ---
        if ejer_navn and ejer_email:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 17 (Sniper Profiling) på: {ejer_navn} / {ejer_email}{C.RESET}")
            try:
                from modules.mod_08_sniper import SniperModule
                # FIX: Navngivne argumenter forhindrer fejl-tildeling af emails!
                sniper = SniperModule(name=ejer_navn, email=ejer_email)
                sniper.run()
                print(f"{C.GREEN}  ✓ Modul 17 Sniper fuldført.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 17 overprunget: {e}{C.RESET}")

        # --- MODUL 25: WAYBACK PIVOT ---
        if domaene:
            print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 25 (Wayback Bevissikring) på: {domaene}{C.RESET}")
            try:
                from modules.mod_25_wayback import WaybackMachineIntelligence 
                wb = WaybackMachineIntelligence(domaene)
                wb.run(None)
                print(f"{C.GREEN}  ✓ Modul 25 Bevissikring fuldført.{C.RESET}")
            except Exception as e: print(f"{C.DIM}  [-] Modul 25 overprunget: {e}{C.RESET}")

        self.save()

    def save(self):
        os.makedirs(session.get("loot_folder", "loot_evidence"), exist_ok=True)
        clean_name = self.input_query.replace(' ', '_').replace('.', '_')
        filename = f"{session.get('loot_folder', 'loot_evidence')}/02_BUSINESS_{clean_name}.json"
        
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass

        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}    [✓] Master Corporate Report gemt lokalt: {filename}{C.RESET}")