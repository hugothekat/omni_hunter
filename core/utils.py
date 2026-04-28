# -*- coding: utf-8 -*-
import re
import os
import json
import shutil
from datetime import datetime

class C:
    """GOLIATH V8: Udvidet ANSI Terminal Styling"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BG_RED = '\033[41m' # Til kritiske fejl
    RESET = '\033[0m'

# ==========================================
# GOLIATH V8: REGEX INTELLIGENCE ENGINE
# ==========================================
REGEX_EMAIL = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}\b')
REGEX_BANK = re.compile(r'(?:reg|regnr)[^\d]{0,10}(\d{4}).{0,40}?(?:konto|kontonr)[^\d]{0,10}(\d{7,10})', re.IGNORECASE)
REGEX_CPR = re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b')
REGEX_CVR = re.compile(r'\b[1-9]\d{7}\b') # Danske CVR numre

# Udvidet Krypto-detektion (Inkluderer nu SegWit BTC og Monero)
REGEX_BTC = re.compile(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b')
REGEX_ETH = re.compile(r'\b0x[a-fA-F0-9]{40}\b')
REGEX_XMR = re.compile(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b') # Monero (Darkweb standard)

# Netværk & Finans
REGEX_IBAN = re.compile(r'\b[A-Z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?!(?:[ ]?[0-9]){3})(?:[ ]?[0-9]{1,2})?\b')
REGEX_IPV4 = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
REGEX_MAC = re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b')

session = {
    "name": "", 
    "city": "", 
    "email": "", 
    "phone": "",
    "username": "",
    "found_links": [],
    "loot_folder": "loot_evidence"
}

# SESSION_FILE og save_session fjernes/deaktiveres her
def save_session():
    """Funktion deaktiveret for at undgå irriterende hukommelse"""
    pass

def load_session():
    """Funktion deaktiveret - starter altid på en frisk"""
    pass

def get_input(prompt_text, session_key):
    """Henter input uden at foreslå gamle værdier som '99'"""
    val = input(f"{C.CYAN}{prompt_text}: {C.RESET}").strip()
    
    # Vi gemmer stadig værdien i den aktive kørsel, så modulerne virker,
    # men vi gemmer den ALDRIG til harddisken.
    session[session_key] = val
    return val

def extract_danish_phones(text):
    """GOLIATH V8: Udvidet udtræk af danske telefonnumre (Håndterer +45 og 0045)"""
    # Fanger nu også numre der starter med landekode og har vilkårlige mellemrum
    pattern = r'\b(?:\+45|0045)?\s*([2-9]\d{1})\s*(\d{2})\s*(\d{2})\s*(\d{2})\b'
    matches = re.findall(pattern, text)
    phones = set()
    for match in matches:
        # Samler the capture groups til et rent 8-cifret nummer
        phone = ''.join(match)
        if phone.isdigit() and len(phone) == 8:
            phones.add(phone)
    return phones

def sanitize_filename(name):
    """NY V8: Sikrer at filnavne ikke crasher pga. ulovlige OS-tegn"""
    if not name:
        return f"unknown_{datetime.now().strftime('%H%M%S')}"
    # Fjerner alt der ikke er bogstaver, tal, bindestreg eller understregning
    clean = re.sub(r'[^\w\-_\. ]', '_', str(name))
    return clean[:50].strip() # Max 50 tegn for at undgå path length limits