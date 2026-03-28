@echo off
:: Double-cliquer pour lancer REBiRTH Upload Bot

:: Va dans le dossier du script
cd /d "%~dp0"

:: Active le venv
call venv\Scripts\activate.bat

:: Lance le bot
python app.py

:: Garde la fenêtre ouverte en cas d'erreur
if errorlevel 1 pause
