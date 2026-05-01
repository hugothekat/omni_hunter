# -*- coding: utf-8 -*-
"""
🚀 GOLIATH PRODUCTION WORKER (CELERY & REDIS DAEMON)
📌 Formål: Starter Redis (Message Broker) og Celery asynkront for Web Command Center.
"""
import os
import subprocess
import time
import sys
from pathlib import Path

# =====================================================================
# GOLIATH V46: VENV AUTO-HIJACK (BYPASSES PEP-668 EXTERNALLY MANAGED)
# =====================================================================
def ensure_venv():
    """Tvinger scriptet til at køre i venv for at undgå system pip-begrænsninger."""
    if sys.prefix == sys.base_prefix:
        venv_python = Path("venv/bin/python")
        if venv_python.exists():
            print("\033[93m[*] Udenfor venv detekteret. Genstarter automatisk inde i The Goliath Venv...\033[0m")
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            print("\033[91m[!] Intet 'venv' fundet. Kør './goliath.sh' for at bygge miljøet først.\033[0m")
            sys.exit(1)

ensure_venv()

def ensure_celery():
    try:
        import celery
    except ImportError:
        print("\033[93m[*] Auto-installerer manglende 'celery' afhængigheder til dit nuværende miljø...\033[0m")
        subprocess.run([sys.executable, "-m", "pip", "install", "celery", "redis"], stdout=subprocess.DEVNULL)
ensure_celery()

def check_redis():
    """Tjekker om Redis kører på port 6379, ellers startes den."""
    print("\033[96m[*] Tjekker Redis Message Broker (Port 6379)...\033[0m")
    try:
        res = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
        if "PONG" in res.stdout:
            print("\033[92m    ✓ Redis kører allerede!\033[0m")
            return True
    except FileNotFoundError:
        print("\033[91m[!] redis-cli ikke fundet. Kør: sudo apt install redis-server\033[0m")
        sys.exit(1)
    
    print("\033[93m[*] Starter Redis Server i baggrunden...\033[0m")
    try:
        subprocess.Popen(["redis-server", "--daemonize", "yes"])
        time.sleep(2)
        return True
    except FileNotFoundError:
        print("\033[91m[!] 'redis-server' binær fil ikke fundet. Afbryder. Kør: sudo apt install redis-server\033[0m")
        sys.exit(1)

def start_celery():
    """Spinder Celery worker og Celery Beat op bundet til core.web_server (Reprohack Architecture)."""
    print("\n\033[96m[*] Initierer Celery Worker & Beat Scheduler (GOLIATH APEX)...\033[0m")
    try:
        os.makedirs("logs", exist_ok=True)
        # GOLIATH AUTO-HEAL: Flusher døde tasks fra ældre batches ud af Redis
        print("\033[95m[*] Tømmer Redis-køen for forældede ghost-tasks...\033[0m")
        subprocess.run([sys.executable, "-m", "celery", "-A", "core.web_server", "purge", "-f"])
        
        # Starter Celery Beat asynkront i baggrunden for cronjobs
        subprocess.Popen([sys.executable, "-m", "celery", "-A", "core.web_server", "beat", "--loglevel=info", "--logfile=logs/celery_beat.log"])
        
        # Starter hovedworkeren i forgrunden
        subprocess.run([sys.executable, "-m", "celery", "-A", "core.web_server", "worker", "--loglevel=info", "--pool=solo", "--logfile=logs/celery_worker.log"])
    except KeyboardInterrupt:
        print("\n\033[91m[*] Celery Worker afbrudt manuelt.\033[0m")
    except Exception as e:
        print(f"\n\033[91m[!] Fejl ved opstart af Celery: {e}. Er 'celery' installeret (pip install celery)?\033[0m")

if __name__ == "__main__":
    print(f"\033[91m\033[1m{'='*60}\n[BATCH 5] GOLIATH PRODUCTION WORKER DAEMON\n{'='*60}\033[0m")
    if check_redis(): start_celery()