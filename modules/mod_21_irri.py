# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V36: CALL FORM TRACKER
📌 Formål: Passiv analyse af hjemmesider for at opspore "Ring mig op"-formularer og Lead Gen felter.
"""
import sys
import re
import random
import urllib.parse
import requests
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
import concurrent.futures
from bs4 import BeautifulSoup

from core.base_module import BaseModule, ModuleCategory
from core.utils import C
from core.browser import OmniHunterBrowser, BrowserConfig
from core.network import omni_dork_search

class CallFormTracker(BaseModule):
    """
    GOLIATH V40: LEAD-GEN INTELLIGENCE ENGINE
    Scanner danske hjemmesider for kontaktformularer og auto-udfylder dem med
    genereret data (Faker) for at teste lead-gen flows. Understøtter passiv DOM-analyse,
    dybdegående scoring og aktiv injektion.
    """
    def __init__(self, urls: str = "", phone_number: str = "", mode: str = "analysis"):
        super().__init__()
        self.name = "LEAD-GEN INTELLIGENCE ENGINE V40"
        self.description = "Dyb DOM-analyse af kontaktformularer, Network Surface Mapping og Auto-Fill."
        self.category = ModuleCategory.NETWORK
        
        self.phone_number = phone_number or "+4512345678"
        self.mode = mode.lower() if mode.lower() in ["passive", "analysis", "active"] else "analysis"
        self._lock = threading.Lock()
        
        try:
            from faker import Faker
            self.fake = Faker("da_DK")
        except ImportError as e:
            # =================================================================
            # NYT V37: ADVANCED DEPENDENCY DIAGNOSTICS & AUTO-HEAL
            # =================================================================
            print(f"\n{C.YELLOW}[!] Afhængighedsfejl: 'faker' mangler i det aktuelle Python-miljø.{C.RESET}")
            print(f"{C.DIM}    -> Detekteret Miljø: {sys.prefix}{C.RESET}")
            print(f"{C.DIM}    -> Traceback: {str(e)}{C.RESET}")
            
            from core.utils import auto_install_package
            if auto_install_package("faker"):
                from faker import Faker
                self.fake = Faker("da_DK")
                print(f"{C.GREEN}    [+] 'faker' blev auto-installeret og indlæst live!{C.RESET}\n")
            else:
                print(f"{C.RED}    [-] Auto-Heal fejlede. Bruger hardcodede fallback navne.{C.RESET}\n")
                self.fake = None
                
        self.danish_names = [self.fake.name() for _ in range(15)] if self.fake else ["Jens Jensen", "Lars Nielsen", "Mette Sørensen", "Hanne Petersen"]
        
        self.field_mappings = {
            "name": ["navn", "name", "fornavn", "efternavn", "fullname", "fname", "lname"],
            "email": ["email", "mail", "e-mail", "epost"],
            "phone": ["telefon", "tlf", "phone", "mobil", "nummer"]
        }

        # Mønstre vi aktivt leder efter uanset formatering
        self.cta_patterns = [
            r"bed om et opkald", r"ring mig op", r"bliv kontaktet", 
            r"vi ringer dig op", r"kontakt mig", r"book et opkald", 
            r"få et gratis opkald", r"bliv ringet op", r"call me back"
        ]
        
        # Initial data struktur
        self.urls_to_scan = [u.strip() for u in urls.split(",")] if urls else []
        self.data = {
            "Meta": {
                "Module": self.name,
                "Version": "V40",
                "Mode": self.mode,
                "Total_Forms_Found": 0
            },
            "Scannede_Mål": self.urls_to_scan,
            "Side_Statistik": {
                "Med_Formular": 0,
                "Uden_Formular": 0,
                "Med_Telefonfelt": 0,
                "Med_Stærk_CTA": 0
            },
            "Dorking_Metrics": {
                "Dorking_Kilde": "omni_dork_search",
                "Dorking_Queries": [],
                "Dorking_Results_Count": 0
            },
            "Network_Surface": {
                "Form_Endpoints": []
            },
            "Fundne_Sider_Med_Opkalds_Formular": [],
            "Detaljeret_Analyse": [],
            "Fetch_Log": []
        }

    def _determine_page_type(self, url: str, title: str) -> str:
        url_l = url.lower()
        title_l = title.lower()
        if any(x in url_l or x in title_l for x in ['kontakt', 'contact', 'os']): return "Kontakt"
        if any(x in url_l or x in title_l for x in ['book', 'booking', 'møde', 'aftale']): return "Booking"
        if any(x in url_l or x in title_l for x in ['tilbud', 'pris', 'quote', 'beregn']): return "Lead Gen / Tilbud"
        if any(x in url_l or x in title_l for x in ['support', 'hjælp', 'faq']): return "Support"
        return "Generel / Ukendt"

    def _deep_form_intelligence(self, html: str, url: str) -> Optional[Dict]:
        """Deep DOM-parsing ved hjælp af BeautifulSoup for at kortlægge alle input-felter passivt."""
        soup = BeautifulSoup(html, "html.parser")
        page_text_lower = soup.get_text(separator=' ').lower()
        
        # Page Context Intelligence
        page_title = soup.title.string.strip() if soup.title else "Ingen Titel"
        h1_tag = soup.find('h1')
        page_h1 = h1_tag.get_text(strip=True) if h1_tag else "Ingen H1"
        page_type = self._determine_page_type(url, page_title)
        
        # 1. Led efter CTA'er i hele sidens tekst for at fange JavaScript-genererede blokke
        found_ctas = set()
        for pattern in self.cta_patterns:
            if re.search(pattern, page_text_lower):
                found_ctas.add(pattern)

        page_forms_data = []
        has_any_call_forms = False

        # 2. Iterér over alle fysiske HTML forms
        forms = soup.find_all('form')
        page_network_endpoints = set()

        for idx, form in enumerate(forms):
            form_text = form.get_text(separator=' ').lower()
            fields = []
            req_fields = []
            has_phone_field = False
            
            action_endpoint = urllib.parse.urljoin(url, form.get('action', ''))
            method = form.get('method', 'get').upper()
            page_network_endpoints.add(action_endpoint)
            
            # Find alle inputtyper (input, textarea, select)
            for input_element in form.find_all(['input', 'textarea', 'select']):
                name = input_element.get('name', 'ukendt_name')
                i_type = input_element.get('type', 'text')
                placeholder = input_element.get('placeholder', '')
                is_req = input_element.get('required') is not None or '*' in placeholder or '*' in name
                
                fields.append(f"{name} (type: {i_type})")
                if is_req: req_fields.append(name)
                
                # Heuristik: Er dette et telefon-felt?
                if i_type == "tel" or any(x in name.lower() or x in placeholder.lower() for x in ['tlf', 'telefon', 'phone', 'mobil']):
                    has_phone_field = True
            
            # Find Knap Tekst
            buttons = form.find_all(['button', 'input'])
            btn_texts = [b.get_text(strip=True) for b in buttons if b.name == 'button']
            btn_texts += [b.get('value', '') for b in buttons if b.name == 'input' and b.get('type') in ['submit', 'button']]
            
            # CTA Intelligence
            form_ctas = [cta for cta in self.cta_patterns if re.search(cta, form_text)]
            cta_matches = list(set(form_ctas) | found_ctas)
            cta_count = len(cta_matches)
            cta_strength = "Høj" if cta_count > 2 else "Mellem" if cta_count > 0 else "Lav"
            
            # Vurder formålet
            form_purpose = "Standard Kontakt"
            if "book" in form_text: form_purpose = "Booking"
            elif cta_count > 0: form_purpose = "Lead Generation"
            
            # Udregn Lead Intelligence Score
            score = 10
            if has_phone_field: score += 30
            if cta_strength in ["Mellem", "Høj"]: score += 20 + (10 * cta_count)
            if page_type in ["Lead Gen / Tilbud", "Booking"]: score += 20
            if 0 < len(req_fields) <= 4: score += 10 # Lav friktion er godt for leads
            score = min(100, score)
            
            # Logikkrav fra bruger: Kun udtræk sider med formularer der tilskynder opkald
            if has_phone_field or cta_count > 0 or self.mode == "analysis":
                has_any_call_forms = True
                page_forms_data.append({
                    "Formular_ID": form.get('id', f"Form_{idx}"),
                    "Formular_Type": form_purpose,
                    "Felter": fields,
                    "Antal_Påkrævede_Felter": len(req_fields),
                    "Påkrævede_Felter": req_fields,
                    "Telefon_Felt_Findes": has_phone_field,
                    "Knap_Tekster": [b for b in btn_texts if b],
                    "CTA_Match_Count": cta_count,
                    "CTA_Strength": cta_strength,
                    "Fundne_Opkalds_Indikatorer": cta_matches,
                    "Lead_Intelligence_Score": score,
                    "Submit_Endpoint": action_endpoint,
                    "Submit_Method": method
                })
        
        if has_any_call_forms:
            return {
                "URL": url,
                "Side_Context": {
                    "Side_Type": page_type,
                    "Side_Title": page_title,
                    "Primær_Overskrift": page_h1,
                    "Side_CTA_Overview": {"total_matches": len(found_ctas), "unique_patterns": list(found_ctas)}
                },
                "Network_Surface": {"Form_Endpoints": list(page_network_endpoints)},
                "Formularer": sorted(page_forms_data, key=lambda x: x['Lead_Intelligence_Score'], reverse=True)
            }
        return None

    def _scrape_danish_domains(self, driver) -> List[str]:
        """Auto-indsamler danske domæner (.dk) hvis intet target er givet."""
        print(f"{C.YELLOW}[*] Ingen mål angivet. Eksekverer Dorking for at finde danske Lead-Gen sider...{C.RESET}")
        danish_domains = []
        queries = ['site:.dk "ring mig op"', 'site:.dk "bliv kontaktet"', 'site:.dk "book et opkald"']
        if driver:
            for q in queries:
                self.data["Dorking_Metrics"]["Dorking_Queries"].append(q)
                hits = omni_dork_search(driver, q, max_links=5)
                for hit in hits:
                    if hit['url'] not in danish_domains: danish_domains.append(hit['url'])
            self.data["Dorking_Metrics"]["Dorking_Results_Count"] = len(danish_domains)
        if not danish_domains:
            danish_domains = ["https://eksempel.dk/kontakt"]
        return danish_domains

    def _fill_and_submit_form(self, form: BeautifulSoup, url: str) -> Optional[Dict]:
        """Detekterer formularfelter og auto-udfylder med syntetisk dansk data."""
        form_data = {}
        fields = form.find_all(['input', 'textarea', 'select'])
        
        for field in fields:
            field_name = field.get('name', '').lower()
            if not field_name: continue
            
            if any(m in field_name for m in self.field_mappings["name"]):
                form_data[field_name] = random.choice(self.danish_names)
            elif any(m in field_name for m in self.field_mappings["email"]):
                form_data[field_name] = self.fake.email() if self.fake else f"test_{random.randint(100,999)}@test.dk"
            elif any(m in field_name for m in self.field_mappings["phone"]):
                form_data[field_name] = self.phone_number
            else:
                if field.get('required') is not None:
                    form_data[field_name] = "Test Forespørgsel fra GOLIATH"

        if form_data:
            method = form.get('method', 'get').lower()
            action = form.get('action', '')
            submit_url = urllib.parse.urljoin(url, action)
            
            print(f"{C.CYAN}    [*] Auto-udfylder formular på {submit_url} med payload: {form_data.get('email', 'ukendt')}...{C.RESET}")
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                if method == "post":
                    response = requests.post(submit_url, data=form_data, headers=headers, timeout=10)
                else:
                    response = requests.get(submit_url, params=form_data, headers=headers, timeout=10)
                
                print(f"{C.GREEN}    [+] Formular indsendt succesfuldt! (Status: {response.status_code}){C.RESET}")
                return {"status": response.status_code, "payload": form_data, "target_endpoint": submit_url}
            except Exception as e:
                print(f"{C.RED}    [!] Formular indsendelse fejlede: {e}{C.RESET}")
        return None

    def _process_url(self, url: str) -> None:
        """Sikker, isoleret fetch for hver URL. Udnytter stealth-browsing med JS-rendering."""
        if not url.startswith("http"): url = f"https://{url}"
        
        if "." not in url.split("://")[-1]:
            print(f"{C.RED}    [!] Ugyldig URL sprunget over: {url}{C.RESET}")
            return
            
        print(f"{C.YELLOW}[*] Scraper og analyserer: {url}{C.RESET}")
        
        try:
            # Opret en isoleret instans med JS rendering aktiveret (Undetected Chromedriver / Playwright)
            config = BrowserConfig(headless=True, js_rendering=True, behavior_level="off")
            browser = OmniHunterBrowser(config)
            browser.start()

            res = browser.fetch(url) if hasattr(browser, 'fetch') else {"html": ""}
            html = res.get("html", "")
            if not html: return
            
            form_intel = self._analyze_dom_for_forms(html, url)
            
            if form_intel:
                print(f"{C.GREEN}    🔥 HIT: Fandt Lead-Gen formular(er) på {url}!{C.RESET}")
                self.data["Fundne_Sider_Med_Opkalds_Formular"].append(url)
                self.data["Detaljeret_Analyse"].append(form_intel)
            else:
                print(f"{C.DIM}    [-] Ingen opkalds-formularer detekteret på {url}.{C.RESET}")
            
            browser.close()

        except Exception as e:
            print(f"{C.RED}    [!] Fejl ved processering af {url}: {e}{C.RESET}")

    def _analyze_dom_for_forms(self, html: str, url: str) -> Optional[Dict]:
        """Wrapper til deep_form_intelligence for at overholde navngivning i _process_url."""
        return self._deep_form_intelligence(html, url)


    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        print(f"\n{C.CYAN}{'='*60}\n[32] DANISH CALL FORM AUTOFILL V37\n{'='*60}{C.RESET}")
        
        if target:
            self.urls_to_scan = [t.strip() for t in target.split(',')]
            self.data["Scannede_Mål"] = self.urls_to_scan
            
        if not self.urls_to_scan:
            self.urls_to_scan = self._scrape_danish_domains(driver)
            self.data["Scannede_Mål"] = self.urls_to_scan
            
        if not self.urls_to_scan:
            print(f"{C.RED}[!] Ingen URL'er angivet eller fundet via Dorking.{C.RESET}")
            return self.data
            
        print(f"{C.YELLOW}[*] Starter asynkron dybdeanalyse af {len(self.urls_to_scan)} mål for Lead-Gen logik...{C.RESET}")

        # Brug ThreadPoolExecutor til parallel håndtering for hastighed
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self._process_url, self.urls_to_scan)

        # Output Summary
        print(f"\n{C.CYAN}--- TACTICAL LEAD-GEN SUMMARY ---{C.RESET}")
        print(f"[{C.WHITE}*{C.RESET}] Mål Scannet: {len(self.urls_to_scan)} (Fejl/Tomme: {len([x for x in self.data['Fetch_Log'] if x['status'] != 'OK'])})")
        print(f"[{C.GREEN}+{C.RESET}] Sider m. Formular: {self.data['Side_Statistik']['Med_Formular']}")
        print(f"[{C.MAGENTA}+{C.RESET}] Unikke Endpoints: {len(self.data['Network_Surface']['Form_Endpoints'])}")
        
        if self.data["Detaljeret_Analyse"]:
            print(f"\n{C.WHITE}{'URL'.ljust(35)} | {'Forms'.ljust(5)} | {'Tlf Felt'.ljust(9)} | {'Stærk CTA'.ljust(10)} | {'Score'}{C.RESET}")
            print("-" * 75)
            
        for analyse in self.data["Detaljeret_Analyse"]:
            url_trunc = analyse["URL"][:32] + "..." if len(analyse["URL"]) > 35 else analyse["URL"].ljust(35)
            f_count = str(len(analyse["Formularer"])).ljust(5)
            
            best_form = analyse["Formularer"][0] # Vi sorterede dem efter score tidligere
            tlf_felt = f"{C.GREEN}Ja{C.RESET}      " if best_form["Telefon_Felt_Findes"] else f"{C.DIM}Nej{C.RESET}     "
            cta_str = f"{C.YELLOW}{best_form['CTA_Strength'].ljust(10)}{C.RESET}" if best_form['CTA_Strength'] != "Lav" else f"{C.DIM}Lav       {C.RESET}"
            score = f"{C.RED if best_form['Lead_Intelligence_Score'] > 70 else C.GREEN}{best_form['Lead_Intelligence_Score']}{C.RESET}"
            
            print(f"{url_trunc} | {f_count} | {tlf_felt} | {cta_str} | {score}")

        # GOLIATH V36 STANDARD: Vi gemmer resultatet automatisk og sikkert
        from core.utils import sanitize_filename
        identifier = sanitize_filename("BATCH_SCAN" if len(self.urls_to_scan) > 1 else self.urls_to_scan[0])
        self.save_to_loot(f"21_LEADGEN_{identifier}.json")
        
        return self.data
