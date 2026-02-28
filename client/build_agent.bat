@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building SysConnect Agent...
pyinstaller --noconsole --onefile --name SysConnectAgent main.py

echo.
echo Build complete! Your silent executable is in the "dist" folder.
pause
