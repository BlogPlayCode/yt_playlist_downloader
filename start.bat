@echo off
set PATH=%~dp0ffmpeg\bin;%PATH%
if exist "python\python.exe" (
    python\python.exe yt-playlist-downloader.py
) else (
    venv\Scripts\python.exe yt-playlist-downloader.py
)
pause
