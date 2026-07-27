#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/anomalyco/friday.git"
INSTALL_DIR="${FRIDAY_DIR:-$HOME/friday}"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}━━━ FRIDAY AI OS Installer ━━━${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux)
        if command -v pacman &>/dev/null; then
            echo -e "${GREEN}Detected Arch Linux${NC}"
            sudo pacman -Sy --noconfirm python python-pip python-virtualenv nodejs npm git
        elif command -v apt &>/dev/null; then
            echo -e "${GREEN}Detected Debian/Ubuntu${NC}"
            sudo apt update && sudo apt install -y python3 python3-pip python3-venv nodejs npm git xclip
        else
            echo -e "${RED}Unsupported Linux distro. Install python3, pip, venv, git manually.${NC}"
            exit 1
        fi
        ;;
    Darwin)
        echo -e "${GREEN}Detected macOS${NC}"
        if ! command -v brew &>/dev/null; then
            echo -e "${CYAN}Installing Homebrew...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.11 node git
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
        echo "For Windows, use WSL2: https://learn.microsoft.com/en-us/windows/wsl/install"
        exit 1
        ;;
esac

# Clone or pull
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}Updating existing installation...${NC}"
    cd "$INSTALL_DIR" && git pull
else
    echo -e "${CYAN}Cloning FRIDAY...${NC}"
    git clone "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Python venv
if [ ! -d ".venv" ]; then
    echo -e "${CYAN}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install FRIDAY
echo -e "${CYAN}Installing FRIDAY and dependencies...${NC}"
pip install --upgrade pip
pip install -e .

# .env
if [ ! -f ".env" ]; then
    echo -e "${CYAN}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Edit .env to add your API keys.${NC}"
fi

# Systemd service (Linux only)
if [ "$OS" = "Linux" ] && [ -f /proc/1/comm ] && [ "$(cat /proc/1/comm)" = "systemd" ]; then
    echo -e "${CYAN}Setting up systemd service...${NC}"
    sudo bash install/setup.sh
fi

# Login profile (Linux only)
if [ "$OS" = "Linux" ]; then
    echo -e "${CYAN}Setting up login profile...${NC}"
    if [ ! -f /etc/profile.d/friday.sh ]; then
        sudo cp install/friday-welcome.sh /etc/profile.d/friday.sh
        echo -e "${GREEN}Installed /etc/profile.d/friday.sh${NC}"
    fi
fi

echo ""
echo -e "${GREEN}━━━ FRIDAY installed successfully! ━━━${NC}"
echo -e ""
echo -e "  Run REPL:  ${CYAN}cd $INSTALL_DIR && .venv/bin/python friday/main.py${NC}"
echo -e "  Run GUI:   ${CYAN}cd $INSTALL_DIR && .venv/bin/python friday/main.py --gui${NC}"
echo -e ""
echo -e "  Edit ${CYAN}$INSTALL_DIR/.env${NC} to add API keys."
echo -e "  Type ${CYAN}/help${NC} inside FRIDAY for commands."
