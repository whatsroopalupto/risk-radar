"""Start the API and dashboard together, then open the browser."""
from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
API_URL = "http://127.0.0.1:8000"
DASH_URL = "http://127.0.0.1:8501"


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_for(url: str, attempts: int = 40) -> None:
    for _ in range(attempts):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise SystemExit(f"Timed out waiting for {url}")


def python_exe() -> str:
    if PYTHON.exists():
        return str(PYTHON)
    return sys.executable


def main() -> None:
    py = python_exe()
    backend: subprocess.Popen[bytes] | None = None

    if port_in_use(8000):
        print("Backend already running on port 8000.")
    else:
        backend = subprocess.Popen(
            [py, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(ROOT / "backend"),
        )
        print("Started backend at", API_URL)

    wait_for(f"{API_URL}/api/health")

    if port_in_use(8501):
        print("Dashboard already running. Opening browser.")
        webbrowser.open(DASH_URL)
        if backend is not None:
            print("Backend is running. Close this window to stop it.")
            try:
                backend.wait()
            except KeyboardInterrupt:
                backend.terminate()
        return

    dashboard = subprocess.Popen(
        [
            py,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            "8501",
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(ROOT / "dashboard"),
        stdin=subprocess.DEVNULL,
    )
    try:
        wait_for(DASH_URL)
        webbrowser.open(DASH_URL)
        print("Dashboard:", DASH_URL)
        dashboard.wait()
    except KeyboardInterrupt:
        pass
    finally:
        dashboard.terminate()
        if backend is not None:
            backend.terminate()


if __name__ == "__main__":
    main()
