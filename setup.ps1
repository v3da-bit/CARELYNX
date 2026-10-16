# ==============================================================================
# CARELYNX — Automated Single-Command Setup (Windows PowerShell)
# Downloads and installs all backend Python & frontend Node.js dependencies,
# initializes local configuration, runs migrations, and generates sample records.
# ==============================================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  CARELYNX Automated Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Error "Python 3 was not found on PATH. Please install Python 3.10+ and add it to PATH."
    exit 1
}

& $pythonCmd run.py setup

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  All dependencies have been successfully installed!" -ForegroundColor Green
Write-Host "  To start the full-stack system, run:" -ForegroundColor Green
Write-Host "    .\run_dev.ps1" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Green
