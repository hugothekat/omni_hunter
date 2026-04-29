#!/bin/bash
# ==============================================================================
# 🚀 GOLIATH APEX BOOTSTRAPPER (PETFE EDITION)
# Sikrer miljøet, installerer afhængigheder og starter OMNI_HUNTER autonomt.
# ==============================================================================

# Farver til terminal output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  [ PETFE ] GOLIATH APEX BOOTSTRAP SEQUENCE INITIATED ${NC}"
echo -e "${CYAN}======================================================${NC}"

# 1. Tjekker for root-rettigheder til systempakker
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}[*] Bed om sudo-rettigheder for at verificere systempakker (nmap, tor, tesseract)...${NC}"
  sudo -v || exit 1
fi

# 2. Systemafhængigheder (Parrot/Debian/Ubuntu)
echo -e "\n${GREEN}[+] Verificerer system-værktøjer...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip nmap tesseract-ocr libimage-exiftool-perl ripgrep tor curl jq > /dev/null

# Sørg for at Tor kører
sudo systemctl enable tor > /dev/null 2>&1
sudo systemctl start tor > /dev/null 2>&1

# 3. Virtual Environment (venv) opsætning
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[*] Opretter isoleret Python miljø (venv)...${NC}"
    python3 -m venv venv
fi

# Aktiver venv
source venv/bin/activate

# 4. Opdater Pip og installer Python afhængigheder
echo -e "${GREEN}[+] Synkroniserer Python våbenarsenal...${NC}"
python3 -m pip install --upgrade pip -q

cat << 'EOF' > .goliath_reqs.txt
requests>=2.31.0
requests-cache>=1.1.0
aiohttp>=3.8.5
beautifulsoup4>=4.12.2
fake-useragent>=1.2.1
playwright>=1.37.0
selenium>=4.11.2
undetected-chromedriver>=3.5.3
stem>=1.8.1
pydantic>=2.3.0
cryptography>=41.0.3
structlog>=23.1.0
python-dotenv>=1.0.0
shodan>=1.29.1
censys>=2.2.0
python-nmap>=0.7.1
paramiko>=3.3.1
securitytrails>=1.0.0
virustotal-api>=1.1.11
alienvault-api>=0.1.0
greynoise>=2.1.0
mistralai>=0.1.2
pyfiglet>=1.0.2
python-whois>=0.8.0
Pillow>=10.0.0
pytesseract>=0.3.10
pandas>=2.0.3
numpy>=1.25.2
scikit-learn>=1.3.0
netifaces>=0.11.0
dnspython>=2.4.2
bleach>=6.0.0
EOF

python3 -m pip install -r .goliath_reqs.txt -q
rm .goliath_reqs.txt

# 5. Playwright Browsere (kun hvis de mangler)
if [ ! -d ~/.cache/ms-playwright ]; then
    echo -e "${YELLOW}[*] Installerer asynkrone Playwright browsere (første kørsel)...${NC}"
    python3 -m playwright install chromium firefox > /dev/null 2>&1
fi

echo -e "\n${GREEN}[✓] MILJØ SIKRET. OVERGIVER KONTROL TIL GOLIATH ORCHESTRATOR...${NC}\n"
sleep 1

# 6. Start Main (Send evt. argumenter videre)
python3 main.py "$@"

# Deaktiver venv når programmet lukkes
deactivate
