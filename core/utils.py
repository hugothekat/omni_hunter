#!/usr/bin/env python3
"""
🚀 OMNI_HUNTER - ULTIMATE OSINT Utility Module v6.0 (THE WAF EDITION)
📌 Purpose: Core utilities for OSINT, security, data persistence, and automation.
🔧 Features:
   - FASTSAT: bleach v6.0+ kompatibilitet løst.
   - Unicode Homoglyph Normalization (NFKC).
   - Indbygget OmniWAF (SQLi, XSS, Path Traversal detektion).
   - In-Memory Rate Limiter Engine.
   - Bulletproof Boot Sequence & Dynamic Auto-Heal
   - Military-Grade Input Sanitization & PBKDF2 Encryption
   - Deep Threat Intel Extraction & JWT Decoder
   - PII Sanitizer & GDPR Redaction Engine
   - Binary Forensics Engine & SQLite Data Lake
"""

import os
import sys
import json
import csv
import logging
import asyncio
import hashlib
import base64
import sqlite3
import re
import socket
import subprocess
import math
import binascii
import unicodedata
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import List, Dict, Union, Optional, Any, Callable, Tuple, Set
from pathlib import Path

# ==========================================
# 🔹 1. ANSI STYLING & SESSION STATE
# ==========================================
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BG_RED = '\033[41m'
    RESET = '\033[0m'

session = {
    "name": "", 
    "city": "", 
    "email": "", 
    "phone": "",
    "username": "",
    "found_links": [],
    "loot_folder": "loot_evidence"
}

def get_input(prompt_text, session_key):
    val = input(f"{C.CYAN}{prompt_text}: {C.RESET}").strip()
    session[session_key] = val
    return val

# ==========================================
# 🔹 2. LOGGING ENGINE (INITIALISERES FØRST!)
# ==========================================
import structlog
structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO)
)
logger = structlog.get_logger()

# ==========================================
# 🔹 3. RATE LIMITER & LOCAL WAF
# ==========================================
class RateLimiter:
    """In-memory rate limiter for at beskytte mod spam og DoS."""
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.history = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        self.history[identifier] = [t for t in self.history[identifier] if now - t < self.period]
        if len(self.history[identifier]) >= self.calls:
            return False
        self.history[identifier].append(now)
        return True

class OmniWAF:
    """Lokal Web Application Firewall der opfanger ondsindede payloads før parsing."""
    SQLI_PATTERN = re.compile(r'(?i)(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC)\b|--|;)')
    XSS_PATTERN = re.compile(r'(?i)(<script>|javascript:|onerror=|onload=|eval\()')
    PATH_TRAVERSAL = re.compile(r'(\.\./|\.\.\\|/etc/passwd|\\Windows\\System32)')

    @classmethod
    def inspect(cls, payload: str) -> bool:
        if cls.SQLI_PATTERN.search(payload):
            logger.warning(f"OmniWAF: SQLi signature detected in payload: {payload[:50]}")
            raise ValueError("SQL Injection pattern detected.")
        if cls.XSS_PATTERN.search(payload):
            logger.warning(f"OmniWAF: XSS signature detected in payload: {payload[:50]}")
            raise ValueError("XSS pattern detected.")
        if cls.PATH_TRAVERSAL.search(payload):
            logger.warning(f"OmniWAF: Path Traversal detected in payload: {payload[:50]}")
            raise ValueError("Path Traversal pattern detected.")
        return True

# ==========================================
# 🔹 4. AUTO-HEAL DEPENDENCY SHIELD
# ==========================================
class DummyModule:
    def __init__(self, name: str):
        self._name = name

    def __getattr__(self, name):
        def _dummy_func(*args, **kwargs):
            logger.warning(f"Dummy fallback kaldt på manglende modul: {self._name}.{name}()")
            return {"error": f"Module '{self._name}' is missing. Feature disabled."}
        return _dummy_func
        
    def __bool__(self):
        return False

def auto_install_package(pip_name: str) -> bool:
    print(f"{C.YELLOW}[*] AUTO-HEAL: Forsøger at installere manglende afhængighed '{pip_name}'...{C.RESET}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{C.GREEN}    [+] Installation af {pip_name} fuldført!{C.RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{C.RED}    [-] Auto-Heal fejlede for {pip_name}. Kør manuelt: pip install {pip_name}{C.RESET}")
        return False

def safe_import(module_name: str, pip_name: Optional[str] = None):
    try:
        if "." in module_name:
            components = module_name.split('.')
            mod = __import__(module_name, fromlist=[components[-1]])
            return mod
        return __import__(module_name)
    except ImportError:
        target_pip = pip_name or module_name
        logger.warning(f"Missing dependency: {module_name}. Engaging Auto-Heal protocol.")
        if auto_install_package(target_pip):
            try:
                if "." in module_name:
                    components = module_name.split('.')
                    return __import__(module_name, fromlist=[components[-1]])
                return __import__(module_name)
            except ImportError: pass
        return DummyModule(module_name)

