@echo off
REM Force close the running application before building
TASKKILL /IM AppVolumeControl.exe /F >nul 2>&1

echo Building AppVolumeControl.exe with custom icon...
pyinstaller --onefile --windowed --icon=icon.ico --name=AppVolumeControl --add-data "icon.ico;." --add-data "nircmd.exe;." volume_keys.py
echo.
echo Build complete! Check the dist folder
echo The exe file will be created as AppVolumeControl.exe
pause 