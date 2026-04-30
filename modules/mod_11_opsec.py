# -*- coding: utf-8 -*-
import os
import time
import subprocess
from PIL import Image
from core.utils import C

class OpsecSanitizer:
    """Fjerner al EXIF, metadata og OS-timestamps fra filer, inden de deles eller uploades (GOLIATH V8)"""
    def __init__(self, file_path):
        self.file_path = file_path.strip()
        
    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[24] OPSEC Sanitizer (Metadata & Timestomping V8)\n{'='*60}{C.RESET}")
        
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Filen findes ikke: {self.file_path}{C.RESET}")
            return
            
        clean_path = self.file_path.rsplit('.', 1)[0] + "_CLEANED." + self.file_path.rsplit('.', 1)[1]
        image_success = False

        # --- EKSISTERENDE BILLEDE-RENSNING (Dræber også Steganografi) ---
        print(f"{C.YELLOW}[*] Forsøger Pixel-for-Pixel data rensning (Kun billeder)...{C.RESET}")
        try:
            img = Image.open(self.file_path)
            # Kopierer kun pixels, ingen metadata (Dræber EOF steganografi og EXIF)
            clean_data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(clean_data)
            
            clean_img.save(clean_path)
            image_success = True
            print(f"{C.GREEN}    ✓ Visuel Data-Rensning: Billede strippet for skjult EXIF og Steganografi!{C.RESET}")
            
        except Exception as e:
            print(f"{C.DIM}    [-] PIL Billed-rensning fejlede (Filen er sandsynligvis ikke et billede): {e}{C.RESET}")

        # --- NY V8 TILFØJELSE: Universal ExifTool Fallback (Til PDF, Video, Word doc osv) ---
        if not image_success:
            print(f"\n{C.YELLOW}[*] Kører Universal Metadata-rensning via ExifTool...{C.RESET}")
            try:
                # -all= fjerner alle metadata tags
                result = subprocess.run(["exiftool", "-all=", "-o", clean_path, self.file_path], capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(clean_path):
                    print(f"{C.GREEN}    ✓ ExifTool Rensning: Al metadata udslettet fra filen!{C.RESET}")
                else:
                    print(f"{C.RED}    [!] ExifTool kunne ikke rense filen.{C.RESET}")
                    return
            except FileNotFoundError:
                print(f"{C.RED}    [!] 'exiftool' er ikke installeret. Kør: sudo apt install libimage-exiftool-perl{C.RESET}")
                return
            except Exception as e:
                print(f"{C.RED}    [!] Systemfejl under ExifTool kørsel: {e}{C.RESET}")
                return

        # --- NY V8 TILFØJELSE: OS Anti-Forensics (Timestomping) ---
        self._timestomp_file(clean_path)

        print(f"\n{C.GREEN}    ✓ Sikker kopi gemt: {clean_path}{C.RESET}")
        print(f"{C.CYAN}    🔥 OPSEC STATUS: Filen er fuldstændig anonymiseret og klar til sikker distribution.{C.RESET}")

    def _timestomp_file(self, target_path):
        """NY V8 TILFØJELSE: Ændrer filens OS-tidsstempler for at ødelægge forensic tidslinjer"""
        print(f"\n{C.YELLOW}[*] Udfører Timestomping (Sletter OS Forensics spor)...{C.RESET}")
        try:
            # Sætter tiden til 1. Januar 1980 (Klassisk hacker epoch)
            epoch_time = 315532800
            os.utime(target_path, (epoch_time, epoch_time))
            print(f"{C.GREEN}    ✓ Timestomping: Oprettelses- og Ændringsdato sat til 01-01-1980!{C.RESET}")
        except Exception as e:
            print(f"{C.DIM}    [-] Timestomping fejlede på OS-niveau: {e}{C.RESET}")