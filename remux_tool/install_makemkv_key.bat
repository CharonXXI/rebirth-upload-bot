@echo off
setlocal
chcp 65001 >nul 2>&1

echo.
echo ==========================================
echo  MakeMKV - Enregistrement de la cle beta
echo ==========================================
echo.

set "KEY=T-sJ5R5BKxhD671U9s0teXbyP19MhCkkkB7rmnNbb1aEHaqveiVqyI3RXGMHDXhoyNUC"

echo Cle: %KEY%
echo Valide jusqu'a: Fin mai 2026
echo.

echo [1/2] Ecriture dans le registre Windows...

REM Créer la clé dans le registre (HKCU\Software\MakeMKV\app_Key)
reg add "HKCU\Software\MakeMKV" /v "app_Key" /t REG_SZ /d "%KEY%" /f >nul 2>&1

if %ERRORLEVEL%==0 (
    echo       [OK] Cle enregistree dans le registre
) else (
    echo       [ERREUR] Impossible d'ecrire dans le registre
    echo       Essayez manuellement: MakeMKV GUI ^> Help ^> Register
    pause
    exit /b 1
)

echo.
echo [2/2] Verification...

reg query "HKCU\Software\MakeMKV" /v "app_Key" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo       [OK] Cle presente dans le registre
) else (
    echo       [WARN] Verification echouee
)

echo.
echo ==========================================
echo  Cle installee avec succes!
echo.
echo  Vous pouvez maintenant lancer:
echo  - MakeMKV (GUI) pour verifier
echo  - run_interactive.bat pour le remux
echo ==========================================
echo.
pause
exit /b 0
