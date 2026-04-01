#!/bin/bash
# Script de build macOS — génère REBiRTH.app
echo "🔨 Build REBiRTH.app pour macOS..."

cd "$(dirname "$0")"
source venv/bin/activate

# Installe PyInstaller si pas présent
pip install pyinstaller -q

# Build
pyinstaller build_mac.spec --clean --noconfirm

echo ""
echo "✅ Terminé ! REBiRTH.app se trouve dans dist/"
echo "   Tu peux le glisser dans ton dossier Applications."
