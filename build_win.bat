@echo off
echo Build REBiRTH.exe pour Windows...

cd /d "%~dp0"
call venv\Scripts\activate.bat

:: Installe PyInstaller si pas présent
pip install pyinstaller -q

:: Build
pyinstaller build_win.spec --clean --noconfirm

echo.
echo Termine ! REBiRTH.exe se trouve dans dist\REBiRTH\
pause
