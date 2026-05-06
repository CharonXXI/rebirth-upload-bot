#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "=========================================="
echo "[SETUP] Environnement virtuel + deps (macOS/Linux)"
echo "=========================================="

OS="$(uname -s || echo '')"
case "$OS" in
  Darwin)  PLATFORM="macOS" ;;
  Linux)   PLATFORM="Linux" ;;
  *)       PLATFORM="Unknown" ;;
esac
echo "[INFO] Plateforme detectee : $PLATFORM"
sleep 1

# 1) Python/venv
if command -v python3 >/dev/null 2>&1 ; then
  PYBIN="python3"
else
  echo "[ERREUR] python3 introuvable. Installez Python 3 (https://www.python.org/) puis relancez."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/5] Creation du venv..."
  "$PYBIN" -m venv .venv
  echo "[INFO] Pause 2s apres creation du venv..."; sleep 2
else
  echo "[1/5] venv deja present."
fi

VENV_PY=".venv/bin/python"
VENV_PIP="$VENV_PY -m pip"

echo "[2/5] Upgrade pip/setuptools/wheel (optionnel)..."
set +e
$VENV_PIP install --upgrade pip setuptools wheel --no-cache-dir
UP_RC=$?
set -e
if [ "$UP_RC" -ne 0 ]; then
  echo "[AVERTISSEMENT] Upgrade pip a echoue. On continue avec la version actuelle."
fi
echo "[INFO] Pause 2s..."; sleep 2

echo "[3/5] Installation des dependances Python..."
$VENV_PIP install -r requirements.txt
echo "[INFO] Pause 2s..."; sleep 2

# 4) Outils externes
echo "[4/5] Verification des outils externes (MakeMKV, MediaInfo, MKVToolNix, FFmpeg)..."
missing=()

# Helpers
have() { command -v "$1" >/dev/null 2>&1; }
try_paths() {
  # args: exe_name paths...
  local exe="$1"; shift
  if have "$exe"; then return 0; fi
  for p in "$@"; do
    if [ -x "$p" ]; then
      echo "  [~] $exe trouve: $p"
      export PATH="$(dirname "$p"):$PATH"
      return 0
    fi
  done
  return 1
}

# Common mac paths (match those used in your Python code)
MI_CANDIDATES=(
  "/opt/homebrew/bin/mediainfo"
  "/usr/local/bin/mediainfo"
  "/usr/bin/mediainfo"
  "/Applications/MediaInfo.app/Contents/MacOS/MediaInfo"
)
FFP_CANDIDATES=(
  "/opt/homebrew/bin/ffprobe"
  "/usr/local/bin/ffprobe"
  "/usr/bin/ffprobe"
  "/opt/homebrew/opt/ffmpeg/bin/ffprobe"
)
MKV_CANDIDATES=(
  "/opt/homebrew/bin/mkvmerge"
  "/usr/local/bin/mkvmerge"
  "/usr/bin/mkvmerge"
  "/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge"
  "/Applications/MKVToolNix-88.0.app/Contents/MacOS/mkvmerge"
)
MMK_CANDIDATES=(
  "/Applications/MakeMKV.app/Contents/MacOS/makemkvcon"
  "/usr/local/bin/makemkvcon"
  "/opt/homebrew/bin/makemkvcon"
  "/usr/bin/makemkvcon"
)

# makemkvcon
if ! try_paths "makemkvcon" "${MMK_CANDIDATES[@]}"; then
  echo "  [X] makemkvcon introuvable"
  missing+=("MakeMKV")
fi
# mediainfo
if ! try_paths "mediainfo" "${MI_CANDIDATES[@]}"; then
  echo "  [X] mediainfo introuvable"
  missing+=("MediaInfo")
fi
# mkvmerge
if ! try_paths "mkvmerge" "${MKV_CANDIDATES[@]}"; then
  echo "  [X] mkvmerge introuvable"
  missing+=("MKVToolNix")
fi
# ffprobe
if ! try_paths "ffprobe" "${FFP_CANDIDATES[@]}"; then
  echo "  [X] ffprobe introuvable"
  missing+=("FFmpeg")
fi

if [ "${#missing[@]}" -gt 0 ]; then
  echo ""
  echo "[ATTENTION] Outils manquants : ${missing[*]}"
  if [ "$PLATFORM" = "macOS" ]; then
    echo "  Vous pouvez les installer via Homebrew :"
    echo "    brew install --cask makemkv"
    echo "    brew install mediainfo mkvtoolnix ffmpeg"
  elif [ "$PLATFORM" = "Linux" ]; then
    echo "  Exemple Ubuntu/Debian :"
    echo "    sudo apt-get update && sudo apt-get install -y ffmpeg mediainfo mkvtoolnix"
    echo "  (MakeMKV peut necessiter un paquet tiers ou AppImage)"
  fi
  echo ""
else
  echo "[OK] Tous les outils externes necessaires semblent disponibles."
fi

# 5) Versions
echo "[5/5] Versions detectees:"
set +e
if have makemkvcon; then echo "  [makemkvcon] $(makemkvcon -r --version 2>/dev/null | head -n1)"; fi
if have mediainfo;  then echo "  [mediainfo] $(mediainfo --Version | head -n1)"; fi
if have mkvmerge;   then echo "  [mkvmerge] $(mkvmerge --version | head -n1)"; fi
if have ffprobe;    then echo "  [ffprobe] $(ffprobe -version 2>/dev/null | head -n1)"; fi
set -e

echo ""
echo "[OK] Setup termine. Lancez :"
echo "  .venv/bin/python main.py"
