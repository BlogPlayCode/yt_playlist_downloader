@echo off
setlocal EnableDelayedExpansion

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo "Requesting admin..."
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo "[SCRIPT] Removing current virtual environ"
rd /s /q "./venv" >nul 2>nul
rd /s /q "./python" >nul 2>nul

echo "[SCRIPT] Checking python path"
set PY=python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo "Python is installed"
    echo "[SCRIPT] Building venv"
    python -m venv venv
    if %errorlevel% equ 0 (
        set PY=venv\Scripts\python.exe
        echo "Python venv was built successfully"
    ) else (
        echo "Error: Python venv building failed"
        pause
        exit /b 1
    )
) else (
    echo "Python not found"
    if not exist "python-embed.zip" (
        echo "Downloading python..."
        curl -L "https://www.python.org/ftp/python/3.13.11/python-3.13.11-embed-amd64.zip" -o "python-embed.zip"
    ) else (
        echo "python-embed.zip found locally"
    )
    if exist "python-embed.zip" (
        mkdir python 2> nul
        powershell -Command "Expand-Archive -Path 'python-embed.zip' -DestinationPath './python' -Force"
        set PY=python\python.exe
        curl -L "https://bootstrap.pypa.io/get-pip.py" -o "python\get-pip.py"
        if exist "python\get-pip.py" (
            echo "get-pip.py downloaded"
        ) else (
            echo "Error: get-pip download failed"
            pause
            exit /b 1
        )
        echo "Getting pip..."
        !PY! python\get-pip.py
        echo "get-pip executed"
        powershell -Command "(gc python\python3*._pth) -replace '#import site', 'import site' | Out-File python\python3*._pth -Encoding ASCII"
        set "CMD_OUTPUT="
        for /f "delims=" %%a in ('!PY! -m pip --version 2^>nul') do set "CMD_OUTPUT=%%a"
        echo "!CMD_OUTPUT!" | findstr /c:"pip" | findstr /c:"from" | findstr /c:"site-packages\pip" >nul
        if !errorlevel! equ 0 (
            echo "Python embedable + pip installed successfully"
        ) else (
            echo "Error: Python embedable + pip installation failed"
            pause
            exit /b 1
        )
        del python-embed.zip
    ) else (
        echo "Error: python download failed"
        pause
        exit /b 1
    )
)

echo "[SCRIPT] Installing requirements to pip"
!PY! -m pip install -r requirements.txt -U --no-warn-script-location

echo "[SCRIPT] Checking if ffmpeg is installed"
where /q ffmpeg
if %errorlevel% equ 0 (
    echo "FFmpeg is installed"
    pause
    exit /b 0
)

echo "FFmpeg not found"
if not exist "ffmpeg.7z" (
    echo "Starting FFmpeg installation..."
    curl -L "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z" -o "ffmpeg.7z"
) else (
    for /f "delims=" %%a in ('curl.exe -s -L "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z.sha256"') do (
        set "right_sha256=%%a"
    )
    if not defined right_sha256 (
        echo "Unable to fetch right ffmpeg.7z hash"
        pause
        exit /b 1
    )
    echo "right_sha256"
    echo "%right_sha256%"
    echo " "
    for /f "tokens=* skip=1" %%a in ('certutil -hashfile "ffmpeg.7z" SHA256') do (
        if not defined filehash (
            set "filehash=%%a"
        )
    )
    if not defined filehash (
        echo "Unable to calculate current ffmpeg.7z hash"
        pause
        exit /b 1
    )
    set "filehash=%filehash: =%"
    echo "filehash"
    echo "%filehash%"
    echo " "
    if "%filehash%" neq "%right_sha256%" (
        echo "Right ffmpeg.7z hash does not match current"
        del ffmpeg.7z
        echo "Starting FFmpeg installation..."
        curl -L "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z" -o "ffmpeg.7z"
    ) else (
        echo "ffmpeg.7z hash is correct, download is not required"
    )
)
if exist "ffmpeg.7z" (
    echo "FFmpeg archive downloaded, unpacking..."
    mkdir C:\ffmpeg
    if not exist "7zr.exe" (
        echo "Downloading 7-Zip console executable..."
        curl -L "https://www.7-zip.org/a/7zr.exe" -o "7zr.exe"
        if exist "7zr.exe" (
            echo "7-Zip console executable downloaded successfully"
        ) else (
            echo "Error: 7-Zip console executable download failed"
            pause
            exit /b 1
        )
    ) else (
        echo "7zr.exe found locally"
    )
    7zr.exe x "ffmpeg.7z" -oC:\ffmpeg -y
    for /d %%i in ("C:\ffmpeg\ffmpeg-*") do (
        xcopy "%%i\*" "C:\ffmpeg\" /E /H /Y /Q
        rd /S /Q "%%i"
    )
) else (
    echo "Error: FFmpeg archive download failed"
    pause
    exit /b 1
)
@REM del ffmpeg.7z
@REM del 7zr.exe
set FFMPEGPATH=C:\ffmpeg\bin

echo "Adding %FFMPEGPATH% into system PATH..."
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYSTEM_PATH=%%B"
if not defined SYSTEM_PATH (
    echo "Error: Cannot read system PATH from registry."
    echo "Add %FFMPEGPATH% manually."
    goto :after_path
)

set "CHECKPATH=;!SYSTEM_PATH!;"
echo !CHECKPATH! | findstr /I /C:";!FFMPEGPATH!;" >nul
if !errorlevel! equ 0 (
    echo "%FFMPEGPATH% is already in system PATH."
) else (
    echo "%FFMPEGPATH% not found in system PATH, adding..."
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "!SYSTEM_PATH!;%FFMPEGPATH%" /f >nul 2>&1
    if !errorlevel! equ 0 (
        echo "%FFMPEGPATH% successfully added to system PATH."
        echo "Restart cmd or computer for changes to take effect."
    ) else (
        echo "Error: Failed to add to registry (errorlevel !errorlevel!)."
        echo "Add %FFMPEGPATH% to PATH manually."
    )
)

:after_path

set "PATH=%PATH%;%FFMPEGPATH%"

where /q ffmpeg
if %errorlevel% equ 0 (
    echo "FFmpeg successfully installed to %FFMPEGPATH%"
) else (
    echo "Warning: FFmpeg still not found in PATH."
    echo "You may need to:"
    echo "1. Run the script as Administrator"
    echo "2. Restart your computer / open new cmd window"
    echo "3. Install FFmpeg and add it to PATH by yourself"
)

pause
exit /b 0
