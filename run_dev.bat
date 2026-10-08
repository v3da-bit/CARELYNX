@echo off
REM CARELYNX — Windows Command Prompt Runner
setlocal

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python run.py %*
    goto :eof
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -3 run.py %*
    goto :eof
)

echo ERROR: Python 3 is required but was not found on your PATH.
echo Please install Python 3.10+ from https://www.python.org and check "Add Python to PATH".
pause
exit /b 1
