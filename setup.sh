#!/usr/bin/env bash
# ==============================================================================
# CARELYNX — Automated Single-Command Setup (Linux & macOS)
# Downloads and installs all backend Python & frontend Node.js dependencies,
# initializes local configuration, runs migrations, and generates sample records.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================="
echo "  CARELYNX Automated Setup"
echo "================================================================="

# 1. Verify Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 is required but neither 'python3' nor 'python' was found on PATH."
    echo "Please install Python 3.10+ and ensure it is available in your PATH."
    exit 1
fi

# 2. Verify Node.js and npm
if ! command -v node &>/dev/null; then
    echo "WARNING: 'node' was not found on PATH. Next.js frontend requires Node.js 18+."
fi

if ! command -v npm &>/dev/null; then
    echo "WARNING: 'npm' was not found on PATH."
fi

# 3. Delegate to the cross-platform setup engine
$PYTHON_CMD run.py setup

echo ""
echo "================================================================="
echo "  All dependencies have been successfully installed!"
echo "  To start the full-stack system concurrently, simply run:"
echo "    ./run_dev.sh"
echo "================================================================="
