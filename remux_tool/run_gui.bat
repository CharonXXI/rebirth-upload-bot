@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo [SETUP] Creation de l'environnement virtuel...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python -c "import webview" 2>nul
if errorlevel 1 (
    echo [SETUP] Installation de pywebview...
    pip install pywebview
)

echo.
echo ============================================
echo   REMUX TOOL - GUI
echo ============================================
echo.
python gui.py
pause
