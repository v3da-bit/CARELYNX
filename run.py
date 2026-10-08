#!/usr/bin/env python3
"""CARELYNX Cross-Platform Orchestrator and Runner.

Works seamlessly out-of-the-box on:
  - Windows (cmd.exe, PowerShell, Windows Terminal)
  - macOS (Apple Silicon & Intel, bash, zsh)
  - Linux (Ubuntu, Debian, Fedora, Arch, etc.)

Usage:
  python run.py dev             # Run both API (backend) and Web (frontend) concurrently
  python run.py api             # Run FastAPI backend only (http://localhost:8000)
  python run.py web             # Run Next.js frontend only (http://localhost:3000)
  python run.py setup           # Create venv, install Python & Node dependencies, run migrations
  python run.py test            # Run API integration and safety tests
  python run.py generate-samples # Generate sample medical PDFs for testing
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
API_DIR = REPO_ROOT / "apps" / "api"
WEB_DIR = REPO_ROOT / "apps" / "web"
IS_WINDOWS = platform.system() == "Windows"


def get_venv_python() -> Path:
    """Return platform-specific Python interpreter path in apps/api/.venv."""
    if IS_WINDOWS:
        candidate = API_DIR / ".venv" / "Scripts" / "python.exe"
        if candidate.exists():
            return candidate
        # Fallback to general python.exe if venv not found
        return Path(sys.executable)
    else:
        candidate = API_DIR / ".venv" / "bin" / "python"
        if candidate.exists():
            return candidate
        return Path(sys.executable)


def get_venv_bin(name: str) -> str:
    """Return platform-specific binary inside apps/api/.venv or system PATH."""
    if IS_WINDOWS:
        # Check .venv/Scripts/<name>.exe
        venv_bin = API_DIR / ".venv" / "Scripts" / f"{name}.exe"
        if venv_bin.exists():
            return str(venv_bin)
        venv_script = API_DIR / ".venv" / "Scripts" / name
        if venv_script.exists():
            return str(venv_script)
    else:
        venv_bin = API_DIR / ".venv" / "bin" / name
        if venv_bin.exists():
            return str(venv_bin)

    # Fallback to system PATH
    which_bin = shutil.which(name)
    return which_bin or name


def get_npm_cmd() -> str:
    """Return cross-platform npm command name."""
    if IS_WINDOWS:
        npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
        return npm or "npm.cmd"
    return "npm"


def stream_output(process: subprocess.Popen, prefix: str, color_code: str = "") -> None:
    """Stream process stdout/stderr line by line with a labeled prefix."""
    reset_code = "\033[0m" if color_code else ""
    try:
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                print(f"{color_code}[{prefix}]{reset_code} {line.rstrip()}", flush=True)
    except Exception:
        pass


def run_setup() -> int:
    """Bootstrap virtualenv, install dependencies, run migrations, and generate samples."""
    print("=================================================================")
    print("  CARELYNX Cross-Platform Environment Setup")
    print(f"  Operating System: {platform.system()} ({platform.machine()})")
    print(f"  Root Directory:   {REPO_ROOT}")
    print("=================================================================")

    # 1. Setup Python Virtual Environment in apps/api
    venv_dir = API_DIR / ".venv"
    if not venv_dir.exists():
        print("\n[1/5] Creating Python virtual environment in apps/api/.venv...")
        res = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], cwd=API_DIR)
        if res.returncode != 0:
            print("ERROR: Failed to create virtual environment.")
            return res.returncode
    else:
        print("\n[1/5] Python virtual environment already exists at apps/api/.venv.")

    py_bin = get_venv_python()

    # 2. Install Python Dependencies
    print("\n[2/5] Installing Python dependencies (FastAPI, SQLAlchemy, Alembic, etc.)...")
    req_file = API_DIR / "requirements.txt"
    if req_file.exists():
        res = subprocess.run([str(py_bin), "-m", "pip", "install", "--upgrade", "pip"], cwd=API_DIR)
        res = subprocess.run([str(py_bin), "-m", "pip", "install", "-r", "requirements.txt"], cwd=API_DIR)
        if res.returncode != 0:
            print("ERROR: Failed to install Python dependencies.")
            return res.returncode
    
    req_dev_file = API_DIR / "requirements-dev.txt"
    if req_dev_file.exists():
        subprocess.run([str(py_bin), "-m", "pip", "install", "-r", "requirements-dev.txt"], cwd=API_DIR)

    # 3. Run Database Migrations
    print("\n[3/5] Running Alembic database migrations...")
    alembic_bin = get_venv_bin("alembic")
    res = subprocess.run([str(alembic_bin), "upgrade", "head"], cwd=API_DIR)
    if res.returncode != 0:
        # Fallback to python -m alembic
        res = subprocess.run([str(py_bin), "-m", "alembic", "upgrade", "head"], cwd=API_DIR)
        if res.returncode != 0:
            print("WARNING: Alembic migration reported non-zero returncode. DB engine will create tables on startup if missing.")

    # 4. Install Node.js Frontend Dependencies
    print("\n[4/5] Installing Node.js frontend dependencies (Next.js, React, Tailwind)...")
    npm_cmd = get_npm_cmd()
    if (WEB_DIR / "package.json").exists():
        res = subprocess.run([npm_cmd, "install"], cwd=WEB_DIR)
        if res.returncode != 0:
            print("WARNING: npm install encountered an issue. Ensure Node.js (>= 18) and npm are installed.")

    # 5. Generate Sample Discharge PDFs
    print("\n[5/5] Generating sample medical discharge PDFs for instant testing...")
    sample_gen = REPO_ROOT / "generate_sample_pdf.py"
    if sample_gen.exists():
        subprocess.run([str(py_bin), str(sample_gen)], cwd=REPO_ROOT)

    print("\n=================================================================")
    print("  Setup Complete! You can now start the application with:")
    print("    python run.py dev")
    print("=================================================================\n")
    return 0


def run_api() -> int:
    """Run the FastAPI backend server."""
    py_bin = get_venv_python()
    uvicorn_bin = get_venv_bin("uvicorn")
    
    print(f"Starting CARELYNX FastAPI backend on http://0.0.0.0:8000 ...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # Try uvicorn executable, or fallback to python -m uvicorn
    cmd = [
        str(py_bin), "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    try:
        return subprocess.run(cmd, cwd=API_DIR, env=env).returncode
    except KeyboardInterrupt:
        return 0


def run_web() -> int:
    """Run the Next.js frontend development server."""
    npm_cmd = get_npm_cmd()
    print(f"Starting CARELYNX Next.js frontend on http://localhost:3000 ...")
    cmd = [npm_cmd, "run", "dev", "--", "-H", "0.0.0.0"]
    try:
        return subprocess.run(cmd, cwd=WEB_DIR).returncode
    except KeyboardInterrupt:
        return 0


def run_dev() -> int:
    """Run both API backend and Next.js frontend concurrently with unified logging and graceful shutdown."""
    py_bin = get_venv_python()
    npm_cmd = get_npm_cmd()

    print("=================================================================")
    print("  Starting CARELYNX Full-Stack System (Cross-Platform Dev)")
    print("  Backend API:  http://localhost:8000  (Docs: /docs, /api/v1/health)")
    print("  Web Portal:   http://localhost:3000  (Patient & Reviewer Views)")
    print("  Press CTRL+C anytime to cleanly shut down both servers.")
    print("=================================================================\n")

    api_cmd = [
        str(py_bin), "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    web_cmd = [npm_cmd, "run", "dev", "--", "-H", "0.0.0.0"]

    api_env = os.environ.copy()
    api_env["PYTHONUNBUFFERED"] = "1"

    # Cyan for API, Green for Web
    API_COLOR = "\033[96m" if not IS_WINDOWS or "WT_SESSION" in os.environ else ""
    WEB_COLOR = "\033[92m" if not IS_WINDOWS or "WT_SESSION" in os.environ else ""

    p_api = subprocess.Popen(
        api_cmd,
        cwd=API_DIR,
        env=api_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    p_web = subprocess.Popen(
        web_cmd,
        cwd=WEB_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    t_api = threading.Thread(target=stream_output, args=(p_api, "API:8000", API_COLOR), daemon=True)
    t_web = threading.Thread(target=stream_output, args=(p_web, "WEB:3000", WEB_COLOR), daemon=True)

    t_api.start()
    t_web.start()

    stop_requested = threading.Event()

    def handle_sigint(signum, frame):
        stop_requested.set()

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        while not stop_requested.is_set():
            if p_api.poll() is not None:
                print(f"\nAPI process exited with code {p_api.returncode}")
                break
            if p_web.poll() is not None:
                print(f"\nWeb process exited with code {p_web.returncode}")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down CARELYNX services...")
        for p in (p_api, p_web):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("All CARELYNX services stopped cleanly.")

    return 0


def run_tests() -> int:
    """Run backend tests using pytest."""
    py_bin = get_venv_python()
    pytest_bin = get_venv_bin("pytest")
    print("Running CARELYNX backend tests...")
    cmd = [str(py_bin), "-m", "pytest", "tests", "-v"]
    return subprocess.run(cmd, cwd=API_DIR).returncode


def generate_samples() -> int:
    """Generate sample PDF files."""
    py_bin = get_venv_python()
    script = REPO_ROOT / "generate_sample_pdf.py"
    return subprocess.run([str(py_bin), str(script)], cwd=REPO_ROOT).returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="CARELYNX Cross-Platform CLI Runner")
    parser.add_argument(
        "command",
        choices=["dev", "api", "web", "setup", "test", "generate-samples"],
        nargs="?",
        default="dev",
        help="Command to run (default: dev)",
    )
    args = parser.parse_args()

    if args.command == "setup":
        sys.exit(run_setup())
    elif args.command == "api":
        sys.exit(run_api())
    elif args.command == "web":
        sys.exit(run_web())
    elif args.command == "dev":
        sys.exit(run_dev())
    elif args.command == "test":
        sys.exit(run_tests())
    elif args.command == "generate-samples":
        sys.exit(generate_samples())


if __name__ == "__main__":
    main()
