# -*- coding: utf-8 -*-
import os
import zipfile
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core.utils import C, session, sanitize_filename, logger

class GoliathExporter:
    """GOLIATH V55: Pakker og AES-256 krypterer sagsbeviser for sikker overdragelse."""
    def __init__(self, target: str, password: str):
        self.target = target
        self.password = password.encode('utf-8')
        self.loot_dir = Path(session.get("loot_folder", "loot_evidence"))

    def export(self) -> str:
        safe_target = sanitize_filename(self.target)
        zip_path = self.loot_dir / f"export_tmp_{safe_target}.zip"
        enc_path = self.loot_dir / f"GOLIATH_EXPORT_{safe_target}.aes"

        print(f"{C.YELLOW}[*] Zippper alle beviser og rapporter relateret til: {self.target}...{C.RESET}")
        
        # 1. Saml og Zip filer der tilhører målet
        files_added = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.loot_dir):
                for file in files:
                    # Ignorerer tidligere eksporter og urelaterede filer
                    if safe_target.lower() in file.lower() and not file.endswith('.aes') and not file.endswith('.zip'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.loot_dir)
                        zipf.write(file_path, arcname)
                        files_added += 1

        if files_added == 0:
            if zip_path.exists(): os.remove(zip_path)
            raise FileNotFoundError(f"Ingen bevisfiler fundet for target '{self.target}'.")

        print(f"{C.YELLOW}[*] AES-256 Krypterer arkiv ({files_added} filer sikret)...{C.RESET}")
        
        # 2. Generer en PBKDF2 Key baseret på OTP password
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        cipher = Fernet(key)

        # 3. Indlæs og krypter zip-filen (Fernet håndterer filer < 500MB effektivt i RAM)
        with open(zip_path, 'rb') as f:
            plaintext = f.read()
        
        encrypted_data = cipher.encrypt(plaintext)

        # 4. Gem salt (første 16 bytes) og derefter the ciphertext
        with open(enc_path, 'wb') as f:
            f.write(salt + encrypted_data)

        os.remove(zip_path)
        return str(enc_path)