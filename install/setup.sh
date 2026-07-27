#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> FRIDAY Boot + Login Setup"
echo ""

cd "$DIR"

# Create venv if missing
if [[ ! -d "$DIR/.venv" ]]; then
    echo "[1/4] Creating virtual environment…"
    python3 -m venv .venv
fi
VENV_PYTHON="$DIR/.venv/bin/python"

echo "[2/4] Installing FRIDAY package…"
"$VENV_PYTHON" -m pip install --quiet -e .

echo "[3/4] Installing systemd service (boot)…"
sed -e "s|__USER__|$USER|g" -e "s|__FRIDAY_DIR__|$DIR|g" "$DIR/install/friday.service" | sudo tee /etc/systemd/system/friday.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable friday.service
echo "  ✓ friday.service — starts at boot"

echo "[4/4] Installing login hook…"
sudo tee /etc/profile.d/friday.sh > /dev/null < "$DIR/install/friday-welcome.sh"
sudo chmod 644 /etc/profile.d/friday.sh
echo "  ✓ /etc/profile.d/friday.sh — login welcome"

# Verify
if "$VENV_PYTHON" -c "from friday import __version__; print(__version__)" 2>/dev/null; then
    echo ""
    echo "  ✓ FRIDAY v$("$VENV_PYTHON" -c "from friday import __version__; print(__version__)") ready"
fi

echo ""
echo "==> Done. FRIDAY will:"
echo "    • Start at boot       (systemd friday.service)"
echo "    • Ask permission      (first login, /etc/profile.d/friday.sh)"
echo "    • Launch on demand    (type 'friday' in your shell)"
echo ""
echo "  sudo systemctl start friday.service   # start now"
echo "  friday                                 # enter the REPL"
