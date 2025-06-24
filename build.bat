@echo off
REM Force close the running application before building
TASKKILL /IM AppVolumeControl.exe /F >nul 2>&1

echo Building AppVolumeControl.exe with custom icon...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found. Make sure to install dependencies:
    echo    pip install -r requirements.txt
)

REM Build with PyInstaller
pyinstaller --onefile --windowed --icon=icon.ico --name=AppVolumeControl --add-data "icon.ico;." main.py

if errorlevel 1 (
    echo ❌ Build failed! Check the error messages above.
    echo 💡 Make sure PyInstaller is installed: pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo ✅ Build complete! Check the dist folder
echo 📁 The exe file will be created as AppVolumeControl.exe
pause 