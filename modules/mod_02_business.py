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
from selenium.webdriver.common.by import By 

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
            "Statstidende_Hits": [],          
            "Trustpilot_Social_Hits": [],     
            "Deep_Scrape_Telefoner": [],      
            "Deep_Scrape_Emails": [],         
            "Deep_Scrape_Adresser": [],
            "Timestamp": datetime.now().isoformat()
        }

    def _update_progress(self, pct, message):
        """Klippestabil progress bar der rydder linjen"""
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(f"{C.CYAN}    [*] {message}... {pct}%{C.RESET}")
        sys.stdout.flush()

    def run(self, driver):
        self.driver_ref = driver 
        print(f"\n{C.CYAN}{'='*60}\n[02] Erhvervs-efterretning (CVR, Hunter, Proff & DDG V7)\n{'='*60}{C.RESET}")
        print(f"[*] Starter virksomheds-analyse for: {self.input_query}\n")
        
        self._update_progress(20, "Slår op i CVR-Registeret")
        self._check_cvr()
        
        self._update_progress(40, "Søger i Hunter.io Databasen")
        domain_found = self._check_hunter()
        
        if domain_found and driver:
            self._update_progress(55, "Udfører LinkedIn Pivot Search")
            self._linkedin_pivot(driver, domain_found)
        
        self._update_progress(65, "Dorking Proff.dk (Regnskaber & Netværk)")
        self._check_proff(driver)
        
        self._update_progress(75, "Søger i Statstidende (Konkurser/Jura)")
        self._check_statstidende(driver)
        
        self._update_progress(80, "Scanner Trustpilot & Sociale Medier")
        self._check_trustpilot_and_socials(driver)
        
        self._update_progress(85, "Udfører Multi-Engine Fallback (Google & DDG)")
        self._google_broad_fallback(driver)

        # NY V7: ANTI-DORK BYPASS! Hvis Google og DDG blokerede os, tvinger vi direkte URLs ind
        self._bypass_google_dorking()
        
        self._update_progress(95, "Deep Scrape af virksomhedsprofiler")
        self._deep_scrape_company_links(driver)
        
        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.GREEN}[✓] Erhvervs-analyse 100% fuldført.{C.RESET}")
        
        # --- V7: INTERAKTIV VALIDERING & SAMLET JSON PIVOT ---
        print(f"\n{C.CYAN}--- OPSUMMERING AF FUND FOR {self.results['Mål']} ({self.input_query}) ---{C.RESET}")
        adresser = self.results.get("Deep_Scrape_Adresser", [])
        if adresser: print(f"{C.GREEN}[+] Adresser fundet: {', '.join(adresser)}{C.RESET}")
        
        telefoner = self.results.get("Deep_Scrape_Telefoner", [])
        if telefoner: print(f"{C.GREEN}[+] Telefonnumre fundet: {', '.join(telefoner)}{C.RESET}")
        
        emails = self.results.get("Deep_Scrape_Emails", [])
        if emails: print(f"{C.GREEN}[+] Emails fundet: {', '.join(emails)}{C.RESET}")
        
        if self.results.get("Statstidende_Hits"):
            print(f"{C.RED}[!] ADVARSEL: Juridiske sager/Konkurser fundet i Statstidende!{C.RESET}")

        netvaerk = self.results.get('Erhvervs_Netværk', [])
        if netvaerk: print(f"{C.GREEN}[+] Identificeret Netværk/Ejere: {', '.join(netvaerk)}{C.RESET}")
        
        if netvaerk or adresser or telefoner:
            valg = input(f"\n{C.YELLOW}[?] Er dette korrekt? Skal GOLIATH udføre total person-pivot på ejeren og bygge en SAMLET JSON? (j/n): {C.RESET}").lower()
            if valg == 'j':
                ejer_navn = input(f"{C.CYAN}[?] Indtast navnet på personen fra listen (f.eks. {netvaerk[0] if netvaerk else 'Navn'}): {C.RESET}").strip()
                if ejer_navn:
                    print(f"\n{C.RED}[!] STARTER TOTAL CROSS-MODULE PIVOT PÅ {ejer_navn}...{C.RESET}")
                    self.results["Samlet_Pivot_Data"] = {}
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

        if not api_success:
            print(f"{C.YELLOW}    [*] API blokeret. Prøver DuckDuckGo HTML Scraper for CVR-data...{C.RESET}")
            dork = f'site:virk.dk "{self.input_query}"'
            # Prøver Omni Dork først
            links = omni_dork_search(self.driver_ref, dork, max_links=3) if hasattr(self, 'driver_ref') else []
            
            # Hvis Google blokerer, bruger vi DuckDuckGo direkte!
            if not links:
                links_urls = self._duckduckgo_html_search(dork)
                links = [{"url": u, "title": "", "snippet": ""} for u in links_urls]

            if links:
                print(f"{C.GREEN}    ✓ Fandt virksomhedsdata via Multi-Engine Dorking!{C.RESET}")
                for link in links:
                    self._extract_cvr_and_roles(link.get('snippet', ''), link['url'])
                    break 
            else:
                print(f"{C.DIM}    [-] Multi-Engine Dorking fandt ingen CVR-data.{C.RESET}")

    def _duckduckgo_html_search(self, query):
        """NY V7: DuckDuckGo Fallback Scraper når Google blokerer"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            res = requests.get(url, headers=headers, timeout=10)
            # Udtrækker direkte links fra DuckDuckGo HTML
            links = re.findall(r'href="([^"]+)"', res.text)
            clean_links = [urllib.parse.unquote(l.split('uddg=')[1].split('&')[0]) for l in links if 'uddg=' in l]
            if clean_links:
                print(f"{C.GREEN}      ✓ DuckDuckGo leverede resultater udenom Google!{C.RESET}")
            return clean_links[:5]
        except Exception as e:
            return []

    def _bypass_google_dorking(self):
        """NY V7: Anti-Dork Bypass! Google blokerer os ofte. Hvis vi har et CVR, indsætter vi bare de rigtige links direkte!"""
        if self.is_cvr:
            print(f"\n{C.YELLOW}[*] Anti-Dork Bypass Aktiveret: Injektion af direkte links til databaser...{C.RESET}")
            ownr_url = f"https://ownr.dk/companies/public-profile/{self.input_query}"
            virk_url = f"https://datacvr.virk.dk/enhed/virksomhed/{self.input_query}"
            
            for url in [ownr_url, virk_url]:
                if url not in self.results.get("Proff_Links", []):
                    self.results["Proff_Links"].append(url)
                    print(f"{C.GREEN}    ✓ Direkte URL injiceret til Scraperen: {url}{C.RESET}")

    def _check_hunter(self):
        if not self.api_key:
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Mangler API-nøgle i config.json){C.RESET}")
            return None
        domain = self.name if not self.is_cvr else self.results.get("Mål")
        if domain == "Ukendt Virksomhed": 
            print(f"\n{C.DIM}[-] Springer Hunter.io over (Intet firmanavn endnu){C.RESET}")
            return None
        if "." not in domain:
            forslag = domain.lower().replace(' ', '') + ".com" 
            domain = input(f"\n{C.YELLOW}[?] Indtast domæne for email-udtræk (f.eks. {forslag}) eller tryk ENTER for at springe over: {C.RESET}").strip()
            if not domain: return None

        print(f"\n{C.YELLOW}[*] Udfører Corporate Domain Search på '{domain}'...{C.RESET}")
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.api_key}"
        try:
            res = requests.get(url, timeout=10).json()
            if "data" in res and "emails" in res["data"] and len(res["data"]["emails"]) > 0:
                emails = res["data"]["emails"]
                pattern = res["data"].get("pattern", "Ukendt")
                print(f"{C.GREEN}    🔥 Fandt {len(emails)} e-mails tilknyttet {domain}!{C.RESET}")
                clean_emails = []
                for emp in emails[:15]:
                    first, last, pos = emp.get("first_name", ""), emp.get("last_name", ""), emp.get("position", "")
                    clean_emails.append({"Email": emp.get("value"), "Navn": f"{first} {last}".strip(), "Stilling": pos})
                    print(f"{C.GREEN}      ✓ {emp.get('value')} ({first} {last}) - {pos}{C.RESET}")
                self.results["Hunter_Data"] = {"Format": pattern, "Emails": clean_emails}
                return domain
            else:
                print(f"{C.YELLOW}    [-] Ingen offentlige e-mails fundet for {domain}.{C.RESET}")
                return None
        except Exception as e:
            print(f"{C.RED}    [!] Hunter.io Fejl: {e}{C.RESET}")
            return None

    def _linkedin_pivot(self, driver, domain):
        print(f"\n{C.YELLOW}[*] Dorking LinkedIn for ansatte hos {domain}...{C.RESET}")
        firma_navn = domain.split('.')[0]
        dork = f'site:linkedin.com/in "{firma_navn}"'
        links = omni_dork_search(driver, dork, max_links=3)
        if links:
            print(f"{C.GREEN}    ✓ Fandt LinkedIn profiler for ansatte!{C.RESET}")
            for link in links: print(f"      -> {link['url']}")
        else:
            print(f"{C.DIM}    [-] Ingen tydelige LinkedIn profiler fundet i topresultaterne.{C.RESET}")

    def _check_proff(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking Proff.dk, Ownr.dk & Virk.dk for netværk...{C.RESET}")
        if driver:
            dork = f'site:proff.dk OR site:ownr.dk OR site:virk.dk "{self.name}"'
            links = omni_dork_search(driver, dork, max_links=5)
            if not links:
                links_urls = self._duckduckgo_html_search(dork)
                links = [{"url": u, "title": "", "snippet": ""} for u in links_urls]

            if links:
                print(f"{C.GREEN}    ✓ Fandt regnskabs/netværks-data!{C.RESET}")
                for link in links:
                    print(f"      -> {link['url']}")
                    self.results["Proff_Links"].append(link['url'])
            else:
                print(f"{C.DIM}    [-] Intet fundet på Proff/Ownr/Virk.{C.RESET}")

    def _check_statstidende(self, driver):
        """NY V7: Fixet False Positives"""
        print(f"\n{C.YELLOW}[*] Dorking Statstidende for juridiske advarsler...{C.RESET}")
        if driver:
            search_term = self.input_query if self.is_cvr else f'"{self.name}"'
            dork = f'site:statstidende.dk {search_term}'
            links = omni_dork_search(driver, dork, max_links=3)
            if links:
                # Filtrerer ubrugelige links væk som kun er forsiden eller robots.txt
                real_hits = [l for l in links if l['url'] not in ["https://www.statstidende.dk/", "https://www.statstidende.dk/robots.txt"]]
                if real_hits:
                    print(f"{C.RED}    [!] ADVARSEL: Juridiske publikationer fundet i Statstidende!{C.RESET}")
                    for link in real_hits:
                        print(f"      -> {link['url']}")
                        self.results["Statstidende_Hits"].append({"Titel": link.get('title',''), "URL": link['url']})
                else:
                    print(f"{C.DIM}    [-] Ingen hits i Statstidende (Falske positiver sorteret fra).{C.RESET}")
            else:
                print(f"{C.DIM}    [-] Ingen hits i Statstidende.{C.RESET}")

    def _check_trustpilot_and_socials(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking Trustpilot & Facebook (Omdømme og kontaktinfo)...{C.RESET}")
        if driver and self.name != "Ukendt Virksomhed":
            dork = f'(site:trustpilot.com/review OR site:facebook.com) "{self.name}"'
            links = omni_dork_search(driver, dork, max_links=4)
            if links:
                print(f"{C.GREEN}    ✓ Fandt sociale/anmeldelses-profiler!{C.RESET}")
                for link in links:
                    print(f"      -> {link['url']}")
                    self.results["Trustpilot_Social_Hits"].append(link['url'])
            else:
                print(f"{C.DIM}    [-] Ingen åbenlyse Trustpilot/Facebook sider fundet.{C.RESET}")

    def _extract_cvr_and_roles(self, text, url):
        cvr_matches = re.findall(r'\b(?:CVR|cvr)[\s:-]*(\d{8})\b', text)
        for cvr in cvr_matches:
            if cvr not in self.results.get("CVR_Intel", [{}])[0].get("CVR", ""): 
                print(f"{C.CYAN}      -> Sekundært CVR-Nummer detekteret i netværket: {cvr}{C.RESET}")

    def _google_broad_fallback(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking: Udfører bred Google Fallback-søgning...{C.RESET}")
        if driver:
            dork = f'"{self.input_query}" OR "cvr: {self.input_query}" OR "cvr {self.input_query}"'
            links = omni_dork_search(driver, dork, max_links=5)
            if not links:
                links_urls = self._duckduckgo_html_search(dork)
                links = [{"url": u, "title": "", "snippet": ""} for u in links_urls]

            if links:
                print(f"{C.GREEN}    ✓ Fandt {len(links)} resultater via bred søgning!{C.RESET}")
                for link in links:
                    print(f"      -> {link['url']}")
                    self.results["Proff_Links"].append(link['url'])
            else:
                print(f"{C.DIM}    [-] Bred søgning gav ingen yderligere resultater.{C.RESET}")

    def _deep_scrape_company_links(self, driver):
        print(f"\n{C.YELLOW}[*] Deep Scrape: Går direkte ind på fundne profiler for at hente skjult data...{C.RESET}")
        if not driver: return
        
        for url in list(set(self.results.get("Proff_Links", [])))[:6]:
            print(f"{C.DIM}    -> Åbner og scraper: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(4) # Venter ekstra på Ownr's tunge DOM
                
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["accept", "tillad", "godkend", "ok"]):
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1)
                            break
                except: pass
                
                page_title = driver.title
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                if self.name == "Ukendt Virksomhed" and self.is_cvr:
                    parts = page_title.split('-')
                    if parts and len(parts[0].strip()) > 2:
                        self.name = parts[0].strip()
                        self.results["Mål"] = self.name
                        print(f"{C.GREEN}      ✓ Firmanavn reddet via Deep Scrape: {self.name}{C.RESET}")
                
                # Splitter teksten til præcis linje-analyse (Fjerner tomme linjer)
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]

                # 1. PRÆCIS ADRESSE-UDTRÆK (Leder efter dansk postnummer og tager gaden over)
                for i, line in enumerate(lines):
                    zip_match = re.search(r'\b(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ]+)\b', line)
                    if zip_match:
                        zip_city = zip_match.group(0)
                        street = lines[i-1] if i > 0 else ""
                        # Undgår at fange irrelevante data-felter
                        if len(street) > 3 and not any(x in street.lower() for x in ["stiftet", "status", "cvr", "telefon", "adresse"]):
                            full_addr = f"{street}, {zip_city}"
                            if full_addr not in self.results["Deep_Scrape_Adresser"]:
                                self.results["Deep_Scrape_Adresser"].append(full_addr)
                                print(f"{C.GREEN}      ✓ Præcis Adresse fundet: {full_addr}{C.RESET}")

                # 2. PRÆCIS EJER-UDTRÆK (Bypasser knapper som 'Se selskabsdiagram')
                bad_names = ["se selskabsdiagram", "legale ejere", "reelle ejere", "ejerhistorik", "dk", "direktion", "bestyrelse"]
                for i, line in enumerate(lines):
                    if any(x in line.lower() for x in ["ejerandel", "fuldt ansvarlig", "reelle ejere", "direktør"]):
                        # Kigger op ad (op til 6 linjer tilbage) for at finde et navn, der ikke er en knap
                        for j in range(i-1, max(-1, i-6), -1):
                            pot_name = lines[j]
                            # Et navn har mellemrum, ingen tal, og er ikke i vores 'bad_names' liste
                            if " " in pot_name and not any(c.isdigit() for c in pot_name) and pot_name.lower() not in bad_names:
                                if pot_name not in self.results["Erhvervs_Netværk"]:
                                    self.results["Erhvervs_Netværk"].append(pot_name)
                                    print(f"{C.MAGENTA}      ✓ Ejer/Netværk præcist udtrukket: {pot_name}{C.RESET}")
                                break # Stop når vi har fundet navnet for denne rolle

                # 3. Udtrækker Email-adresser 
                emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', page_text)
                for email in set(emails):
                    if email.lower() not in self.results.setdefault("Deep_Scrape_Emails", []) and ".png" not in email.lower() and ".jpg" not in email.lower():
                        self.results["Deep_Scrape_Emails"].append(email.lower())
                        print(f"{C.CYAN}      ✓ Direkte Email fundet på siden: {email.lower()}{C.RESET}")

                # 4. Udtrækker danske telefonnumre
                phones = re.findall(r'\b(?:[2-9]\d{7}|[2-9]\d{1}\s\d{2}\s\d{2}\s\d{2})\b', page_text)
                for phone in set(phones):
                    clean_phone = phone.replace(" ", "")
                    if len(clean_phone) == 8 and clean_phone not in self.results.setdefault("Deep_Scrape_Telefoner", []):
                        self.results["Deep_Scrape_Telefoner"].append(clean_phone)
                        print(f"{C.CYAN}      ✓ Direkte Telefon fundet på siden: {clean_phone}{C.RESET}")

            except Exception as e:
                print(f"{C.DIM}      [-] Kunne ikke deep-scrape {url}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        clean_name = self.input_query.replace(' ', '_').replace('.', '_')
        filename = f"{session['loot_folder']}/02_BUSINESS_{clean_name}.json"
        
        # NY V7: Tvungen sletning af gammel fil for at sikre at Windows ikke cacher filen!
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt (Overskrevet succesfuldt): {filename}{C.RESET}")