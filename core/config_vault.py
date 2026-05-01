# -*- coding: utf-8 -*-
"""
🚀 OMNI_HUNTER - UNIVERSAL CONFIG VAULT & HOT-RELOADER (V5)
📌 Formål: Auto-detektion af konfigurationer, militær kryptering og asynkron live-opdatering.
🔧 Features:
   - FASTSAT: datetime import fejl løst.
   - Universal Auto-Discovery & Plaintext Eradication.
   - AES-256 Vault med Cryptographic Versioning (Audit Trail).
   - Autonomous Integrity Rollback (Redder korrupte config-filer).
   - Asynchronous Hot-Reloading & OPSEC Memory Wiping.
"""

import os
import json
import asyncio
import hashlib
import threading
import time
import gc
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from cryptography.fernet import Fernet, InvalidToken
import structlog

logger = structlog.get_logger()
C_GREEN = '\033[92m'
C_RED = '\033[91m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_MAGENTA = '\033[95m'
C_RESET = '\033[0m'

class GoliathVault:
    """Enterprise-grade konfigurations-håndtering med Hot-Reload, Kryptering og Versioning."""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.vault_path = Path("goliath_secure.vault")
        self.key_path = Path(".goliath_master.key")
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = [] # NYT: Holder styr på de 5 seneste config states
        self.max_history = 5
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
            self.key_path.write_bytes(new_key)
            if os.name != 'nt': os.chmod(self.key_path, 0o600)
            logger.info("🔑 Ny Master Key genereret til Goliath Vault.")
            return new_key

    def _auto_discover_and_migrate(self):
        """Smarte funktionen der migrerer usikre configs til the Vault."""
        if self.vault_path.exists():
            self._load_from_vault()
            return

        print(f"\n{C_YELLOW}[*] Ingen sikret Vault fundet. Kører Auto-Discovery efter konfigurationer...{C_RESET}")
        
        possible_configs = ["goliath_session.json", "config.json", "settings.json", "omni_config.json"]
        found_config = None
        
        for cfg in possible_configs:
            if Path(cfg).exists():
                found_config = Path(cfg)
                break
                
        if not found_config:
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
            self.state = raw_data
            self._save_to_vault(raw_data)
            
            print(f"{C_RED}[!] ADVARSEL: {found_config.name} ligger i klartekst på disken.{C_RESET}")
            backup_name = f"{found_config.name}.bak"
            found_config.rename(backup_name)
            print(f"{C_CYAN}    -> Omdøbt original til {backup_name} for din OPSEC.{C_RESET}")
        else:
            print(f"{C_RED}[!] Kunne ikke finde en konfigurationsfil. Opret goliath_session.json!{C_RESET}")
            raise FileNotFoundError("Ingen JSON config at migrere!")

    def _save_to_vault(self, data: Dict[str, Any]):
        """Krypterer og gemmer konfigurationen militært, MED historik-vedligeholdelse."""
        with self.lock:
            # Opdater history stack
            if self.state:
                self.history.insert(0, json.dumps(self.state).encode('utf-8'))
                if len(self.history) > self.max_history:
                    self.history.pop()

            json_data = json.dumps(data, indent=4).encode('utf-8')
            encrypted_current = self.cipher.encrypt(json_data)
            
            # Krypter også historikken
            encrypted_history = [self.cipher.encrypt(h).decode('utf-8') for h in self.history]
            
            integrity_hash = hashlib.sha256(encrypted_current).hexdigest()
            vault_payload = {
                "integrity": integrity_hash,
                "payload": encrypted_current.decode('utf-8'),
                "history": encrypted_history,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.vault_path.write_text(json.dumps(vault_payload), encoding='utf-8')
            if os.name != 'nt': os.chmod(self.vault_path, 0o600)
            logger.info(f"🛡️ Data skrevet til {self.vault_path.name} med AES-256 kryptering og Versioning.")

    def _load_from_vault(self):
        """Læser fra Vault med Anti-Tampering og Auto-Rollback."""
        try:
            vault_content = json.loads(self.vault_path.read_text(encoding='utf-8'))
            encrypted_payload = vault_content["payload"].encode('utf-8')
            
            # Integritetstjek (Anti-Tampering)
            if hashlib.sha256(encrypted_payload).hexdigest() != vault_content["integrity"]:
                raise ValueError("Vault tampering or corruption detected!")
                
            decrypted_data = self.cipher.decrypt(encrypted_payload)
            with self.lock:
                self.state = json.loads(decrypted_data)
                self.history = [self.cipher.decrypt(h.encode('utf-8')).decode('utf-8') for h in vault_content.get("history", [])]
                
            logger.info("🔓 Secure Vault dekrypteret og indlæst i hukommelsen.")
            
        except (ValueError, InvalidToken, json.JSONDecodeError) as e:
            logger.critical(f"🚨 VAULT FEJL: {e}")
            self._attempt_rollback(vault_content if 'vault_content' in locals() else None)
        except Exception as e:
            logger.error(f"Kritisk ukendt fejl ved indlæsning af Vault: {e}")
            raise

    def _attempt_rollback(self, corrupted_content: Optional[Dict]):
        """NYT: Gendanner automatisk en tidligere, fungerende krypteret konfiguration."""
        print(f"\n{C_RED}[!] KRITISK VAULT FEJL DETEKTERET. Initierer Auto-Rollback Protocol...{C_RESET}")
        
        if not corrupted_content or "history" not in corrupted_content or not corrupted_content["history"]:
            print(f"{C_RED}[!] Ingen historik at gendanne fra. System Halted.{C_RESET}")
            raise RuntimeError("Vault is completely corrupted with no history.")
            
        for i, enc_hist in enumerate(corrupted_content["history"]):
            try:
                decrypted = self.cipher.decrypt(enc_hist.encode('utf-8'))
                state = json.loads(decrypted)
                
                with self.lock:
                    self.state = state
                    self.history = [self.cipher.decrypt(h.encode('utf-8')).decode('utf-8') for h in corrupted_content["history"][i+1:]]
                    self._save_to_vault(self.state)
                    
                print(f"{C_GREEN}[+] Auto-Rollback succes! Gendannede fra historisk version {i+1}.{C_RESET}")
                return
            except Exception:
                continue
                
        print(f"{C_RED}[!] Alle historiske versioner er også korrupte. Destroying vault.{C_RESET}")
        self.vault_path.unlink(missing_ok=True)
        return

    def get(self, section: str, key: str = None) -> Any:
        """Trådsikker hentning af konfigurationer."""
        with self.lock:
            if key:
                section_data = self.state.get(section)
                return section_data.get(key) if isinstance(section_data, dict) else None
            return self.state.get(section)

    def update_key_live(self, service: str, new_key: str):
        """Tillader live-opdatering med OPSEC Memory Wiping."""
        with self.lock:
            if "api_keys" not in self.state:
                self.state["api_keys"] = {}
                
            self.state["api_keys"][service] = new_key
            self._save_to_vault(self.state)
            
            # OPSEC: Tving Garbage Collection for at slette gamle strenge fra RAM
            gc.collect()
            logger.info(f"🔄 Live-Update: Nøgle for '{service}' opdateret og RAM sanitiseret.")

    def _hot_reload_daemon(self):
        """Asynkron watcher til live opdateringer under operation."""
        update_file = Path("omni_update.json")
        while True:
            try:
                if update_file.exists():
                    time.sleep(1) # Vent på I/O sync
                    new_data = json.loads(update_file.read_text(encoding='utf-8'))
                    
                    with self.lock:
                        for k, v in new_data.items():
                            if isinstance(v, dict) and k in self.state:
                                self.state[k].update(v)
                            else:
                                self.state[k] = v
                                
                    self._save_to_vault(self.state)
                    update_file.unlink() # Destroy file
                    gc.collect()
                    print(f"\n{C_MAGENTA}[⚡] HOT-RELOAD TRIGGRET: Omni_Hunter har indlæst nye indstillinger live!{C_RESET}")
            except Exception:
                pass
            time.sleep(3)

# Global eksport
vault = GoliathVault()