# --- UDFØRER SIKRE IMPORTS ---
import requests
import requests_cache
import bleach
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    from pydantic import BaseModel, field_validator as validator, ValidationError, Field
except ImportError:
    from pydantic import BaseModel, validator, ValidationError, Field

dns = safe_import('dns.resolver', 'dnspython')
whois = safe_import('whois', 'python-whois')
shodan = safe_import('shodan')
censys = safe_import('censys.search', 'censys')
netifaces = safe_import('netifaces')
Image = safe_import('PIL.Image', 'pillow')
ExifTags = safe_import('PIL.ExifTags', 'pillow')
pytesseract = safe_import('pytesseract')
pd = safe_import('pandas')
np = safe_import('numpy')

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    has_sklearn = True
except ImportError:
    logger.warning("Missing sklearn. AI Clustering disabled.")
    has_sklearn = False

# ==========================================
# 🔹 5. SYSTEM INITIALIZATION & CACHE
# ==========================================
load_dotenv()

requests_cache.install_cache(
    "omni_hunter_cache_v5",
    expire_after=86400,
    allowable_methods=["GET", "POST"],
    allowable_codes=[200, 404],
    stale_if_error=True,
    backend="sqlite",
    use_temp=False
)

SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
CENSYS_API_ID = os.getenv("CENSYS_API_ID")
CENSYS_API_SECRET = os.getenv("CENSYS_API_SECRET")

shodan_client = shodan.Shodan(SHODAN_API_KEY) if bool(shodan) and SHODAN_API_KEY else None
if bool(censys) and CENSYS_API_ID and CENSYS_API_SECRET:
    try:
        from censys.search import CensysHosts
        censys_client = CensysHosts(api_id=CENSYS_API_ID, api_secret=CENSYS_API_SECRET)
    except Exception:
        censys_client = None
else:
    censys_client = None

# ==========================================
# 🔹 6. SECURITY, CRYPTO & OPSEC
# ==========================================
class MilitarySafeInput(BaseModel):
    query: str = Field(..., max_length=500)
    
    @validator("query", mode='before')
    def military_sanitize(cls, v: str) -> str:
        # 1. Homoglyph Normalization
        normalized = unicodedata.normalize('NFKC', str(v))
        
        # 2. Local WAF Inspection
        OmniWAF.inspect(normalized)
        
        # 3. Bleach HTML Stripping (Fixed for v6.0+)
        sanitized = bleach.clean(normalized, tags=[], strip=True, attributes={}, strip_comments=True)
        
        # 4. Strict Regex Validation
        sanitized = re.sub(r"[^a-zA-Z0-9\-._@ ]", "", sanitized)
        
        if len(sanitized) > 500: raise ValueError("Input too long!")
        return sanitized

def military_sanitize_input(user_input: str) -> str:
    try:
        validated = MilitarySafeInput(query=user_input)
        return validated.query
    except ValidationError as e:
        logger.critical("MILITARY SECURITY BREACH ATTEMPT DETECTED", error=str(e))
        raise ValueError("🚨 SECURITY ALERT: Invalid or malicious input detected!")

class AdvancedCrypto:
    def __init__(self, master_password: Optional[str] = None):
        self.key_file = Path("omni_crypto.key")
        self.key = self._initialize_key(master_password)
        self.cipher = Fernet(self.key)

    def _initialize_key(self, password: Optional[str]) -> bytes:
        if password:
            salt = b'omni_hunter_salt_x99'
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
            return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        if self.key_file.exists(): return self.key_file.read_bytes()
        else:
            new_key = Fernet.generate_key()
            self.key_file.write_bytes(new_key)
            return new_key

    def encrypt(self, data: str) -> str: return self.cipher.encrypt(data.encode()).decode()
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        if isinstance(encrypted_data, str): encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()

crypto = AdvancedCrypto(master_password=os.getenv("OMNI_MASTER_PASSWORD"))

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(" ", "_")[:50]

class PIISanitizer:
    @staticmethod
    def redact_pii(text: str) -> str:
        text = re.sub(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b', '[REDACTED_CPR]', text)
        text = re.sub(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}\b', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED_CC]', text)
        return text

