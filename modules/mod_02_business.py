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
            "Maps_Links": [],                 # NY V7 TILFØJELSE
            "Wayback_Machine": [],            # NY V7 TILFØJELSE
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
        print(f"[*] Starter virksomheds-analyse for CVR/Firma: {self.input_query}\n")
        
        self._update_progress(10, "Slår op i CVR-Registeret")
        self._check_cvr()
        
        # --- SMART BYPASS TIL CVR SØGNINGER ---
        if self.is_cvr:
            print(f"\n{C.YELLOW}[*] CVR detekteret: Springer langsom Google dorking over og bygger direkte links...{C.RESET}")
            self._bypass_google_dorking()
        else:
            self._update_progress(20, "Dorking Proff.dk (Regnskaber & Netværk)")
            self._check_proff(driver)
            self._update_progress(30, "Udfører Multi-Engine Fallback (Google & DDG)")
            self._google_broad_fallback(driver)
            self._bypass_google_dorking()
        
        # Kør Deep Scrape NU
        self._update_progress(50, "Deep Scrape af virksomhedsprofiler")
        self._deep_scrape_company_links(driver)
        
        # NU kører vi API'er og Socials automatisk baseret på vores fund
        self._update_progress(70, "Søger i Hunter.io Databasen")
        domain_found = self._check_hunter()
        
        if domain_found and driver:
            self._update_progress(75, "Udfører LinkedIn Pivot Search")
            self._linkedin_pivot(driver, domain_found)
        
        self._update_progress(85, "Søger i Statstidende (Konkurser/Jura)")
        self._check_statstidende(driver)
        
        self._update_progress(95, "Scanner Trustpilot & Sociale Medier via Netværk/Tlf")
        self._check_trustpilot_and_socials(driver)

        # NY V7 TILFØJELSE: Kortlægning og Historik
        self._update_progress(97, "Genererer Geolocation & Street View Links")
        self._generate_maps_links()
        
        self._update_progress(98, "Søger i Wayback Machine (Historisk data)")
        self._check_wayback_machine()

        sys.stdout.write("\r" + " " * 80 + "\r")
        print(f"{C.GREEN}[✓] Erhvervs-analyse 100% fuldført.{C.RESET}")
        
        # --- V7: TOTAL AUTO-PIVOT ENGINE ---
        print(f"\n{C.CYAN}--- OPSUMMERING AF FUND FOR {self.results['Mål']} ({self.input_query}) ---{C.RESET}")
        adresser = self.results.get("Deep_Scrape_Adresser", [])
        if adresser: print(f"{C.GREEN}[+] Adresser fundet: {', '.join(adresser)}{C.RESET}")
        
        maps = self.results.get("Maps_Links", [])
        if maps: print(f"{C.CYAN}[+] Google Maps: {maps[0]}{C.RESET}")
        
        telefoner = self.results.get("Deep_Scrape_Telefoner", [])
        if telefoner: print(f"{C.GREEN}[+] Telefonnumre fundet: {', '.join(telefoner)}{C.RESET}")
        
        emails = self.results.get("Deep_Scrape_Emails", [])
        if emails: print(f"{C.GREEN}[+] Emails fundet: {', '.join(emails)}{C.RESET}")

        wayback = self.results.get("Wayback_Machine", [])
        if wayback: print(f"{C.MAGENTA}[+] Arkiveret Hjemmeside fundet: {wayback[0]}{C.RESET}")
        
        if self.results.get("Statstidende_Hits"):
            print(f"{C.RED}[!] ADVARSEL: Juridiske sager/Konkurser fundet i Statstidende!{C.RESET}")

        netvaerk = self.results.get('Erhvervs_Netværk', [])
        if netvaerk: print(f"{C.GREEN}[+] Identificeret Netværk/Ejere: {', '.join(netvaerk)}{C.RESET}")
        
        # AUTO PIVOT - Ingen manuel tastearbejde! TOTAL OMNI-PIVOT PÅ ALLE MODULER
        if netvaerk or adresser or telefoner or emails:
            valg = input(f"\n{C.YELLOW}[?] Bekræft Fund? Tryk ENTER for GOLIATH TOTAL PIVOT på ALT DATA igennem ALLE MODULER (eller 'n' for at stoppe): {C.RESET}").lower()
            if valg != 'n':
                print(f"\n{C.RED}[!] 💥 INITIERER GOLIATH OMNI-PIVOT (CROSS-MODULE DOMINATION) 💥{C.RESET}")
                self.results["Samlet_Pivot_Data"] = {}
                
                ejer_navn = netvaerk[0] if netvaerk else self.name
                ejer_email = emails[0] if emails else None
                ejer_telefon = telefoner[0] if telefoner else None

                # --- MODUL 01: KRAK / 118 PIVOT ---
                print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 01 (Offentlige Registre / Krak) på: {ejer_navn} / {ejer_telefon}{C.RESET}")
                try:
                    from modules.mod_01_krak import KrakIntelligenceAnalyst 
                    m1_query = ejer_telefon if ejer_telefon else ejer_navn
                    m1 = KrakIntelligenceAnalyst(m1_query)
                    m1.run(driver)
                    self.results["Samlet_Pivot_Data"]["Krak_118"] = m1.data
                    print(f"{C.GREEN}  ✓ Modul 01 data tilføjet.{C.RESET}")
                except ImportError:
                    print(f"{C.DIM}  [-] Modul 01 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                except Exception as e:
                    print(f"{C.DIM}  [-] Modul 01 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 03: BREACH PIVOT ---
                if ejer_email:
                    print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 03 (Breach Analyse) på: {ejer_email}{C.RESET}")
                    try:
                        from modules.mod_03_breach import BreachIntelligenceAnalyst
                        breach = BreachIntelligenceAnalyst(ejer_email)
                        breach.run(driver)
                        self.results["Samlet_Pivot_Data"]["Breach_Data"] = breach.data
                        print(f"{C.GREEN}  ✓ Modul 03 data tilføjet.{C.RESET}")
                    except ImportError:
                        print(f"{C.DIM}  [-] Modul 03 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 03 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 04: SOCIAL STALKER PIVOT ---
                if ejer_navn:
                    print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 04 (Social Media Stalker) på: {ejer_navn}{C.RESET}")
                    try:
                        from modules.mod_04_social import SocialMediaProfiler
                        soc = SocialMediaProfiler(ejer_navn)
                        soc.run(driver)
                        self.results["Samlet_Pivot_Data"]["Social_Media"] = soc.data
                        print(f"{C.GREEN}  ✓ Modul 04 data tilføjet.{C.RESET}")
                    except ImportError:
                        print(f"{C.DIM}  [-] Modul 04 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 04 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 05: OFFLINE DB PIVOT ---
                if ejer_navn or ejer_email:
                    print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 05 (Offline DB) på: {ejer_navn} / {ejer_email}{C.RESET}")
                    try:
                        from modules.mod_05_offline import OfflineDBAnalyst
                        off_query = ejer_email if ejer_email else ejer_navn
                        off_db = OfflineDBAnalyst(off_query)
                        off_db.run(driver)
                        self.results["Samlet_Pivot_Data"]["Offline_DB"] = off_db.data
                        print(f"{C.GREEN}  ✓ Modul 05 data tilføjet.{C.RESET}")
                    except ImportError:
                        print(f"{C.DIM}  [-] Modul 05 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 05 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 07: PHONE PIVOT ---
                if ejer_telefon:
                    print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 07 (Telefon-Opslag) på: {ejer_telefon}{C.RESET}")
                    try:
                        from modules.mod_07_phone import PhoneIntelligenceAnalyst
                        phone_check = PhoneIntelligenceAnalyst(ejer_telefon)
                        phone_check.run(driver)
                        self.results["Samlet_Pivot_Data"]["Phone_Data"] = phone_check.data
                        print(f"{C.GREEN}  ✓ Telefon data tilføjet.{C.RESET}")
                    except ImportError:
                        print(f"{C.DIM}  [-] Modul 07 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 07 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 09: DARKWEB PIVOT ---
                if ejer_navn or ejer_email:
                    print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 09 (Darkweb Scanner) på: {ejer_navn} / {ejer_email}{C.RESET}")
                    try:
                        from modules.mod_09_darkweb import DarkwebScanner 
                        dw_query = ejer_email if ejer_email else ejer_navn
                        dw = DarkwebScanner(dw_query)
                        dw.run(driver)
                        self.results["Samlet_Pivot_Data"]["Darkweb"] = dw.data
                        print(f"{C.GREEN}  ✓ Modul 09 data tilføjet.{C.RESET}")
                    except ImportError:
                        print(f"{C.DIM}  [-] Modul 09 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 09 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 17: SNIPER PIVOT ---
                if ejer_navn and ejer_email:
                    print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 17 (Sniper) på: {ejer_navn} / {ejer_email}{C.RESET}")
                    try:
                        from modules.mod_17_sniper import SniperModule
                        sniper = SniperModule(ejer_navn, ejer_email)
                        sniper.run(driver)
                        self.results["Samlet_Pivot_Data"]["Sniper_Data"] = sniper.data
                        print(f"{C.GREEN}  ✓ Modul 17 Sniper fuldført.{C.RESET}")
                    except ImportError:
                        print(f"{C.DIM}  [-] Modul 17 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                    except Exception as e:
                        print(f"{C.DIM}  [-] Modul 17 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 23: MATRIX PIVOT ---
                print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 23 (Matrix Correlation)...{C.RESET}")
                try:
                    from modules.mod_23_matrix import MatrixAnalyzer
                    matrix = MatrixAnalyzer(self.results["Samlet_Pivot_Data"])
                    matrix.run()
                    self.results["Samlet_Pivot_Data"]["Matrix_Analysis"] = matrix.data
                    print(f"{C.GREEN}  ✓ Modul 23 Matrix fuldført.{C.RESET}")
                except ImportError:
                        print(f"{C.DIM}  [-] Modul 23 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                except Exception as e:
                    print(f"{C.DIM}  [-] Modul 23 overprunget/fejl: {e}{C.RESET}")

                # --- MODUL 29: REPORT BUILDER ---
                print(f"\n{C.CYAN}[*] PIVOT -> Kører Modul 29 (Final Report Builder)...{C.RESET}")
                try:
                    from modules.mod_29_report import ReportGenerator
                    report = ReportGenerator(self.results)
                    report.generate()
                    print(f"{C.GREEN}  ✓ Modul 29 Rapport genereret.{C.RESET}")
                except ImportError:
                        print(f"{C.DIM}  [-] Modul 29 mangler lokalt eller navngivningsfejl. Springer over.{C.RESET}")
                except Exception as e:
                    print(f"{C.DIM}  [-] Modul 29 overprunget/fejl: {e}{C.RESET}")

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

        if not api_success and not self.is_cvr:
            print(f"{C.YELLOW}    [*] API blokeret. Prøver DuckDuckGo HTML Scraper for CVR-data...{C.RESET}")
            dork = f'site:virk.dk "{self.input_query}"'
            links = omni_dork_search(self.driver_ref, dork, max_links=3) if hasattr(self, 'driver_ref') else []
            
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
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            res = requests.get(url, headers=headers, timeout=10)
            links = re.findall(r'href="([^"]+)"', res.text)
            clean_links = [urllib.parse.unquote(l.split('uddg=')[1].split('&')[0]) for l in links if 'uddg=' in l]
            if clean_links:
                print(f"{C.GREEN}      ✓ DuckDuckGo leverede resultater udenom Google!{C.RESET}")
            return clean_links[:5]
        except Exception:
            return []

    def _bypass_google_dorking(self):
        if self.is_cvr:
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
        
        domain = None
        bad_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.dk", "icloud.com", "ownr.dk", "virk.dk", "proff.dk", "sentry.io"]
        
        for email in self.results.get("Deep_Scrape_Emails", []):
            extracted_domain = email.split('@')[-1].lower()
            if extracted_domain not in bad_domains:
                domain = extracted_domain
                print(f"\n{C.YELLOW}[*] Hunter.io: Fandt internt domæne via Deep Scrape ({domain})...{C.RESET}")
                break
                
        if not domain and self.name != "Ukendt Virksomhed":
            domain = self.name.lower().replace(' ', '') + ".com"
            print(f"\n{C.YELLOW}[*] Hunter.io: Genererer automatisk formodet domæne ({domain})...{C.RESET}")
            
        if not domain:
            print(f"\n{C.DIM}[-] Springer Hunter over (Mangler domæne at søge på){C.RESET}")
            return None

        print(f"{C.YELLOW}[*] Udfører Corporate Domain Search på '{domain}'...{C.RESET}")
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
        if driver:
            dork = f'site:proff.dk OR site:ownr.dk OR site:virk.dk "{self.name}"'
            links = omni_dork_search(driver, dork, max_links=5)
            if not links:
                links_urls = self._duckduckgo_html_search(dork)
                links = [{"url": u, "title": "", "snippet": ""} for u in links_urls]

            if links:
                print(f"{C.GREEN}    ✓ Fandt regnskabs/netværks-data!{C.RESET}")
                for link in links:
                    self.results["Proff_Links"].append(link['url'])
            else:
                print(f"{C.DIM}    [-] Intet fundet på Proff/Ownr/Virk.{C.RESET}")

    def _check_statstidende(self, driver):
        print(f"\n{C.YELLOW}[*] Dorking Statstidende for juridiske advarsler...{C.RESET}")
        if driver:
            search_term = self.input_query if self.is_cvr else f'"{self.name}"'
            dork = f'site:statstidende.dk {search_term}'
            links = omni_dork_search(driver, dork, max_links=3)
            if links:
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
        print(f"\n{C.YELLOW}[*] GOLIATH CLUSTER-DORKING (Lynhurtig Krydssøgning på 30+ domæner)...{C.RESET}")
        if not driver: return
        
        international_sites = [
            "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", 
            "twitter.com", "x.com", "reddit.com/user", "pinterest.com", 
            "youtube.com", "twitch.tv", "steamcommunity.com/id", 
            "tinder.com", "badoo.com", "vk.com", "medium.com", "github.com",
            "t.me", "vimeo.com", "soundcloud.com", "snapchat.com/add"
        ]
        
        danish_sites = [
            "dba.dk", "guloggratis.dk", "scor.dk", "dating.dk", 
            "holdet.dk", "amino.dk", "hardwareonline.dk", "studieportalen.dk", 
            "trustpilot.com/users", "kino.dk", "boligportal.dk", "heste-nettet.dk", "trendsales.dk"
        ]

        all_sites = international_sites + danish_sites
        site_chunks = [all_sites[i:i + 17] for i in range(0, len(all_sites), 17)] 
        
        raw_queries = []
        if self.results.get("Erhvervs_Netværk"): raw_queries.append(self.results["Erhvervs_Netværk"][0])
        if self.results.get("Deep_Scrape_Telefoner"): raw_queries.append(self.results["Deep_Scrape_Telefoner"][0])
        if self.results.get("Deep_Scrape_Emails"): raw_queries.append(self.results["Deep_Scrape_Emails"][0])
        if self.results.get("Deep_Scrape_Adresser"): 
            clean_addr = self.results["Deep_Scrape_Adresser"][0].split(',')[0].strip()
            raw_queries.append(clean_addr)
        
        raw_queries = list(set(raw_queries))
        
        if not raw_queries:
            print(f"{C.DIM}    [-] Intet person-data at krydssøge med.{C.RESET}")
            return
            
        combined_query_str = " OR ".join([f'"{q}"' for q in raw_queries])
        print(f"{C.DIM}    -> Kombineret Payload: {combined_query_str}{C.RESET}")
        
        found_any = False
        for chunk in site_chunks:
            site_dork = " OR ".join([f"site:{s}" for s in chunk])
            full_dork = f'({site_dork}) ({combined_query_str})'
            
            links = omni_dork_search(driver, full_dork, max_links=5)
            if links:
                found_any = True
                print(f"{C.GREEN}    🔥 Fandt Social/Dark hits!{C.RESET}")
                for link in links:
                    if link['url'] not in self.results["Trustpilot_Social_Hits"]:
                        print(f"      -> {link['url']}")
                        self.results["Trustpilot_Social_Hits"].append(link['url'])
                            
        if not found_any:
            print(f"{C.DIM}    [-] Krydssøgning gav ingen åbenlyse hits på tværs af de 33 platforme.{C.RESET}")

    # NY V7 TILFØJELSE: Kort-generering
    def _generate_maps_links(self):
        for addr in self.results.get("Deep_Scrape_Adresser", []):
            encoded = urllib.parse.quote(addr)
            link = f"https://www.google.com/maps/search/?api=1&query={encoded}"
            if link not in self.results.setdefault("Maps_Links", []):
                self.results["Maps_Links"].append(link)
                print(f"{C.CYAN}      -> Google Maps Link: {link}{C.RESET}")

    # NY V7 TILFØJELSE: Archive.org API
    def _check_wayback_machine(self):
        domain = None
        for em in self.results.get("Deep_Scrape_Emails", []):
            d = em.split('@')[-1]
            if d not in ["gmail.com", "hotmail.com", "yahoo.com", "live.dk"]:
                domain = d
                break
        
        if not domain and self.name != "Ukendt Virksomhed":
            domain = self.name.lower().replace(" ", "") + ".dk"
            
        if domain:
            print(f"\n{C.YELLOW}[*] Tjekker Wayback Machine for historiske snapshots af '{domain}'...{C.RESET}")
            url = f"http://archive.org/wayback/available?url={domain}"
            try:
                res = requests.get(url, timeout=5).json()
                if res.get("archived_snapshots", {}).get("closest"):
                    snap = res["archived_snapshots"]["closest"]["url"]
                    self.results.setdefault("Wayback_Machine", []).append(snap)
                    print(f"{C.GREEN}    🔥 Fandt historisk snapshot! Link: {snap}{C.RESET}")
                else:
                    print(f"{C.DIM}    [-] Ingen snapshots fundet for domænet.{C.RESET}")
            except:
                pass

    def _extract_cvr_and_roles(self, text, url):
        cvr_matches = re.findall(r'\b(?:CVR|cvr)[\s:-]*(\d{8})\b', text)
        for cvr in cvr_matches:
            if cvr not in self.results.get("CVR_Intel", [{}])[0].get("CVR", ""): 
                print(f"{C.CYAN}      -> Sekundært CVR-Nummer detekteret i netværket: {cvr}{C.RESET}")

    def _google_broad_fallback(self, driver):
        if driver:
            dork = f'"{self.input_query}" OR "cvr: {self.input_query}"'
            links = omni_dork_search(driver, dork, max_links=3)
            if not links:
                links_urls = self._duckduckgo_html_search(dork)
                links = [{"url": u, "title": "", "snippet": ""} for u in links_urls]

            if links:
                for link in links:
                    if "ownr" in link['url'] or "virk" in link['url'] or "proff" in link['url']:
                        self.results["Proff_Links"].append(link['url'])

    def _deep_scrape_company_links(self, driver):
        print(f"\n{C.YELLOW}[*] Deep Scrape: Går direkte ind på fundne profiler for at hente skjult data...{C.RESET}")
        if not driver: return
        
        for url in list(set(self.results.get("Proff_Links", [])))[:6]:
            print(f"{C.DIM}    -> Åbner og scraper: {url}{C.RESET}")
            try:
                driver.get(url)
                time.sleep(4)
                
                try:
                    for btn in driver.find_elements(By.TAG_NAME, "button"):
                        if any(x in btn.text.lower() for x in ["accept", "tillad", "godkend", "ok"]):
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1)
                            break
                except: pass
                
                page_title = driver.title
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                html_source = driver.page_source
                
                bad_email_domains = ["ownr.dk", "virk.dk", "proff.dk", "sentry.io"]
                hidden_emails = re.findall(r'mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', html_source)
                for em in set(hidden_emails):
                    if em.lower() not in self.results.setdefault("Deep_Scrape_Emails", []) and not any(ext in em.lower() for ext in [".png", ".jpg", "sentry"] + bad_email_domains):
                        self.results["Deep_Scrape_Emails"].append(em.lower())
                        print(f"{C.CYAN}      ✓ Skjult Email fundet i Kildekode: {em.lower()}{C.RESET}")

                bad_phones = [self.input_query, "36408820", "70200000", "72200000"]
                hidden_phones = re.findall(r'tel:(?:\+45|45|0045)?\s*([2-9]\d{7}|[2-9]\d{1}\s\d{2}\s\d{2}\s\d{2})', html_source)
                for ph in set(hidden_phones):
                    clean_ph = ph.replace(" ", "")
                    if len(clean_ph) == 8 and clean_ph not in self.results.setdefault("Deep_Scrape_Telefoner", []) and clean_ph not in bad_phones:
                        self.results["Deep_Scrape_Telefoner"].append(clean_ph)
                        print(f"{C.CYAN}      ✓ Skjult Telefon fundet i Kildekode: {clean_ph}{C.RESET}")
                
                if self.name == "Ukendt Virksomhed" and self.is_cvr:
                    parts = page_title.split('-')
                    if parts and len(parts[0].strip()) > 2:
                        pot_name = parts[0].strip()
                        if "just a moment" not in pot_name.lower() and "cloudflare" not in pot_name.lower() and "attention required" not in pot_name.lower():
                            self.name = pot_name
                            self.results["Mål"] = self.name
                            print(f"{C.GREEN}      ✓ Firmanavn reddet via Deep Scrape: {self.name}{C.RESET}")
                
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]

                bad_names = ["se selskabsdiagram", "legale ejere", "reelle ejere", "ejerhistorik", "dk", "direktion", "bestyrelse", "log ind opret", "log ind", "opret", "vis mere", "ejerandel", "fuldt ansvarlig deltager", "registreret på cvr.dk", "et resumé for virksomheden", "deltager", "resume", "nej ja", "ja nej", "ja", "nej", "ownr holder dig opdateret", "ownr holder", "holder dig opdateret", self.name.lower(), self.input_query.lower()]
                
                for i, line in enumerate(lines):
                    if any(x in line.lower() for x in ["ejerandel", "fuldt ansvarlig", "reelle ejere", "direktør", "stifter"]):
                        for j in range(i-1, max(-1, i-10), -1):
                            pot_name = lines[j]
                            if " " in pot_name and not any(c.isdigit() for c in pot_name) and not any(bad in pot_name.lower() for bad in bad_names) and not pot_name.isupper():
                                if pot_name not in self.results["Erhvervs_Netværk"]:
                                    self.results["Erhvervs_Netværk"].append(pot_name)
                                    print(f"{C.CYAN}      ✓ Ejer/Netværk præcist udtrukket: {pot_name}{C.RESET}")
                                break 

                owners_lower = [o.lower() for o in self.results.get("Erhvervs_Netværk", [])]
                bad_address_strings = ["stiftet", "status", "cvr", "telefon", "adresse", "p-nr", "tilføj", "nordkicks", "postnummer og by", self.name.lower()] + owners_lower
                for i, line in enumerate(lines):
                    zip_match = re.search(r'\b(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ]+)\b', line)
                    if zip_match:
                        zip_city = zip_match.group(0)
                        street = lines[i-1] if i > 0 else ""
                        
                        if len(street) > 3 and not any(x in street.lower() for x in bad_address_strings):
                            full_addr = f"{street}, {zip_city}"
                            if full_addr not in self.results["Deep_Scrape_Adresser"]:
                                self.results["Deep_Scrape_Adresser"].append(full_addr)
                                print(f"{C.GREEN}      ✓ Præcis Adresse fundet: {full_addr}{C.RESET}")

            except Exception as e:
                print(f"{C.DIM}      [-] Kunne ikke deep-scrape {url}{C.RESET}")

    def save(self):
        os.makedirs(session["loot_folder"], exist_ok=True)
        clean_name = self.input_query.replace(' ', '_').replace('.', '_')
        filename = f"{session['loot_folder']}/02_BUSINESS_{clean_name}.json"
        
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

        Path(filename).write_text(json.dumps(self.results, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"\n{C.GREEN}[✓] Rapport gemt (Overskrevet succesfuldt): {filename}{C.RESET}")