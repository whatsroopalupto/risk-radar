"""Start the API and dashboard together, then open the browser."""
from __future__ import annotations

import socket
import argparse
import shutil
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
DASH_URL = "http://127.0.0.1:5173"


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monitor", action="store_true", help="Poll news and trade every 15 minutes; may use Gemini quota")
    parser.add_argument("--ais", action="store_true", help="Start the optional AIS collector")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    py = python_exe()
    node = shutil.which("node")
    vite = ROOT / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"
    if not node or not vite.exists():
        raise SystemExit("Install Node.js, then run npm ci inside frontend before launching.")
    children = []
    try:
        if not port_in_use(8000):
            children.append(subprocess.Popen(
                [py, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=str(ROOT)))
        wait_for(f"{API_URL}/api/health")
        if not port_in_use(5173):
            children.append(subprocess.Popen(
                [node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
                cwd=str(ROOT / "frontend"), stdin=subprocess.DEVNULL))
        wait_for(DASH_URL)
        if args.monitor:
            children.append(subprocess.Popen([py, "-m", "backend.app.monitor"], cwd=str(ROOT)))
        if args.ais:
            children.append(subprocess.Popen([py, "-m", "backend.app.connectors.ais"], cwd=str(ROOT)))
        if not args.no_browser:
            webbrowser.open(DASH_URL)
        print("React dashboard:", DASH_URL, "\nPress Ctrl+C to stop services started by this launcher.")
        while children and any(child.poll() is None for child in children):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()


if __name__ == "__main__":
    main()