# ==========================================
# 🔹 7. ADVANCED THREAT INTEL EXTRACTION
# ==========================================
class ThreatIntelExtractor:
    PATTERNS = {
        "email": re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}\b'),
        "ipv4": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        "ipv6": re.compile(r'\b(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}\b'),
        "mac": re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'),
        "md5": re.compile(r'\b[A-Fa-f0-9]{32}\b', re.IGNORECASE),
        "sha256": re.compile(r'\b[A-Fa-f0-9]{64}\b', re.IGNORECASE),
        "crypto_btc": re.compile(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b'),
        "crypto_eth": re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
        "crypto_xmr": re.compile(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'),
        "onion_v3": re.compile(r'\b[a-z2-7]{56}\.onion\b'),               
        "aws_key": re.compile(r'\bAKIA[0-9A-Z]{16}\b'),                   
        "discord_token": re.compile(r'\b[\w-]{24}\.[\w-]{6}\.[\w-]{27}\b'),
        "slack_webhook": re.compile(r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+'),
        "s3_bucket": re.compile(r'(?:http[s]?://)?(?:[a-zA-Z0-9_-]+)\.s3(?:-[a-z0-9-]+)?\.amazonaws\.com'),
        "danish_cpr": re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b'),
        "danish_cvr": re.compile(r'\b[1-9]\d{7}\b'),
        "iban": re.compile(r'\b[A-Z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?!(?:[ ]?[0-9]){3})(?:[ ]?[0-9]{1,2})?\b'),
        "credit_card": re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b')
    }

    @classmethod
    def extract_all(cls, text: str) -> Dict[str, List[str]]:
        results = {}
        for key, pattern in cls.PATTERNS.items():
            matches = list(set(pattern.findall(text)))
            if matches: results[key] = matches
        return results

    @staticmethod
    def extract_danish_phones(text: str) -> Set[str]:
        pattern = r'(?:(?:\+45|0045)\s?)?(?:[2-9][0-9]\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2})'
        raw_matches = re.findall(pattern, text)
        clean_phones = set()
        for m in raw_matches:
            num = re.sub(r'\D', '', m)
            if len(num) == 8: clean_phones.add(num)
            elif len(num) == 10 and num.startswith('45'): clean_phones.add(num[2:])
        return clean_phones

class JWTExtractor:
    JWT_PATTERN = re.compile(r'\b(ey[a-zA-Z0-9_-]+\.ey[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)\b')

    @classmethod
    def decode_payload(cls, token: str) -> Optional[Dict]:
        try:
            parts = token.split('.')
            if len(parts) != 3: return None
            payload_b64 = parts[1]
            padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            return json.loads(decoded_bytes.decode('utf-8'))
        except Exception:
            return None

    @classmethod
    def extract_and_decode(cls, text: str) -> List[Dict[str, Any]]:
        tokens = list(set(cls.JWT_PATTERN.findall(text)))
        results = []
        for token in tokens:
            payload = cls.decode_payload(token)
            if payload:
                results.append({"token": token[:30] + "...", "payload": payload})
        return results

def extract_iocs(text: str) -> Dict[str, List[str]]:
    return ThreatIntelExtractor.extract_all(text)

# ==========================================
# 🔹 8. DATA LAKE EXPORTER & ANALYTICS
# ==========================================
class OmniDataLake:
    def __init__(self, base_dir: str = "loot_evidence"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "omni_datalake.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS osint_records
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             timestamp DATETIME,
                             source_module TEXT,
                             target TEXT,
                             data_json TEXT)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_target ON osint_records(target)')

    def ingest(self, source_module: str, target: str, data: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO osint_records (timestamp, source_module, target, data_json) VALUES (?, ?, ?, ?)",
                         (datetime.now().isoformat(), source_module, target, json.dumps(data, ensure_ascii=False)))

    def save_to_json(self, data: Dict[str, Any], filename: str, encrypt: bool = False, sanitize_pii: bool = False) -> str:
        filepath = self.base_dir / f"{sanitize_filename(filename)}.json"
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        
        if sanitize_pii: json_data = PIISanitizer.redact_pii(json_data)
        if encrypt:
            filepath = filepath.with_suffix(".json.enc")
            filepath.write_text(crypto.encrypt(json_data))
        else:
            filepath.write_text(json_data, encoding='utf-8')
            
        return str(filepath)

datalake = OmniDataLake()
def save_to_json(data: Dict[str, Any], filename: str, encrypt: bool = False) -> None:
    datalake.save_to_json(data, filename, encrypt)

# ==========================================
# 🔹 9. BACKWARDS COMPATIBILITY LAYER
# ==========================================
# Sikrer at ældre moduler (Modul 01, 02, 04, 09) ikke crasher på manglende imports
REGEX_EMAIL = ThreatIntelExtractor.PATTERNS["email"]
REGEX_CPR = ThreatIntelExtractor.PATTERNS["danish_cpr"]
REGEX_CVR = ThreatIntelExtractor.PATTERNS["danish_cvr"]
REGEX_BTC = ThreatIntelExtractor.PATTERNS["crypto_btc"]
REGEX_ETH = ThreatIntelExtractor.PATTERNS["crypto_eth"]
REGEX_XMR = ThreatIntelExtractor.PATTERNS["crypto_xmr"]
REGEX_IBAN = ThreatIntelExtractor.PATTERNS["iban"]
REGEX_IPV4 = ThreatIntelExtractor.PATTERNS["ipv4"]
REGEX_MAC = ThreatIntelExtractor.PATTERNS["mac"]

def extract_danish_phones(text):
    return ThreatIntelExtractor.extract_danish_phones(text)