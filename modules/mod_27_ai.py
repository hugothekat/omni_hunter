import json
import requests
from core.utils import C

class TitanAIEnrichment:
    """Kører rå tekst gennem en lokal LLM (Ollama) for at finde skjult kontekst."""
    def __init__(self, model="llama3"):
        self.model = model
        self.api_url = "http://localhost:11434/api/generate"

    def analyze_text(self, text):
        if not text or len(text) < 20:
            return {}

        # Vi begrænser teksten for at undgå at overbelaste den lokale model
        safe_text = text[:4000] 

        prompt = """
        Du er en cyber-efterforsker. Analyser følgende tekst og uddrag de vigtigste entiteter.
        Returner KUN et validt JSON-objekt med følgende nøgler: 'navne' (liste), 'adresser' (liste), 
        'organisationer' (liste), og 'mistænkelig_adfærd' (kort string opsummering).
        Tekst:
        """ + safe_text

        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False
        }

        try:
            res = requests.post(self.api_url, json=payload, timeout=60).json()
            return json.loads(res.get("response", "{}"))
        except requests.exceptions.ConnectionError:
            print(f"{C.DIM}    [AI Offline] Ollama kører ikke på localhost:11434{C.RESET}")
            return {}
        except Exception as e:
            print(f"{C.DIM}    [AI Fejl] {e}{C.RESET}")
            return {}