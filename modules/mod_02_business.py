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

from core.utils import C, session
from core.network import http, CONFIG, omni_dork_search

class BusinessIntelligenceAnalyst:
    def __init__(self, name_or_cvr):
        self.input_query = name_or_cvr.strip()
        # Intelligent detektion: Er det et navn eller et CVR nummer?
        self.is_cvr = bool(re.match(r'^\d{8}$', self.input_query))
        self.name = "Ukendt Virksomhed" if self.is_cvr else self.input_query
        
        self.api_key = CONFIG.get("api_keys", {}).get("hunter_io", "")
        self.results = {
            "Søgekriterie": self.input_query,
            "Søgetype": "CVR-Nummer" if self.is_cvr else "Virksomhedsnavn",
            "Mål": self.name, 
            "CVR_Intel": [], 
            "Hunter_Data": {}, 
            "Proff_Links": [],
            "Erhvervs_Netværk": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        """Klippestabil progress bar der rydder linjen"""
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        self.driver_ref = driver # Gem driveren så fallback kan bruge den
        print(f"\n{C.CYAN}{'='*60}\n[02] Erhvervs-efterretning (CVR, Hunter & Proff V7)\n{'='*60}{C.RESET}")
        print(f"[*] Starter virksomheds-analyse for: {self.input_query}\n")
        
        self._update_progress(20, "Slår op i CVR-Registeret")
        self._check_cvr()
        
        self._update_progress(50, "Søger i Hunter.io Databasen")
        domain_found = self._check_hunter()
        
        # NYT PIVOT: Hvis Hunter fandt et domæne, led efter LinkedIn profiler
        if domain_found and driver:
            self._update_progress(65, "Udfører LinkedIn Pivot Search")
            self._linkedin_pivot(driver, domain_found)
        
        self._update_progress(80, "Dorking Proff.dk (Regnskaber & Netværk)")
        self._check_proff(driver)
        
        # NY V7: Bred Google Fallback
        self._update_progress(90, "Udfører bred Google Fallback-søgning")
        self._google_broad_fallback(driver)
        
        # NY V7: Fysisk Deep Scrape af alle fundne sider
        self._update_progress(95, "Deep Scrape af virksomhedsprofiler")
        self._deep_scrape_company_links(driver)
        
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.GREEN}[✓] Erhvervs-analyse 100% fuldført.{C.RESET}")
        
        # --- V7: INTERAKTIV VALIDERING & SAMLET JSON PIVOT ---
        print(f"\n{C.CYAN}--- OPSUMMERING AF FUND FOR {self.input_query} ---{C.RESET}")
        adresser = self.results.get("Deep_Scrape_Adresser", [])
        if adresser: print(f"{C.GREEN}[+] Adresser fundet: {', '.join(adresser)}{C.RESET}")
        netvaerk = self.results.get('Erhvervs_Netværk', [])
        if netvaerk: print(f"{C.GREEN}[+] Identificeret Netværk/Ejere: {', '.join(netvaerk)}{C.RESET}")
        
        if netvaerk or adresser:
            valg = input(f"\n{C.YELLOW}[?] Er dette korrekt? Skal GOLIATH udføre total person-pivot på ejeren og bygge en SAMLET JSON? (j/n): {C.RESET}").lower()
            if valg == 'j':
                ejer_navn = input(f"{C.CYAN}[?] Indtast navnet på personen fra listen (f.eks. {netvaerk[0] if netvaerk else 'Navn'}): {C.RESET}").strip()
                if ejer_navn:
                    print(f"\n{C.RED}[!] STARTER TOTAL CROSS-MODULE PIVOT PÅ {ejer_navn}...{C.RESET}")
                    self.results["Samlet_Pivot_Data"] = {}
                    
                    # Kører Modul 04 (Social) direkte ind i vores JSON
                    try:
                        from modules.mod_04_social import SocialMediaProfiler
                        soc = SocialMediaProfiler(ejer_navn)
                        soc.run(driver)
                        self.results["Samlet_Pivot_Data"]["Social_Media"] = soc.data
                        print(f"{C.GREEN}  ✓ Modul 04 data tilføjet til samlet rapport.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 04 Pivot fejlede: {e}{C.RESET}")
        
        self.save()

    def _check_cvr(self):
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.YELLOW}[*] Henter virksomhedsdata via CVR API...{C.RESET}")
        
        headers = {"User-Agent": "PETFE-OSINT-Tool - admin@localhost.com"}
        url = f"https://cvrapi.dk/api?search={urllib.parse.quote(self.input_query)}&country=dk"
        
        api_success = False
        
        try:
            response = http.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and "error" not in response.text:
                raw_data = response.json()
                api_success = True
                
                if self.is_cvr and raw_data.get("name"):
                    self.name = raw_data.get("name")
                    self.results["Mål"] = self.name

                p_units = raw_data.get("productionunits", [])
                
                clean_intel = {
                    "Virksomhed": raw_data.get("name"),
                    "CVR": raw_data.get("vat"),
                    "Status": raw_data.get("status", "Aktiv"),
                    "Hovedadresse": f"{raw_data.get('address')}, {raw_data.get('city')}",
                }
                
                print(f"{C.GREEN}    ✓ Virksomhed fundet via API: {clean_intel['Virksomhed']} (CVR: {clean_intel['CVR']}){C.RESET}")
                self.results["CVR_Intel"].append(clean_intel)

            else:
                err_msg = response.json().get("message", "") if "error" in response.text else str(response.status_code)
                print(f"{C.DIM}    [-] CVR API Fejlede/Blokeret: {err_msg}{C.RESET}")
                
        except Exception as e:
            print(f"{C.RED}    [!] CVR API Netværksfejl: {e}{C.RESET}")

        # --- V7: FALLBACK TIL GOOGLE DORKING (Headless) ---
        if not api_success:
            print(f"{C.YELLOW}    [*] API blokeret. Udfører Fallback: Dorking Virk.dk for CVR-data...{C.RESET}")
            # Vi bruger omni_dork_search, som kører over den usynlige webdriver
            dork = f'site:virk.dk "{self.input_query}"'
            
            # For at undgå at programmet crasher hvis 'driver' ikke er sendt med til check_cvr
            # Sørg for at tilføje 'driver' som parameter i funktionen nedenfor!
            links = omni_dork_search(self.driver_ref, dork, max_links=3) if hasattr(self, 'driver_ref') else []
            
            if links:
                print(f"{C.GREEN}    ✓ Fandt virksomhedsdata via Google Dorking!{C.RESET}")
                for link in links:
                    titel = link.get('title', '')
                    snippet = link.get('snippet', '')
                    
                    # Trækker navnet ud fra titlen (f.eks. "Novo Nordisk A/S - CVR - Virk")
                    virk_navn = titel.split('-')[0].strip() if '-' in titel else titel
                    if self.is_cvr and self.name == "Ukendt Virksomhed":
                        self.name = virk_navn
                        self.results["Mål"] = self.name
                        
                    print(f"      -> {C.CYAN}Navn/Link:{C.RESET} {virk_navn}")
                    
                    # Fodrer netværks-udtrækkeren med snippeten for at finde andre CVR/Roller
                    self._extract_cvr_and_roles(snippet, link['url'])
                    break # Vi behøver kun det bedste hit
            else:
                print(f"{C.DIM}    [-] Fallback Dorking fandt ingen CVR-data for: {self.input_query}{C.RESET}")

    def _check_hunter(self):
        if not self.api_key:
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Mangler API-nøgle i config.json){C.RESET}")
            return None

        # V7: Hvis vi søgte på et CVR nummer, bruger vi det fundne navn fra CVR-databasen
        domain = self.name if not self.is_cvr else self.results.get("Mål")
        
        if domain == "Ukendt Virksomhed": 
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Intet firmanavn fundet via CVR){C.RESET}")
            return None

        if "." not in domain:
            forslag = domain.lower().replace(' ', '') + ".com" 
        # ... RESTEN AF FUNKTIONEN ER UÆNDRET ...

        print(f"\n{C.YELLOW}[*] Udfører Corporate Domain Search på '{domain}'...{C.RESET}")
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.api_key}"
        
        try:
            res = requests.get(url, timeout=10).json()
            if "data" in res and "emails" in res["data"] and len(res["data"]["emails"]) > 0:
                emails = res["data"]["emails"]
                pattern = res["data"].get("pattern", "Ukendt")
                
                print(f"{C.GREEN}    🔥 Fandt {len(emails)} e-mails tilknyttet {domain}!{C.RESET}")
                if pattern:
                    print(f"      -> Format: {pattern}")
                
                clean_emails = []
                for emp in emails[:15]:
                    first = emp.get("first_name", "")
                    last = emp.get("last_name", "")
                    pos = emp.get("position", "")
                    clean_emails.append({
                        "Email": emp.get("value"),
                        "Navn": f"{first} {last}".strip(),
                        "Stilling": pos
                    })
                    print(f"{C.GREEN}      ✓ {emp.get('value')} ({first} {last}) - {pos}{C.RESET}")
                    
                self.results["Hunter_Data"] = {"Format": pattern, "Emails": clean_emails}
                
                if len(emails) > 15:
                    print(f"{C.CYAN}    ... og {len(emails)-15} flere.{C.RESET}")
                return domain
            else:
                print(f"{C.YELLOW}    [-] Ingen offentlige e-mails fundet for {domain}.{C.RESET}")
                return None
        except Exception as e:
            print(f"{C.RED}    [!] Hunter.io Fejl: {e}{C.RESET}")
            return None

    def _linkedin_pivot(self, driver, domain):
        """NY V7 PIVOT: Søger LinkedIn efter medarbejdere ud fra domænet"""
        print(f"\n{C.YELLOW}[*] Dorking LinkedIn for ansatte hos {domain}...{C.RESET}")
        firma_navn = domain.split('.')[0]
        dork = f'site:linkedin.com/in "{firma_navn}"'
        links = omni_dork_search(driver, dork, max_links=3)
        if links:
            print(f"{C.GREEN}    ✓ Fandt LinkedIn profiler for ansatte!{C.RESET}")
            for link in links:
                print(f"      -> {link['url']}")
        else:
            print(f"{C.DIM}    [-] Ingen tydelige LinkedIn profiler fundet i topresultaterne.{C.RESET}")

    def _check_proff(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking Proff.dk, Ownr.dk & Virk.dk for netværk...{C.RESET}")
        if driver:
            # V7: Udvidet dork der rammer de tre største danske erhvervsdatabaser
            dork = f'site:proff.dk OR site:ownr.dk OR site:virk.dk "{self.name}"'
            links = omni_dork_search(driver, dork, max_links=5)
            if links:
                print(f"{C.GREEN}    ✓ Fandt regnskabs/netværks-data!{C.RESET}")
                for link in links:
                    print(f"      -> {link['url']}")
                    self.results["Proff_Links"].append(link['url'])
                    # Kalder V7 netværks-udtrækker for at suge CVR og roller ud af snippeten
                    self._extract_cvr_and_roles(f"{link.get('title', '')} {link.get('snippet', '')}", link['url'])
            else:
                print(f"{C.DIM}    [-] Intet fundet på Proff/Ownr/Virk.{C.RESET}")

    def _extract_cvr_and_roles(self, text, url):
        """NY V7: Udtrækker CVR-numre og roller direkte fra Virk, Ownr og Proff"""
        cvr_matches = re.findall(r'\b(?:CVR|cvr)[\s:-]*(\d{8})\b', text)
        for cvr in cvr_matches:
            # Undgå at printe det samme CVR igen, hvis vi allerede kender det
            if cvr not in self.results.get("CVR_Intel", [{}])[0].get("CVR", ""): 
                print(f"{C.CYAN}      -> Sekundært CVR-Nummer detekteret i netværket: {cvr}{C.RESET}")
        
        if any(domain in url for domain in ["proff.dk", "ownr.dk", "virk.dk"]):
            roller = ["Direktør", "Ejer", "Stifter", "Bestyrelsesmedlem", "CEO", "CFO", "Reel ejer"]
            for rolle in roller:
                if rolle.lower() in text.lower():
                    print(f"{C.MAGENTA}      -> Erhvervsrolle/Netværk detekteret: {rolle}{C.RESET}")

    def _google_broad_fallback(self, driver):
        """NY V7: Bred Google-søgning hvis alt andet fejler eller for at fange 'skjulte' spor"""
        print(f"\n{C.YELLOW}[*] Dorking: Udfører bred Google Fallback-søgning...{C.RESET}")
        if driver:
            # Bred søgning: Fanger "cvr: 12345678", "cvr 12345678" eller bare navnet
            dork = f'"{self.input_query}" OR "cvr: {self.input_query}" OR "cvr {self.input_query}"'
            links = omni_dork_search(driver, dork, max_links=5)
            
            if links:
                print(f"{C.GREEN}    ✓ Fandt {len(links)} resultater via bred Google-søgning!{C.RESET}")
                for link in links:
                    print(f"      -> {link['url']}")
                    self.results["Proff_Links"].append(link['url'])
                    self._extract_cvr_and_roles(f"{link.get('title', '')} {link.get('snippet', '')}", link['url'])
            else:
                print(f"{C.DIM}    [-] Bred Google-søgning gav ingen yderligere resultater.{C.RESET}")

    def _deep_scrape_company_links(self, driver):
        """NY V7: Besøger sider direkte, fjerner cookies og udtrækker adresser og ejere"""
        print(f"\n{C.YELLOW}[*] Deep Scrape: Går direkte ind på fundne profiler for at hente skjult data...{C.RESET}")
        if not driver: return
        
        # Besøger kun de 3 bedste links for ikke at spilde tid
        for url in list(set(self.results.get("Proff_Links", [])))[:3]:
            print(f"{C.DIM}    -> Åbner og scraper: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(3) # Venter på JavaScript/Cloudflare
                
                # Omgår Cookie Popups (Accepter alt)
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["accept", "tillad", "godkend", "ok"]):
                            btn.click(); time.sleep(1); break
                except: pass
                
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                # 1. Udtrækker adresser 
                addr_match = re.search(r'([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\.\-]+ \d+[A-Za-z0-9\.\,]*\s*\n*\s*\d{4} [A-ZÆØÅ][a-zæøåA-ZÆØÅ]+)', page_text)
                if addr_match:
                    found_addr = addr_match.group(1).replace('\n', ', ').strip()
                    print(f"{C.GREEN}      ✓ Adresse fundet på siden: {found_addr}{C.RESET}")
                    self.results.setdefault("Deep_Scrape_Adresser", []).append(found_addr)
                
                # 2. Udtrækker Ejere (Kigger efter ordet 'ejerandel' eller 'direktør' og tager navnet ovenover)
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if any(x in line.lower() for x in ["ejerandel", "fuldt ansvarlig", "direktør", "reelle ejere"]):
                        navn = lines[i-1].strip() if i > 0 else ""
                        navn_2 = lines[i-2].strip() if i > 1 else "" # Nogle gange står det 2 linjer oppe
                        
                        for pot_navn in [navn, navn_2]:
                            # Tjekker at det rent faktisk ligner et navn
                            if len(pot_navn) > 4 and not any(char.isdigit() for char in pot_navn):
                                if pot_navn not in self.results["Erhvervs_Netværk"]:
                                    self.results["Erhvervs_Netværk"].append(pot_navn)
                                    print(f"{C.MAGENTA}      ✓ Ejer/Netværk fundet direkte på siden: {pot_navn}{C.RESET}")
            except Exception as e:
                print(f"{C.DIM}      [-] Kunne ikke deep-scrape {url}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        # Gemmer med et clean filnavn, uanset om det var et CVR eller navn
        clean_name = self.input_query.replace(' ', '_').replace('.', '_')
        filename = f"{session['loot_folder']}/02_BUSINESS_{clean_name}.json"
        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt: {filename}{C.RESET}")