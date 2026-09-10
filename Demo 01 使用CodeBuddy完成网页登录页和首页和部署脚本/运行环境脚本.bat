@echo off
echo ============================================
echo   Runtime Environment Check
echo ============================================
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.9+ and check "Add to PATH".
    pause
    exit /b 1
)
echo Python environment OK.
echo Demo 01 is a static website; no extra dependencies needed.
pause
