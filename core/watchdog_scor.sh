#!/bin/bash
# ==============================================================
# 🚀 OMNI_HUNTER V62: SCOR.DK WATCHDOG & PERSISTENCE SCRIPT
# 📌 Formål: Sikrer 100% oppetid for HVT API Monitoren.
# ==============================================================

# Definer absolutte stier (Kritisk for cron-eksekvering)
WORKSPACE_DIR="/home/hugo/omni_hunter"
PYTHON_EXEC="/usr/bin/python3" # Ret til din virtualenv sti hvis du bruger en (f.eks. venv/bin/python)

# Definer dine HVT (High Value Target) overvågningskriterier her
TARGET_KEYWORD="København" 
POLL_INTERVAL=60

cd "$WORKSPACE_DIR" || exit 1

# Opret log-mappe hvis den ikke eksisterer
mkdir -p logs

# Tjek systemets procestabel via pgrep
if pgrep -f "run_scor.py --monitor" > /dev/null
then
    # Processen kører allerede. Stealth mode opretholdt.
    # Udkommenter nedenstående for dyb debug:
    # echo "$(date): Scor.dk Monitor aktiv." >> logs/watchdog.log
    exit 0
else
    echo "$(date): [!] Alert: Scor.dk Monitor er nede! Udfører Auto-Heal genstart..." >> logs/watchdog.log
    nohup $PYTHON_EXEC run_scor.py --monitor "$TARGET_KEYWORD" --interval $POLL_INTERVAL > logs/scor_monitor_cron.log 2>&1 &
fi