@echo off
REM Rebuild claude-usage.exe after editing claude_usage.py.
REM Requires: python on PATH. PyInstaller is installed automatically if missing.
python -m pip show pyinstaller >nul 2>&1 || python -m pip install --user pyinstaller
python -m PyInstaller --onefile --console --name claude-usage --clean claude_usage.py
echo.
echo Done. The executable is at: dist\claude-usage.exe
