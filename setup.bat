@echo off
REM ==============================================================================
REM CARELYNX — Automated Single-Command Setup (Windows CMD)
REM Downloads and installs all backend Python & frontend Node.js dependencies,
REM initializes local configuration, runs migrations, and generates sample records.
REM ==============================================================================

cd /d "%~dp0"
echo =================================================================
echo   CARELYNX Automated Setup (Windows)
echo =================================================================

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Python 3 was not found on PATH.
        echo Please install Python 3.10+ and check "Add python.exe to PATH".
        pause
        exit /b 1
    ) else (
        py run.py setup
        goto finished
    )
) else (
    python run.py setup
    goto finished
)

:finished
echo.
echo =================================================================
echo   All dependencies have been successfully installed!
echo   To start the full-stack system, run:
echo     run_dev.bat
echo =================================================================
