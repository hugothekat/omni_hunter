# -*- coding: utf-8 -*-
"""
🚀 GOLIATH V36: AUTONOMOUS MASS RE-INDEXER
📌 Formål: Omdøber intelligent alle mod_XX.py filer i sekventiel rækkefølge, 
og opdaterer alle interne import-referencer i `core/` og tværgående moduler.
"""
import os
import glob
import re
from pathlib import Path

def run_reindexer():
    print("\033[96m[=] INITIATING GOLIATH MASS RE-INDEXER PROTOCOL [=]\033[0m")
    
    mod_dir = Path("modules")
    if not mod_dir.exists():
        print("Fejl: Mappen 'modules' findes ikke.")
        return
        
    # 1. Hent alle mod_*.py filer og sortér dem alfabetisk/numerisk
    mod_files = sorted([f for f in mod_dir.glob("mod_*.py")], key=lambda x: x.name)
    
    rename_map = {}
    counter = 1
    
    # 2. Generer mapping for nye navne
    for file in mod_files:
        old_name = file.stem # f.eks. mod_02_business
        parts = old_name.split('_')
        
        if len(parts) >= 3 and parts[0] == "mod" and parts[1].isdigit():
            new_index = f"{counter:02d}"
            new_name = f"mod_{new_index}_{'_'.join(parts[2:])}"
            if old_name != new_name:
                rename_map[old_name] = new_name
            counter += 1
            
    if not rename_map:
        print("\033[92m[✓] Alle moduler er allerede perfekt indekseret.\033[0m")
        return
        
    print(f"\033[93m[*] Omstrukturerer {len(rename_map)} moduler...\033[0m")
    
    # 3. Omdøb filerne fysisk på disken
    for old_base, new_base in rename_map.items():
        old_path = mod_dir / f"{old_base}.py"
        new_path = mod_dir / f"{new_base}.py"
        os.rename(old_path, new_path)
        print(f"\033[95m    -> Omdøbt: {old_base}.py til {new_base}.py\033[0m")
        
    # 4. Opdater alle Python filer i projektet med de nye import navne
    print(f"\n\033[93m[*] Opdaterer interne krydsreferencer (Cross-Module Injections)...\033[0m")
    all_python_files = glob.glob("**/*.py", recursive=True)
    
    for py_file in all_python_files:
        # Rør ikke reindexeren selv
        if os.path.basename(py_file) == "goliath_reindexer.py": continue
        
        path = Path(py_file)
        try:
            content = path.read_text(encoding='utf-8')
            modified = False
            
            for old_base, new_base in rename_map.items():
                if old_base in content:
                    content = content.replace(old_base, new_base)
                    modified = True
                    
            if modified:
                path.write_text(content, encoding='utf-8')
                print(f"\033[92m    ✓ Patchet referencer i: {py_file}\033[0m")
        except Exception as e:
            print(f"\033[91m    [!] Fejl ved læsning af {py_file}: {e}\033[0m")
            
    print("\n\033[92m[✓] RE-INDEXING COMPLETE! Hele biblioteket og alle pivot-referencer er synkroniseret.\033[0m")

if __name__ == "__main__":
    run_reindexer()