#!/usr/bin/env bash
# FRIDAY post-login welcome — placed in /etc/profile.d/ by setup.sh
FRIDAY_DIR="/home/king/Projects/Friday"
VENV_PYTHON="$FRIDAY_DIR/.venv/bin/python"
FRIDAY_MAIN="$FRIDAY_DIR/friday/main.py"

# Show welcome message (once per session)
if [[ -z ${FRIDAY_WELCOME_SHOWN:-} ]]; then
    export FRIDAY_WELCOME_SHOWN=1
    if command -v systemctl &>/dev/null && systemctl is-active --quiet friday.service 2>/dev/null; then
        echo "  [FRIDAY] Service is running"
    fi
    "$VENV_PYTHON" "$FRIDAY_MAIN" --welcome 2>/dev/null || true
fi

# Shell function to launch FRIDAY REPL
friday() {
    cd "$FRIDAY_DIR" || return 1
    "$VENV_PYTHON" "$FRIDAY_MAIN" "$@"
}
