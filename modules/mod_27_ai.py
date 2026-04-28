# -*- coding: utf-8 -*-
import json
import requests
import re
from core.utils import C
from core.network import CONFIG

class TitanAIEnrichment:
    """GOLIATH V8: Deep Forensic Context Engine via lokal LLM (Ollama)"""
    def __init__(self):
        # Henter model fra config, falder tilbage til llama3 hvis ikke sat
        self.model = CONFIG.get("ai_model", "llama3")
        self.api_url = "http://localhost:11434/api/generate"
        self.is_online = self._check_ollama_status()

    def _check_ollama_status(self):
        """Tjekker lynhurtigt om Ollama dæmonen kører lokalt"""
        try:
            res = requests.get("http://localhost:11434/", timeout=2)
            if res.status_code == 200:
                return True
        except Exception:
            pass
        return False

    def analyze_text(self, text):
        if not self.is_online:
            print(f"{C.DIM}    [AI Offline] Ollama kører ikke på localhost:11434. Skipper AI-analyse.{C.RESET}")
            return {}

        if not text or len(text) < 20:
            return {}

        print(f"{C.YELLOW}    [*] Fodrer tekst til Lokal AI ({self.model}) for Forensic Profiling...{C.RESET}")

        # Optimeret grænse for at sikre context window ikke sprænges (ca. 4000 tokens)
        safe_text = text[:12000] 

        prompt = """
        Du er en ekspert inden for cyber-efterforskning, trusselsvurdering og OSINT.
        Analyser følgende rå tekst/dokument og uddrag kritisk efterretningsdata.
        
        Du MÅ KUN returnere et validt JSON-objekt og INTET andet. Brug følgende præcise JSON-struktur:
        {
            "Navne_og_Aliaser": ["liste af unikke navne"],
            "Organisationer_og_Netværk": ["liste af firmaer/grupper"],
            "Lokationer": ["liste af fysiske steder"],
            "Psykologisk_Profil_Tone": "Kort opsummering af afsenderens tone (fx truende, manipulerende, stresset, formel)",
            "Skjult_Kontekst_Intent": "Hvad er den egentlige (muligvis skjulte) hensigt med teksten?",
            "Tidslinje_Events": ["Liste af datoer/møder/deadlines nævnt"],
            "Trusselsvurdering_1_til_10": [indsæt et tal fra 1 til 10, hvor 10 er kritisk/ulovligt]
        }
        
        Tekst der skal analyseres:
        """ + safe_text

        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1, # Meget lav temperatur for at undgå hallucinationer og sikre analytisk præcision
                "top_p": 0.9
            }
        }

        try:
            res = requests.post(self.api_url, json=payload, timeout=120).json()
            raw_response = res.get("response", "{}")
            
            # --- NY V8 TILFØJELSE: Sikker JSON Recovery ---
            # Lokale modeller kan nogle gange skrive tekst før/efter JSON objektet.
            json_match = re.search(r'\{.*\}', raw_url=raw_response.replace('\n', ''), flags=re.DOTALL)
            
            if json_match:
                clean_json = json_match.group(0)
                parsed_data = json.loads(clean_json)
                
                # Print et kort summary af AI'ens fund
                score = parsed_data.get('Trusselsvurdering_1_til_10', 0)
                color = C.RED if score > 7 else (C.YELLOW if score > 4 else C.GREEN)
                print(f"{color}    🔥 AI TRUSSELSVURDERING: {score}/10{C.RESET}")
                if parsed_data.get('Psykologisk_Profil_Tone'):
                    print(f"{C.MAGENTA}    -> Tone: {parsed_data['Psykologisk_Profil_Tone']}{C.RESET}")
                if parsed_data.get('Skjult_Kontekst_Intent'):
                    print(f"{C.CYAN}    -> Intent: {parsed_data['Skjult_Kontekst_Intent']}{C.RESET}")
                    
                return parsed_data
            else:
                # Fallback hvis regex fejler men den måske alligevel returnerede rent JSON
                return json.loads(raw_response)
                
        except json.JSONDecodeError:
            print(f"{C.RED}    [!] AI returnerede et ugyldigt format. Springer over.{C.RESET}")
            return {}
        except requests.exceptions.Timeout:
            print(f"{C.DIM}    [!] AI Analyse timeout (Teksten var måske for lang for maskinen).{C.RESET}")
            return {}
        except Exception as e:
            print(f"{C.DIM}    [AI Fejl] {e}{C.RESET}")
            return {}