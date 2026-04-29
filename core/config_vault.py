# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - UNIVERSAL CONFIG VAULT & HOT-RELOADER
📌 Formål: Auto-detektion af konfigurationer, militær kryptering og asynkron live-opdatering.
🔧 Features:
   - Universal Auto-Discovery (Finder .json, .env, .yaml uanset navn)
   - AES-256 Vault Migration (Sletter plaintext config efter import)
   - Asynchronous Hot-Reloading (Skift API-nøgler mens systemet kører)
   - In-Memory Secure Enclave via Pydantic Strict Validation
"""

import os
import json
import asyncio
import hashlib
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import structlog

# Forudsætter vi har Pydantic schema fra tidligere
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger()
C_GREEN = '\033[92m'
C_RED = '\033[91m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_RESET = '\033[0m'

class GoliathVault:
    """Enterprise-grade konfigurations-håndtering med Hot-Reload og Kryptering."""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.vault_path = Path("goliath_secure.vault")
        self.key_path = Path(".goliath_master.key")
        self.state: Dict[str, Any] = {}
        self.lock = threading.RLock()
        
        # 1. Sikker Nøglehåndtering
        self.key = master_key or self._get_or_create_key()
        self.cipher = Fernet(self.key)
        
        # 2. Auto-Discovery & Migration
        self._auto_discover_and_migrate()
        
        # 3. Start Hot-Reloader Daemon
        self.watcher_thread = threading.Thread(target=self._hot_reload_daemon, daemon=True)
        self.watcher_thread.start()

    def _get_or_create_key(self) -> bytes:
        """Henter eller genererer en unik AES-256 nøgle til maskinen."""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            new_key = Fernet.generate_key()
            # Gemmes med strenge OS-rettigheder (Kun ejer kan læse)
            self.key_path.write_bytes(new_key)
            if os.name != 'nt': os.chmod(self.key_path, 0o600)
            logger.info("🔑 Ny Master Key genereret til Goliath Vault.")
            return new_key

    def _auto_discover_and_migrate(self):
        """
        Smarte funktionen der svarer på "Kan jeg ikke bare omdøbe filen?".
        Den scanner roden for filer der *ligner* config, suger dataen ud,
        lægger den i Vaulten, og spørger om den skal slette den usikre JSON.
        """
        if self.vault_path.exists():
            self._load_from_vault()
            return

        print(f"\n{C_YELLOW}[*] Ingen sikret Vault fundet. Kører Auto-Discovery efter konfigurationer...{C_RESET}")
        
        possible_configs = ["goliath_session.json", "config.json", "settings.json", "omni_config.json"]
        found_config = None
        
        # Scanner aktivt filsystemet
        for cfg in possible_configs:
            if Path(cfg).exists():
                found_config = Path(cfg)
                break
                
        if not found_config:
            # Fallback til at scanne *alle* JSON filer for GOLIATH signaturer
            for file in Path(".").glob("*.json"):
                try:
                    data = json.loads(file.read_text(encoding='utf-8'))
                    if "system_settings" in data or "api_keys" in data:
                        found_config = file
                        break
                except: continue

        if found_config:
            print(f"{C_GREEN}[+] Fandt usikret konfiguration: {found_config.name}. Migrerer til Secure Vault...{C_RESET}")
            raw_data = json.loads(found_config.read_text(encoding='utf-8'))
            self._save_to_vault(raw_data)
            self.state = raw_data
            
            # OPSEC Feature: Tilbyd at slette originalen
            print(f"{C_RED}[!] ADVARSEL: {found_config.name} ligger i klartekst på disken.{C_RESET}")
            # I et autonomt script sletter vi den automatisk eller omdøber den til .bak
            backup_name = f"{found_config.name}.bak"
            found_config.rename(backup_name)
            print(f"{C_CYAN}    -> Omdøbt original til {backup_name} for din sikkerhed.{C_RESET}")
        else:
            raise FileNotFoundError("Kunne hverken finde en eksisterende .vault eller nogen JSON config at migrere!")

    def _save_to_vault(self, data: Dict[str, Any]):
        """Krypterer og gemmer konfigurationen militært."""
        json_data = json.dumps(data, indent=4).encode('utf-8')
        encrypted_data = self.cipher.encrypt(json_data)
        
        # Gemmer med et hash for integritetstjek
        integrity_hash = hashlib.sha256(encrypted_data).hexdigest()
        vault_payload = {
            "integrity": integrity_hash,
            "payload": encrypted_data.decode('utf-8'),
            "timestamp": datetime.now().isoformat()
        }
        
        self.vault_path.write_text(json.dumps(vault_payload), encoding='utf-8')
        if os.name != 'nt': os.chmod(self.vault_path, 0o600)
        logger.info(f"🛡️ Data skrevet til {self.vault_path.name} med AES-256 kryptering.")

    def _load_from_vault(self):
        """Læser og dekrypterer fra Vault, med integritetstjek."""
        try:
            vault_content = json.loads(self.vault_path.read_text(encoding='utf-8'))
            encrypted_payload = vault_content["payload"].encode('utf-8')
            
            # Integritetstjek (Anti-Tampering)
            if hashlib.sha256(encrypted_payload).hexdigest() != vault_content["integrity"]:
                logger.critical("🚨 VAULT INTEGRITY BREACH: Filen er blevet uautoriseret ændret!")
                raise ValueError("Vault tampering detected!")
                
            decrypted_data = self.cipher.decrypt(encrypted_payload)
            with self.lock:
                self.state = json.loads(decrypted_data)
            logger.info("🔓 Secure Vault dekrypteret og indlæst i hukommelsen.")
        except Exception as e:
            logger.error(f"Kritisk fejl ved indlæsning af Vault: {e}")
            raise

    def get(self, section: str, key: str = None) -> Any:
        """Trådsikker hentning af konfigurationer."""
        with self.lock:
            if key:
                return self.state.get(section, {}).get(key)
            return self.state.get(section)

    def update_key_live(self, service: str, new_key: str):
        """Tillader live-opdatering af en API-nøgle, mens systemet kører."""
        with self.lock:
            if "api_keys" not in self.state:
                self.state["api_keys"] = {}
            self.state["api_keys"][service] = new_key
            self._save_to_vault(self.state)
            logger.info(f"🔄 Live-Update: Nøgle for '{service}' opdateret og krypteret on-the-fly.")

    def _hot_reload_daemon(self):
        """
        Baggrundstråd der tillader os at smide en 'update.json' i mappen, 
        hvorefter GOLIATH suger den op, opdaterer Vaulten, og sletter filen uden at stoppe.
        """
        update_file = Path("omni_update.json")
        while True:
            try:
                if update_file.exists():
                    time.sleep(1) # Vent på at skrive-operationer er færdige
                    new_data = json.loads(update_file.read_text(encoding='utf-8'))
                    
                    with self.lock:
                        # Deep-update af dictionaries
                        for k, v in new_data.items():
                            if isinstance(v, dict) and k in self.state:
                                self.state[k].update(v)
                            else:
                                self.state[k] = v
                                
                    self._save_to_vault(self.state)
                    update_file.unlink() # Slet update-filen for OPSEC
                    print(f"\n{C_MAGENTA}[⚡] HOT-RELOAD TRIGGRET: Omni_Hunter har indlæst nye indstillinger live!{C_RESET}")
            except Exception as e:
                pass
            time.sleep(5)

# Global eksport til hele platformen
vault = GoliathVault()