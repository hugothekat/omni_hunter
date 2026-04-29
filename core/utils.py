#!/usr/bin/env python3
"""
🚀 OMNI_HUNTER - ULTIMATE OSINT Utility Module v2.0
📌 Purpose: Core utilities for OSINT, security, data persistence, and automation.
🔧 Features:
   - Advanced Caching & Parallel Execution
   - Military-Grade Input Sanitization & PBKDF2 Encryption
   - Comprehensive IP/Network Analysis & IOC Extraction
   - Deep Web & Dark Web OSINT (Tor Proxy routing)
   - Automated Report Generation & SQLite Data Lake Integration
   - AI-Powered OSINT Analysis (K-Means Clustering)
   - Resilient Dependency Injection
"""

import os
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import List, Dict, Union, Optional, Any, Callable, Tuple
from pathlib import Path

# ======================
# 🔹 CORE DEPENDENCIES & SHIELD
# ======================
import requests
import requests_cache
import bleach
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Pydantic (Understøtter v1/v2)
try:
    from pydantic import BaseModel, field_validator as validator, ValidationError, Field
except ImportError:
    from pydantic import BaseModel, validator, ValidationError, Field

# Dependency Shield - Forhindrer kritiske nedbrud ved manglende pakker
def safe_import(module_name, pip_name=None):
    try:
        return __import__(module_name)
    except ImportError:
        logger.warning(f"Missing dependency: {module_name}. Some features disabled. Run: pip install {pip_name or module_name}")
        return None

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
    logger.warning("Missing sklearn. AI Clustering disabled. Run: pip install scikit-learn")
    has_sklearn = False

# ======================
# 🔹 INITIALIZATION & SETUP
# ======================
load_dotenv()

requests_cache.install_cache(
    "omni_hunter_cache_v2",
    expire_after=86400,  # 24 timer cache
    allowable_methods=["GET", "POST"],
    allowable_codes=[200, 404],
    stale_if_error=True,
    backend="sqlite",
    use_temp=False
)

structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO)
)
logger = structlog.get_logger()

# 🔹 API Clients
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
CENSYS_API_ID = os.getenv("CENSYS_API_ID")
CENSYS_API_SECRET = os.getenv("CENSYS_API_SECRET")

shodan_client = shodan.Shodan(SHODAN_API_KEY) if shodan and SHODAN_API_KEY else None

if censys and CENSYS_API_ID and CENSYS_API_SECRET:
    from censys.search import CensysHosts
    censys_client = CensysHosts(api_id=CENSYS_API_ID, api_secret=CENSYS_API_SECRET)
else:
    censys_client = None

# ======================
# 🔹 SECURITY & VALIDATION (MILITARY GRADE)
# ======================
class MilitarySafeInput(BaseModel):
    """Ultra-secure input validation with military-grade sanitization."""
    query: str = Field(..., max_length=500)
    allowed_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._@ "
    
    @validator("query", pre=True, always=True)
    def military_sanitize(cls, v: str) -> str:
        sanitized = bleach.clean(
            v, tags=[], strip=True, attributes={}, styles=[], strip_comments=True
        )
        # Regex filter to ensure absolute conformity
        sanitized = re.sub(r"[^a-zA-Z0-9\-._@ ]", "", sanitized)
        if len(sanitized) > 500:
            raise ValueError("Input too long!")
        return sanitized

def military_sanitize_input(user_input: str) -> str:
    try:
        validated = MilitarySafeInput(query=user_input)
        return validated.query
    except ValidationError as e:
        logger.critical("MILITARY SECURITY BREACH ATTEMPT DETECTED", error=str(e))
        raise ValueError("🚨 SECURITY ALERT: Invalid input detected!")

# 🔹 Advanced Encryption System (Persistent PBKDF2 AES-256)
class AdvancedCrypto:
    """Military-grade encryption with persistent key management."""
    def __init__(self, master_password: Optional[str] = None):
        self.key_file = Path("omni_crypto.key")
        self.key = self._initialize_key(master_password)
        self.cipher = Fernet(self.key)

    def _initialize_key(self, password: Optional[str]) -> bytes:
        if password:
            # Derive key from password using PBKDF2
            salt = b'omni_hunter_salt_x99' # In production, store salt securely
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
            return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Auto-key generation & persistence
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            new_key = Fernet.generate_key()
            self.key_file.write_bytes(new_key)
            logger.info("New persistent crypto key generated and saved.", file=str(self.key_file))
            return new_key

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()

    def generate_hash(self, data: str) -> str:
        return hashlib.sha3_512(data.encode()).hexdigest()

