@echo off
if exist "python\python.exe" (
    python\python.exe auto_update.py
) else (
    venv\Scripts\python.exe auto_update.py
)
