#!/usr/bin/env bash
# FRIDAY post-login — placed in /etc/profile.d/ by setup.sh

FRIDAY_DIR=""
for d in /opt/friday "$HOME/Projects/Friday" "$HOME/friday"; do
    if [[ -f "$d/friday/main.py" ]]; then
        FRIDAY_DIR="$d"; break
    fi
done

if [[ -z "$FRIDAY_DIR" ]]; then
    return 0
fi

VENV_PYTHON="$FRIDAY_DIR/.venv/bin/python"
FRIDAY_MAIN="$FRIDAY_DIR/friday/main.py"

if [[ ! -f "$VENV_PYTHON" ]] || [[ ! -f "$FRIDAY_MAIN" ]]; then
    return 0
fi

CONFIG_DIR="$HOME/.config/friday"
PERMIT_FILE="$CONFIG_DIR/autostart"
mkdir -p "$CONFIG_DIR"

# First login — ask permission
if [[ ! -f "$PERMIT_FILE" ]] && [[ -z ${FRIDAY_ASKED_PERMISSION:-} ]]; then
    export FRIDAY_ASKED_PERMISSION=1
    echo ""
    "$VENV_PYTHON" "$FRIDAY_MAIN" --welcome 2>/dev/null || true
    echo -n "  [FRIDAY] Start automatically after login? [Y/n] "
    read -r reply </dev/tty 2>/dev/null || reply="y"
    case "$reply" in
        n|N|no|NO) echo "no" > "$PERMIT_FILE"; echo "  [FRIDAY] OK. Type 'friday' to launch." ;;
        *) echo "yes" > "$PERMIT_FILE"
           echo "  [FRIDAY] Auto-start enabled. Type 'friday' for REPL."
           # Start daemon now (first time)
           "$VENV_PYTHON" "$FRIDAY_MAIN" --daemon &
           disown ;;
    esac
    echo ""
    return 0
fi

# Subsequent logins — auto-start if permitted
if [[ "$(cat "$PERMIT_FILE" 2>/dev/null)" == "yes" ]] && [[ -z ${FRIDAY_DAEMON_STARTED:-} ]]; then
    export FRIDAY_DAEMON_STARTED=1
    # Check if already running
    if ! pgrep -f "friday/main.py --daemon" > /dev/null 2>&1; then
        "$VENV_PYTHON" "$FRIDAY_MAIN" --daemon &
        disown
    fi
fi

# Shell function to launch FRIDAY REPL
friday() {
    cd "$FRIDAY_DIR" || return 1
    "$VENV_PYTHON" "$FRIDAY_MAIN" "$@"
}
