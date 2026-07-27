#!/bin/bash
set -e

echo "Starting FRIDAY v2.0..."

# Load environment
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check for API key
if grep -q "sk-or-v1-your-key-here" .env 2>/dev/null; then
    echo "WARNING: Default API key detected. Edit .env to add your OpenRouter key."
fi

echo "Starting FRIDAY core + CLI..."
python -m friday.main
