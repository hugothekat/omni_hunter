# -*- coding: utf-8 -*-
import os
import sys
import time
import importlib.util
import inspect
import traceback
from functools import wraps
from pathlib import Path
from unittest.mock import MagicMock
from core.utils import C, logger

if 'frontend' not in sys.modules:
    sys.modules['frontend'] = MagicMock()

class ModuleManager:
    """GOLIATH V36: Dynamisk modul-loader med Advanced Error Traceback."""
    def __init__(self, modules_dir="modules"):
        self.modules_dir = Path(modules_dir)
        self.modules = {}
        self.quarantine = {}

    def reload_modules(self):
        self.modules.clear()
        self.quarantine.clear()
        self.discover()

    def discover(self):
        if not self.modules_dir.exists(): return
        
        for file in sorted(self.modules_dir.glob("mod_*.py")):
            mod_id = file.stem.split('_')[1]
            mod_name = file.stem
            
            if mod_name in sys.modules: del sys.modules[mod_name]
            
            try:
                spec = importlib.util.spec_from_file_location(mod_name, file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
                
                module_found = False
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and attr.__module__ == mod_name:
                        if hasattr(attr, 'generate') and not hasattr(attr, 'run'):
                            attr.run = attr.generate 
                            
                        if hasattr(attr, 'run'):
                            self.modules[mod_id] = {
                                "class": attr,
                                "name": getattr(attr, 'name', attr_name),
                                "file_path": str(file)
                            }
                            module_found = True
                            break
                
                if not module_found:
                    self.quarantine[mod_id] = {"file": file.name, "error": "Mangler run() funktion."}
                    
            except SyntaxError as e:
                # [FEJL RETTET: Viser nu den PRÆCISE fil, der har Syntax Error]
                error_file = os.path.basename(e.filename) if getattr(e, 'filename', None) else file.name
                self.quarantine[mod_id] = {"file": file.name, "error": f"Syntax Fejl i {error_file} (Linje {e.lineno})"}
            except ImportError as e:
                self.quarantine[mod_id] = {"file": file.name, "error": f"Mangler afhængighed: {e.name}"}
            except Exception as e:
                self.quarantine[mod_id] = {"file": file.name, "error": str(e).split('\n')[0][:50]}

    def display_dynamic_menu(self):
        print(f"\n{C.RED}--- [ OPERATIONELT VÆRKTØJSARSENAL ] ---{C.RESET}")
        for mod_id, data in sorted(self.modules.items()):
            print(f" {C.WHITE}[{mod_id}]{C.RESET} {data['name']}")
            
        if self.quarantine:
            print(f"\n{C.YELLOW}--- [ VÆRKTØJER I KARANTÆNE (SYSTEMFEJL) ] ---{C.RESET}")
            for mod_id, data in sorted(self.quarantine.items()):
                print(f" {C.RED}[{mod_id}] {data['file']}{C.RESET} -> {C.DIM}{data['error']}{C.RESET}")

    def _telemetry_wrapper(self, func, mod_id, mod_name):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                logger.info(f"Module [{mod_id}] completed in {time.time() - start_time:.2f}s.")
                return result
            except Exception as e:
                logger.error(f"Module [{mod_id}] crashed.", error=str(e))
                print(f"\n{C.BG_RED}{C.WHITE} [!] NEDBRUD I MODUL {mod_id}: {e} {C.RESET}\n")
                raise
        return wrapper

    def get_module(self, mod_id: str):
        mod_info = self.modules.get(mod_id)
        if not mod_info: return None
        
        mod_class = mod_info["class"]
        try:
            sig = inspect.signature(mod_class.__init__)
            instance = mod_class("") if len(sig.parameters) > 1 else mod_class()
            
            if not hasattr(instance, 'check_requirements'): instance.check_requirements = lambda: True
            if not hasattr(instance, 'name'): instance.name = mod_info["name"]
                
            instance.run = self._telemetry_wrapper(instance.run, mod_id, instance.name)
            return instance
            
        except Exception as e:
            logger.error(f"Klargøringsfejl i modul {mod_id}: {e}")
            return None