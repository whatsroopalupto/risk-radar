@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py --monitor --ais
) else (
  python run.py --monitor --ais
)
if errorlevel 1 pause
