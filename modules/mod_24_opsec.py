import os
from PIL import Image
from core.utils import C

class OpsecSanitizer:
    """Fjerner al EXIF og metadata fra filer, inden de deles eller uploades"""
    def __init__(self, file_path):
        self.file_path = file_path.strip()
        
    def run(self, driver=None):
        print(f"\n{C.CYAN}{'='*60}\n[24] OPSEC Sanitizer (Fjern Metadata)\n{'='*60}{C.RESET}")
        if not os.path.exists(self.file_path):
            print(f"{C.RED}[!] Filen findes ikke.{C.RESET}"); return
            
        try:
            img = Image.open(self.file_path)
            # Kopierer kun pixels, ingen metadata
            clean_data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(clean_data)
            
            clean_path = self.file_path.rsplit('.', 1)[0] + "_CLEANED." + self.file_path.rsplit('.', 1)[1]
            clean_img.save(clean_path)
            
            print(f"{C.GREEN}    ✓ Bevis renset for metadata!{C.RESET}")
            print(f"{C.GREEN}    ✓ Sikker kopi gemt: {clean_path}{C.RESET}")
        except Exception as e:
            print(f"{C.RED}    [!] Kunne ikke rense filen (Understøtter kun billeder pt.): {e}{C.RESET}")