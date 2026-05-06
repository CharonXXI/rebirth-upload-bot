@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ==========================================
echo  REMUX TOOL - Mode AUTO
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERREUR] Lancez install_deps.bat d'abord
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
if exist "tools" set "PATH=%~dp0tools;%PATH%"

.venv\Scripts\python.exe main.py --auto

pause
exit /b 0
