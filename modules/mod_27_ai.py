# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER V36: AUTONOMOUS AI ANALYST
📌 Formål: Opsamler alle JSON-beviser og genererer en psykologisk/taktisk profil via LLM.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
import os
import requests
import re
import glob
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from core.base_module import BaseModule, ModuleCategory
from core.utils import C, session, datalake
from core.config_vault import vault

class TitanAIEnrichment(BaseModule):
    """GOLIATH V36: Deep Forensic Context Engine via lokal LLM (Ollama) eller API Fallback"""
    def __init__(self, target: str = ""):
        super().__init__()
        self.name = "AUTONOMOUS AI ANALYST (TITAN CORE)"
        self.description = "Sammenstykker og analyserer data fra alle moduler via AI."
        self.category = ModuleCategory.REPORTING
        
        self.target = target.strip()
        # Trækker indstillinger fra config
        config_data = vault.state if vault else {}
        self.model = config_data.get("ai_model", "llama3")
        self.api_url = "http://localhost:11434/api/generate"
        self.is_online = self._check_ollama_status()
        
        self.data = {
            "Target": self.target,
            "AI_Status": "Online" if self.is_online else "Offline",
            "Analyserede_Filer": 0,
            "Executive_Summary": {},
            "Timestamp": datetime.now().isoformat()
        }

    def _check_ollama_status(self) -> bool:
        """Tjekker lynhurtigt om Ollama dæmonen kører lokalt"""
        try:
            res = requests.get("http://localhost:11434/", timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    def _gather_intelligence(self) -> str:
        """Støvsuger loot-mappen for alt data omkrint target for at give AI'en kontekst."""
        loot_dir = session.get("loot_folder", "loot_evidence")
        if not os.path.exists(loot_dir): return ""
        
        gathered_data = {}
        files = glob.glob(os.path.join(loot_dir, "*.json"))
        
        print(f"{C.YELLOW}[*] Støvsuger {len(files)} bevis-filer for at fodre AI'en...{C.RESET}")
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # Hvis vores target er nævnt i filen, eller hvis intet target er givet
                    if not self.target or self.target.lower() in str(content).lower():
                        mod_name = os.path.basename(file).split('_')[1]
                        gathered_data[os.path.basename(file)] = content
                        self.data["Analyserede_Filer"] += 1
            except Exception: pass
            
        return json.dumps(gathered_data, ensure_ascii=False)

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Kernefunktionen der kommunikerer med LLM'en."""
        if not self.is_online:
            print(f"{C.DIM}    [AI Offline] Ollama kører ikke på localhost:11434. Tjek om dæmonen er startet.{C.RESET}")
            return {"Fejl": "AI Offline"}

        if not text or len(text) < 20:
            print(f"{C.DIM}    [-] For lidt data at analysere.{C.RESET}")
            return {"Fejl": "Insufficient Data"}

        print(f"{C.YELLOW}    [*] Fodrer samlet data til Lokal AI ({self.model}) for Forensic Profiling...{C.RESET}")

        # Optimeret grænse for at sikre context window ikke sprænges
        safe_text = text[:15000] 

        prompt = """
        Du er en ekspert inden for cyber-efterforskning, trusselsvurdering og OSINT for PET.
        Analyser følgende samlede JSON-data fra vores OSINT-værktøjer og uddrag kritisk efterretningsdata.
        
        Du MÅ KUN returnere et validt JSON-objekt og INTET andet. Brug følgende præcise JSON-struktur:
        {
            "Konklusion": "Et skarpt resumé af hvem/hvad target er",
            "Navne_og_Aliaser": ["liste af unikke navne/aliaser"],
            "Organisationer_og_Netværk": ["liste af firmaer/grupper"],
            "Lokationer": ["liste af fysiske steder"],
            "Psykologisk_Profil_Tone": "Kort opsummering af adfærd (hvis relevant ud fra data)",
            "Trusselsvurdering_1_til_10": 5
        }
        
        Data der skal analyseres:
        """ + safe_text

        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1, "top_p": 0.9}
        }

        try:
            res = requests.post(self.api_url, json=payload, timeout=180).json()
            raw_response = res.get("response", "{}")
            
            # Sikker JSON Recovery
            json_match = re.search(r'\{.*\}', raw_url=raw_response.replace('\n', ''), flags=re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                parsed_data = json.loads(clean_json)
                
                # Udskrivning
                score = parsed_data.get('Trusselsvurdering_1_til_10', 0)
                color = C.RED if score >= 7 else (C.YELLOW if score >= 4 else C.GREEN)
                print(f"{color}    🔥 AI TRUSSELSVURDERING: {score}/10{C.RESET}")
                if parsed_data.get('Konklusion'):
                    print(f"{C.CYAN}    -> Konklusion: {parsed_data['Konklusion']}{C.RESET}")
                if parsed_data.get('Psykologisk_Profil_Tone'):
                    print(f"{C.MAGENTA}    -> Profil: {parsed_data['Psykologisk_Profil_Tone']}{C.RESET}")
                    
                return parsed_data
            else:
                return json.loads(raw_response)
                
        except json.JSONDecodeError:
            print(f"{C.RED}    [!] AI returnerede et ugyldigt format.{C.RESET}")
        except requests.exceptions.Timeout:
            print(f"{C.DIM}    [!] AI Analyse timeout.{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [AI Fejl] {e}{C.RESET}")
        return {}

    def run(self, driver: Optional[Any] = None, target: str = "") -> Dict[str, Any]:
        """BaseModule compliance run-funktion."""
        if target: self.target = target
        self.data["Target"] = self.target

        print(f"\n{C.CYAN}{'='*60}\n[27] AUTONOMOUS AI ANALYST (TITAN CORE V36)\n{'='*60}{C.RESET}")
        
        # 1. Saml al data fra databasen
        raw_intel = self._gather_intelligence()
        
        # 2. Analyser
        analysis = self.analyze_text(raw_intel)
        if analysis:
            self.data["Executive_Summary"] = analysis
            
        # 3. Gem
        datalake.ingest(self.name, self.target, self.data)
        
        loot_dir = session.get("loot_folder", "loot_evidence")
        os.makedirs(loot_dir, exist_ok=True)
        out_path = Path(loot_dir) / f"27_AI_REPORT_{self.target.replace(' ', '_')}.json"
        out_path.write_text(json.dumps(self.data, indent=4, ensure_ascii=False), encoding="utf-8")
        
        print(f"\n{C.GREEN}[✓] AI Analyse fuldført og arkiveret.{C.RESET}")
        return self.data

# Backwards compatibility alias
TitanAIEnrichment = TitanAIEnrichment