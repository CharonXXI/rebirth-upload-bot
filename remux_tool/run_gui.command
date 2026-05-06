#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
    echo "[SETUP] Création de l'environnement virtuel..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

if ! python -c "import webview" 2>/dev/null; then
    echo "[SETUP] Installation de pywebview..."
    pip install 'pywebview[cocoa]' 2>/dev/null || pip install pywebview
fi

echo ""
echo "============================================"
echo "  REMUX TOOL - GUI"
echo "============================================"
echo ""
python gui.py
