#!/bin/bash
set -e

echo "================================================"
echo "  FRIDAY v2.0 Setup"
echo "================================================"

# System dependencies
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    sudo pacman -S python --noconfirm
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cat > .env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OLLAMA_URL=http://127.0.0.1:11434
FRIDAY_PORT=8000
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite+aiosqlite:///./data/friday.db
LOG_LEVEL=INFO
EOF
    echo "Edit .env to set your OpenRouter API key."
fi

# Create data directories
mkdir -p data/{knowledge_graph,vector_db,projects,logs}

echo ""
echo "================================================"
echo "  Setup complete!"
echo "  Run: source .venv/bin/activate && python -m friday.main"
echo "================================================"
