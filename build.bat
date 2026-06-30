@echo off
echo ===================================
echo   Quick Phrase - Build Script
echo ===================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Installing PyInstaller...
pip install pyinstaller >nul 2>nul

echo [2/2] Building QuickPhrase.exe...
pyinstaller --onefile --noconsole --name QuickPhrase --icon=NONE quick_phrase.py

if exist "dist\QuickPhrase.exe" (
    echo.
    echo ===================================
    echo   Build successful!
    echo   Output: dist\QuickPhrase.exe
    echo ===================================
    echo.
    echo You can copy QuickPhrase.exe anywhere and run it.
    echo The phrases.json data file will be created next to the exe.
) else (
    echo.
    echo [ERROR] Build failed. Check the output above for details.
)
pause
