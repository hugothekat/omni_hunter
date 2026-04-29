#!/bin/bash
# ==============================================================================
# 🚀 PET FE SECURE EXPORT TOOL
# Pakker OMNI_HUNTER sikkert ned, så du kan flytte det til en anden computer.
# ==============================================================================

echo -e "\033[0;31m[*] Klargør OMNI_HUNTER til overførsel...\033[0m"

# Navnet på den fil vi bygger
OUTPUT_FILE="omni_hunter_deploy.tar.gz"

# Sletter gamle cache-filer der fylder for at gøre zip-filen lille
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo -e "\033[0;32m[+] Pakker kildekode og moduler...\033[0m"

# Vi bruger tar, og vi EKSKLUDERER bevidst sikkerhedsfiler og venv
tar -czf $OUTPUT_FILE \
    --exclude="venv" \
    --exclude=".git" \
    --exclude="*.vault" \
    --exclude="*.key" \
    --exclude="workspaces" \
    --exclude="loot_evidence" \
    .

echo -e "\033[0;32m[✓] EKSPORT FULDFØRT!\033[0m"
echo -e "\033[1;37mSystemet er nu pakket ned i filen:\033[0m \033[1;36m$OUTPUT_FILE\033[0m\n"

echo -e "Sådan flytter du den til din bærbar:"
echo -e "1. Sæt et USB-stik i og kopier \033[1;36m$OUTPUT_FILE\033[0m over."
echo -e "2. Sæt USB'en i bærbaren, og kopier filen over på skrivebordet."
echo -e "3. Åbn en terminal på bærbaren og skriv:"
echo -e "   \033[1;33mtar -xzf omni_hunter_deploy.tar.gz\033[0m"
echo -e "   \033[1;33m./goliath.sh\033[0m"
echo -e "\n\033[0;31mBEMÆRK:\033[0m Bærbaren vil automatisk bygge et nyt venv og generere nye krypteringsnøgler."

