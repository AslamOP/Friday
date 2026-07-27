#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/AslamOP/Friday.git"
INSTALL_DIR="/opt/friday"

# If running from within the repo, use that path
if [[ -f "$(dirname "$0")/../friday/main.py" ]]; then
    DIR="$(cd "$(dirname "$0")/.." && pwd)"
else
    # Standalone — clone from GitHub
    echo "==> Cloning FRIDAY from GitHub…"
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$USER:$USER" "$INSTALL_DIR"
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
    DIR="$INSTALL_DIR"
fi

cd "$DIR"

# Create venv if missing
if [[ ! -d "$DIR/.venv" ]]; then
    echo "==> Creating virtual environment…"
    python3 -m venv .venv
fi
VENV_PYTHON="$DIR/.venv/bin/python"

# Install FRIDAY pip package
echo "==> Installing FRIDAY package…"
"$VENV_PYTHON" -m pip install --quiet -e .

# ── 1. Systemd service ──
echo "[1/4] Installing systemd service…"
sed -e "s|__USER__|$USER|g" -e "s|__FRIDAY_DIR__|$DIR|g" "$DIR/install/friday.service" | sudo tee /etc/systemd/system/friday.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable friday.service
echo "  ✓ friday.service enabled"

# ── 2. Login welcome hook ──
echo "[2/4] Installing login welcome hook…"
sudo tee /etc/profile.d/friday.sh > /dev/null < "$DIR/install/friday-welcome.sh"
sudo chmod 644 /etc/profile.d/friday.sh
echo "  ✓ /etc/profile.d/friday.sh installed"

# ── 3. Ollama models ──
echo "[3/4] Pulling Ollama models…"
if command -v ollama &>/dev/null; then
    ollama pull nomic-embed-text 2>/dev/null || echo "  ! nomic-embed-text pull skipped"
    ollama pull llama3.2 2>/dev/null || echo "  ! llama3.2 pull skipped"
    echo "  ✓ Ollama models ready"
else
    echo "  ! Ollama not found — install: sudo pacman -S ollama"
fi

# ── 4. Verify ──
echo "[4/4] Verifying setup…"
if "$VENV_PYTHON" -c "from friday import __version__; print(__version__)" 2>/dev/null; then
    echo "  ✓ FRIDAY v$("$VENV_PYTHON" -c "from friday import __version__; print(__version__)") ready"
else
    echo "  ! Python import failed — check venv: $VENV_PYTHON"
fi

echo ""
echo "==> Done. FRIDAY will:"
echo "    • Start at boot    (systemd friday.service)"
echo "    • Welcome you       (after login, /etc/profile.d/friday.sh)"
echo "    • Launch on demand  (type 'friday' in your shell)"
echo ""
echo "  sudo systemctl start friday.service   # start now"
echo "  friday                                 # enter the REPL"
