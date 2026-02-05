@echo off
set PATH=%~dp0ffmpeg\bin;%PATH%
if exist "python\python.exe" (
    python\python.exe main.py
) else (
    venv\Scripts\python.exe main.py
)
pause
