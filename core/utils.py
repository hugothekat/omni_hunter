# core/utils.py
import re
import os
import shutil

class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    DIM = '\033[2m'
    RESET = '\033[0m'

REGEX_EMAIL = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}\b')
REGEX_BANK = re.compile(r'(?:reg|regnr)[^\d]{0,10}(\d{4}).{0,40}?(?:konto|kontonr)[^\d]{0,10}(\d{7,10})', re.IGNORECASE)
REGEX_CPR = re.compile(r'\b(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])\d{2}[- ]?\d{4}\b')
REGEX_BTC = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
REGEX_ETH = re.compile(r'\b0x[a-fA-F0-9]{40}\b')

# Global session state (Deles på tværs af moduler)
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
    """Henter input og foreslår den tidligere værdi fra sessionen"""
    default = session.get(session_key, "")
    if default:
        val = input(f"{C.CYAN}{prompt_text} [{default}]: {C.RESET}").strip()
        if not val:  # Hvis brugeren bare trykker ENTER
            return default
    else:
        val = input(f"{C.CYAN}{prompt_text}: {C.RESET}").strip()
    
    session[session_key] = val
    return val

def extract_danish_phones(text):
    """Extract Danish phone numbers from text"""
    pattern = r'(?:^|\s)(\d{2})\s*(\d{2})\s*(\d{2})\s*(\d{2})(?:\s|$|[^\d])'
    matches = re.findall(pattern, text, re.MULTILINE)
    phones = set()
    for match in matches:
        phone = ''.join(match)
        if phone.isdigit() and len(phone) == 8:
            phones.add(phone)
    return phones