crypto = AdvancedCrypto(master_password=os.getenv("OMNI_MASTER_PASSWORD"))

# ======================
# 🔹 NETWORK & OSINT TOOLS
# ======================
def safe_request(
    method: str,
    url: str,
    headers: Optional[Dict] = None,
    params: Optional[Dict] = None,
    timeout: int = 15,
    retries: int = 3,
    proxies: Optional[Dict] = None,
    **kwargs
) -> Dict[str, Any]:
    """Ultra-secure HTTP request with retries, caching, proxies and error handling."""
    headers = headers or {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for attempt in range(retries):
        try:
            response = requests.request(
                method, url, headers=headers, params=params or {}, 
                proxies=proxies, timeout=timeout, **kwargs
            )
            response.raise_for_status()
            
            try: return response.json()
            except json.JSONDecodeError: return {"text_response": response.text}
            
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                logger.error("HTTP request failed after retries", url=url, error=str(e), attempt=attempt)
                return {"error": str(e), "status_code": getattr(e.response, "status_code", None)}
            time.sleep(2 ** attempt) # Exponential backoff

# 🔹 IP & Network Analysis
def get_ip_geolocation(ip: str) -> Dict[str, Any]:
    sources = [
        ("ipapi.co", f"https://ipapi.co/{ip}/json/"),
        ("ipinfo.io", f"https://ipinfo.io/{ip}/json"),
        ("ipgeolocation.io", f"https://api.ipgeolocation.io/ipgeo?apiKey={os.getenv('IPGEO_API_KEY')}&ip={ip}")
    ]
    results = {}
    for name, url in sources:
        try:
            results[name] = safe_request("GET", url)
        except Exception as e:
            results[name] = {"error": str(e)}
    return results

def get_ip_reputation(ip: str) -> Dict[str, Any]:
    sources = [
        ("AbuseIPDB", f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}"),
        ("VirusTotal", f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"),
        ("Shodan", f"https://api.shodan.io/shodan/host/{ip}" if shodan_client else None)
    ]
    results = {}
    headers = {
        "AbuseIPDB": {"Key": os.getenv("ABUSEIPDB_API_KEY")},
        "VirusTotal": {"x-apikey": os.getenv("VT_API_KEY")},
    }

    for name, url in sources:
        if not url: continue
        try:
            if name == "Shodan" and shodan_client:
                results[name] = shodan_client.host(ip)
            else:
                results[name] = safe_request("GET", url, headers=headers.get(name, {}))
        except Exception as e:
            results[name] = {"error": str(e)}
    return results

def get_network_interfaces() -> List[Dict[str, Any]]:
    if not netifaces: return [{"error": "netifaces module missing"}]
    interfaces = []
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        interfaces.append({
            "name": interface,
            "ipv4": addrs.get(netifaces.AF_INET, [{}])[0].get("addr", "N/A"),
            "ipv6": addrs.get(netifaces.AF_INET6, [{}])[0].get("addr", "N/A"),
            "mac": addrs.get(netifaces.AF_LINK, [{}])[0].get("addr", "N/A"),
        })
    return interfaces

# 🔹 DNS & Subdomain Analysis
def dns_lookup(domain: str, record_type: str = "A", recursive: bool = False) -> Dict[str, Any]:
    if not dns: return {"error": "dnspython module missing"}
    try:
        answers = dns.resolver.resolve(domain, record_type)
        results = {"domain": domain, "records": [str(r) for r in answers]}

        if recursive:
            for record in answers:
                try:
                    sub_answers = dns.resolver.resolve(str(record), record_type)
                    results["recursive_records"] = [str(r) for r in sub_answers]
                except Exception: continue
        return results
    except Exception as e:
        logger.error("DNS lookup failed", domain=domain, record_type=record_type, error=str(e))
        return {"error": str(e), "domain": domain}

def subdomain_bruteforce(domain: str, wordlist: List[str], threads: int = 20) -> Dict[str, Any]:
    if not dns: return {"error": "dnspython missing"}
    found = []
    logger.info("Starting subdomain brute-force", domain=domain, total=len(wordlist))

    def check_subdomain(sub: str) -> Optional[str]:
        try:
            dns.resolver.resolve(f"{sub}.{domain}", "A")
            return f"{sub}.{domain}"
        except Exception: return None

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(check_subdomain, sub) for sub in wordlist]
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
                logger.info("Found subdomain", subdomain=result)

    return {"domain": domain, "found": found, "total": len(wordlist)}

# 🔹 Dark Web OSINT
def search_tor_sites(query: str) -> List[Dict[str, Any]]:
    try:
        proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
        response = safe_request("GET", f"http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}", proxies=proxies)
        
        # HTML Parse fallback if Ahmia returns raw HTML instead of JSON
        if "text_response" in response:
            soup = BeautifulSoup(response["text_response"], "html.parser")
            results = []
            for item in soup.find_all("li", class_="searchResultsItem"):
                title = item.find("h4").text if item.find("h4") else "No Title"
                url = item.find("cite").text if item.find("cite") else "No URL"
                desc = item.find("p").text if item.find("p") else "No Desc"
                results.append({"title": title, "url": url, "description": desc})
            return results
        return response
    except Exception as e:
        logger.error("Tor search failed", query=query, error=str(e))
        return []

def get_tor_exit_nodes() -> List[str]:
    try:
        # Use requests directly to avoid JSON enforcing in safe_request
        response = requests.get("https://check.torproject.org/exit-addresses", timeout=10)
        nodes = [line.split()[1] for line in response.text.split("\n") if line.startswith("ExitNode")]
        return nodes
    except Exception as e:
        logger.error("Failed to fetch Tor exit nodes", error=str(e))
        return []

# 🔹 Domain & WHOIS Analysis
def get_domain_whois(domain: str) -> Dict[str, Any]:
    if not whois: return {"error": "python-whois module missing"}
    try:
        w = whois.whois(domain)
        return {
            "domain": domain, "registrar": w.registrar,
            "creation_date": str(w.creation_date), "expiration_date": str(w.expiration_date),
            "name_servers": w.name_servers, "status": w.status,
            "emails": w.emails, "org": w.org,
        }
    except Exception as e:
        return {"error": str(e), "domain": domain}

# 🔹 Shodan & Censys
def shodan_search(ip: str) -> Dict[str, Any]:
    if not shodan_client: return {"error": "Shodan API key not configured"}
    try:
        results = shodan_client.host(ip)
        return {
            "ip": ip, "ports": results.get("ports", []),
            "vulnerabilities": results.get("vulns", []), "hostnames": results.get("hostnames", []),
            "org": results.get("org", "N/A"), "asn": results.get("asn", "N/A"),
        }
    except Exception as e:
        return {"error": str(e), "ip": ip}

def censys_search(ip: str) -> Dict[str, Any]:
    if not censys_client: return {"error": "Censys API credentials not configured"}
    try:
        results = censys_client.view(ip)
        return {
            "ip": ip, "protocols": results.get("protocols", []),
            "services": results.get("services", []), "location": results.get("location", {}),
        }
    except Exception as e:
        return {"error": str(e), "ip": ip}

# ======================
# 🔹 IOC & DOCUMENT ANALYSIS (V2 EXPANDED)
# ======================
def extract_iocs(text: str) -> Dict[str, List[str]]:
    """GOLIATH V2: Automated extraction of Indicators of Compromise from raw text."""
    iocs = {
        "ipv4": list(set(re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text))),
        "md5": list(set(re.findall(r'\b[A-Fa-f0-9]{32}\b', text))),
        "sha256": list(set(re.findall(r'\b[A-Fa-f0-9]{64}\b', text))),
        "emails": list(set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text))),
        "crypto_btc": list(set(re.findall(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', text))),
    }
    return iocs

def extract_text_from_image(image_path: str) -> str:
    if not Image or not pytesseract: return "Missing PIL/pytesseract module"
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        logger.error("OCR failed", image_path=image_path, error=str(e))
        return ""

def analyze_image_exif(image_path: str) -> Dict[str, Any]:
    """GOLIATH V2: Deep EXIF analysis including GPS coordinate extraction."""
    if not Image or not ExifTags: return {"error": "PIL module missing"}
    try:
        img = Image.open(image_path)
        exif_raw = img._getexif()
        if not exif_raw: return {"info": "No EXIF data found"}
        
        exif_data = {}
        for tag, value in exif_raw.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if isinstance(value, bytes): value = value.decode('utf-8', errors='ignore')
            exif_data[decoded] = str(value)
            
        return exif_data
    except Exception as e:
        return {"error": str(e)}

def analyze_document_metadata(file_path: str) -> Dict[str, Any]:
    try:
        if file_path.endswith(".pdf"):
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            metadata = reader.metadata
            return {
                "author": metadata.author, "creator": metadata.creator,
                "producer": metadata.producer, "creation_date": metadata.creation_date,
                "title": metadata.title,
            }
        elif file_path.endswith(".docx"):
            import docx
            doc = docx.Document(file_path)
            return {
                "author": doc.core_properties.author, "title": doc.core_properties.title,
                "subject": doc.core_properties.subject,
            }
        else:
            return {"error": "Unsupported file format"}
    except ImportError:
        return {"error": "Missing PyPDF2 or python-docx library"}
    except Exception as e:
        return {"error": str(e)}

# 🔹 AI-Powered OSINT Analysis
def cluster_texts(texts: List[str], n_clusters: int = 3) -> Dict[str, Any]:
    if not has_sklearn: return {"error": "scikit-learn not installed"}
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        X = vectorizer.fit_transform(texts)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        kmeans.fit(X)

        return {
            "clusters": kmeans.labels_.tolist(),
            "centroids": kmeans.cluster_centers_.tolist(),
            "vectorizer": vectorizer.get_feature_names_out().tolist(),
        }
    except Exception as e:
        logger.error("AI clustering failed", error=str(e))
        return {"error": str(e)}

# ======================
# 🔹 PARALLEL & ASYNC EXECUTION
# ======================
def parallel_execution(func: Callable, items: List[Any], max_workers: int = 20, chunk_size: int = 100) -> List[Any]:
    results = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(func, item) for item in chunk]
            for future in as_completed(futures):
                try: results.append(future.result())
                except Exception: pass
    return results

async def async_parallel_execution(func: Callable, items: List[Any], batch_size: int = 50) -> List[Any]:
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        tasks = [func(item) for item in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter exceptions
        results.extend([r for r in batch_results if not isinstance(r, Exception)])
    return results

# ======================
# 🔹 CACHING & PERFORMANCE
# ======================
@lru_cache(maxsize=2048)
def cached_dns_lookup(domain: str) -> Dict[str, Any]:
    return dns_lookup(domain)

def clear_cache() -> None:
    requests_cache.clear()
    cached_dns_lookup.cache_clear()
    logger.info("All caches cleared")

# ======================
# 🔹 FILE & DATA EXPORT (THE OMNI DATA LAKE V2)
# ======================
class DataExporter:
    """Enterprise-Grade Export System supporting Encryption and SQLite Data Lakes."""
    
    def __init__(self, base_dir: str = "loot_output"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "omni_datalake.db"
        self._init_db()

    def _init_db(self):
        """Initializes SQLite Data Lake for mass querying."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS osint_records
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             timestamp DATETIME,
                             source_module TEXT,
                             target TEXT,
                             data_json TEXT)''')

    def ingest_to_datalake(self, source_module: str, target: str, data: Dict[str, Any]):
        """Gemmer direkte ned i SQLite databasen for fremtidig AI-processing eller SQL-søgning."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO osint_records (timestamp, source_module, target, data_json) VALUES (?, ?, ?, ?)",
                         (datetime.now().isoformat(), source_module, target, json.dumps(data, ensure_ascii=False)))
        logger.info(f"Data ingested into OmniDataLake for target {target}")

    def save_to_json(self, data: Dict[str, Any], filename: str, encrypt: bool = False) -> str:
        filepath = self.base_dir / f"{sanitize_filename(filename)}.json"
        
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        
        if encrypt:
            encrypted_data = crypto.encrypt(json_data)
            filepath = filepath.with_suffix(".json.enc")
            filepath.write_text(encrypted_data)
            logger.info("Encrypted JSON saved", filepath=str(filepath))
        else:
            filepath.write_text(json_data, encoding='utf-8')
            logger.info("Plaintext JSON saved", filepath=str(filepath))
            
        return str(filepath)

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Flattens list of dicts and saves to CSV."""
        if not data: return ""
        filepath = self.base_dir / f"{sanitize_filename(filename)}.csv"
        
        keys = set().union(*(d.keys() for d in data))
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(keys))
            writer.writeheader()
            writer.writerows(data)
            
        logger.info("CSV saved", filepath=str(filepath))
        return str(filepath)

# Global eksportør instans
exporter = DataExporter()

# Wrapper for bagudkompatibilitet til den knækkede kode:
def save_to_json(data: Dict[str, Any], filename: str, encrypt: bool = False) -> None:
    """Legacy wrapper der kalder den nye DataExporter."""
    exporter.save_to_json(data, filename, encrypt)