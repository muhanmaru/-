@echo off
echo ===================================
echo   Quick Phrase - Build with Icon
echo ===================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install pyinstaller pillow >nul 2>nul

echo [2/3] Generating icon...
python create_icon.py

echo [3/3] Building QuickPhrase.exe...
if exist "app_icon.ico" (
    pyinstaller --onefile --noconsole --name QuickPhrase --icon=app_icon.ico quick_phrase.py
) else (
    pyinstaller --onefile --noconsole --name QuickPhrase quick_phrase.py
)

if exist "dist\QuickPhrase.exe" (
    echo.
    echo ===================================
    echo   Build successful!
    echo   Output: dist\QuickPhrase.exe
    echo ===================================
) else (
    echo [ERROR] Build failed.
)
pause
