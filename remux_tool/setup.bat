@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ==========================================
echo  REMUX TOOL - Installation
echo ==========================================
echo.

REM === Etape 1: Verification Python ===
echo [1/4] Verification de Python...

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY=py -3"
    echo       Python trouve via py launcher
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        set "PY=python"
        echo       Python trouve via python
    ) else (
        echo [ERREUR] Python introuvable!
        echo          Telecharge Python depuis https://www.python.org/downloads/
        echo          Coche "Add Python to PATH" lors de l'installation
        pause
        exit /b 1
    )
)

REM === Etape 2: Creation venv ===
echo.
echo [2/4] Creation de l'environnement virtuel...

if exist ".venv\Scripts\python.exe" (
    echo       .venv existe deja
) else (
    %PY% -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERREUR] Echec creation venv
        pause
        exit /b 1
    )
    echo       .venv cree
)

REM === Etape 3: Installation dependances ===
echo.
echo [3/4] Installation des dependances...

.venv\Scripts\python.exe -m pip install --upgrade pip --quiet 2>nul
.venv\Scripts\python.exe -m pip install click requests --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] pip install a echoue, tentative alternative...
    .venv\Scripts\pip.exe install click requests
)
echo       Dependances installees

REM === Etape 4: Verification outils externes ===
echo.
echo [4/4] Verification des outils externes...

set "MISSING="

REM MakeMKV
where makemkvcon >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       [OK] makemkvcon
) else (
    if exist "C:\Program Files (x86)\MakeMKV\makemkvcon.exe" (
        echo       [OK] makemkvcon (Program Files x86)
    ) else if exist "C:\Program Files\MakeMKV\makemkvcon.exe" (
        echo       [OK] makemkvcon (Program Files)
    ) else (
        echo       [X] makemkvcon - https://www.makemkv.com/download/
        set "MISSING=1"
    )
)

REM MediaInfo
where mediainfo >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       [OK] mediainfo
) else (
    if exist "C:\Program Files\MediaInfo\MediaInfo.exe" (
        echo       [OK] mediainfo (Program Files)
    ) else (
        echo       [X] mediainfo - https://mediaarea.net/en/MediaInfo/Download
        set "MISSING=1"
    )
)

REM MKVToolNix
where mkvmerge >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       [OK] mkvmerge
) else (
    if exist "C:\Program Files\MKVToolNix\mkvmerge.exe" (
        echo       [OK] mkvmerge (Program Files)
    ) else (
        echo       [X] mkvmerge - https://mkvtoolnix.download/
        set "MISSING=1"
    )
)

REM FFprobe (optionnel)
where ffprobe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       [OK] ffprobe
) else (
    echo       [~] ffprobe non trouve (optionnel, MediaInfo suffit)
)

echo.
if defined MISSING (
    echo [ATTENTION] Certains outils sont manquants.
    echo             Installez-les avant de lancer le remux.
) else (
    echo [OK] Tous les outils sont installes!
)

REM === Creation dossiers ===
if not exist "FULL" mkdir FULL
if not exist "OUTPUT" mkdir OUTPUT

echo.
echo ==========================================
echo  Installation terminee!
echo.
echo  Placez vos ISO/BDMV dans le dossier FULL
echo  puis lancez: run_interactive.bat
echo ==========================================
echo.
pause
exit /b 0
