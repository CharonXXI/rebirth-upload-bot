@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ==========================================
echo  Installation des dependances Python
echo ==========================================
echo.

REM Verifier Python
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        set "PY=python"
    ) else (
        echo [ERREUR] Python introuvable!
        echo          Installe Python depuis https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo [1/3] Python trouve: %PY%

REM Creer venv si absent
if not exist ".venv\Scripts\python.exe" (
    echo [2/3] Creation du venv...
    %PY% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] Echec creation venv
        pause
        exit /b 1
    )
) else (
    echo [2/3] venv existe deja
)

REM Installer les deps
echo [3/3] Installation click + requests...
.venv\Scripts\python.exe -m pip install click requests --quiet

if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Installation terminee!
    echo.
    echo Lancez maintenant: run.bat
) else (
    echo.
    echo [ERREUR] Installation echouee
)

echo.
pause
exit /b 0
