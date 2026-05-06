@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ==========================================
echo  REMUX TOOL - Demarrage
echo ==========================================
echo.

REM Verifier le venv
if not exist ".venv\Scripts\python.exe" (
    echo [ERREUR] Environnement virtuel introuvable.
    echo          Lancez setup.bat d'abord.
    pause
    exit /b 1
)

set "VENV_PY=.venv\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"

REM Ajouter tools/ au PATH si present
if exist "tools\MediaInfo.exe" (
    set "PATH=%~dp0tools;%PATH%"
)
if exist "tools\ffprobe.exe" (
    set "PATH=%~dp0tools;%PATH%"
)
if exist "tools\mkvmerge.exe" (
    set "PATH=%~dp0tools;%PATH%"
)

echo [INFO] Dossier: %CD%
echo [INFO] Python : %VENV_PY%
echo.

"%VENV_PY%" main.py
set "RC=!ERRORLEVEL!"

echo.
if "!RC!"=="0" (
    echo [OK] Termine avec succes.
) else (
    echo [ERREUR] Code retour: !RC!
)

echo.
pause
exit /b !RC!
