@echo off
chcp 1251 >nul
setlocal EnableDelayedExpansion

set "APP_BAT=start.bat"
set "SHORTCUT_NAME=YT-Playlist-Downloader"
set "LOG_FILE=%~dp0install_log.txt"
set "ICON_FILE=%~dp0icon.ico"

echo "[%date% %time%] Starting shortcut creation script" > "%LOG_FILE%"

if not exist "%~dp0%APP_BAT%" (
    echo "ERROR: File %APP_BAT% not found in current folder" >> "%LOG_FILE%"
    echo "ERROR: File %APP_BAT% not found in current folder"
    pause
    exit /b 1
)

net session >nul 2>&1
if %errorlevel% equ 0 (
    set "IS_ADMIN=1"
    set "STARTMENU_DIR=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
    set "LOCATION=system-wide Start Menu (all users)"
) else (
    set "IS_ADMIN=0"
    set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
    set "LOCATION=current user Start Menu"
)

echo "Mode: !LOCATION!" >> "%LOG_FILE%"

set "DESKTOP_LNK=%USERPROFILE%\Desktop\!SHORTCUT_NAME!.lnk"
call :CreateShortcut "%~dp0%APP_BAT%" "!DESKTOP_LNK!" "Desktop"

if not exist "!STARTMENU_DIR!" (
    mkdir "!STARTMENU_DIR!" >nul 2>&1
)

set "STARTMENU_LNK=!STARTMENU_DIR!\!SHORTCUT_NAME!.lnk"
call :CreateShortcut "%~dp0%APP_BAT%" "!STARTMENU_LNK!" "!LOCATION!"

echo "----------------------------------" >> "%LOG_FILE%"
echo "Shortcut creation completed" >> "%LOG_FILE%"

echo.
echo   "Shortcuts have been created:"
echo   "On Desktop"
echo   "In Start Menu: !LOCATION!"
echo.
echo   "Details saved to: !LOG_FILE!"
echo.

if !IS_ADMIN! equ 0 (
    echo   "Note: To place the shortcut in the system-wide Start Menu"
    echo   "(visible to all users), run this script as Administrator."
    echo.
)

exit /b 0


:CreateShortcut
set "target=%~1"
set "lnk_path=%~2"
set "location=%~3"

set "target_esc=!target:\=\\!"
set "target_esc=!target_esc:'=''!"

set "lnk_path_esc=!lnk_path:\=\\!"
set "lnk_path_esc=!lnk_path_esc:'=''!"

set "ICON_ESC=!ICON_FILE:\=\\!"
set "ICON_ESC=!ICON_ESC:'=''!"

set "ps= $ws = New-Object -ComObject WScript.Shell; "
set "ps=!ps! $s = $ws.CreateShortcut('%lnk_path_esc%'); "
set "ps=!ps! $s.TargetPath = '%target_esc%'; "
set "ps=!ps! $s.WorkingDirectory = [System.IO.Path]::GetDirectoryName('%target_esc%'); "

if exist "%ICON_FILE%" (
    set "ps=!ps! $s.IconLocation = '%ICON_ESC%'; "
    echo "[INFO] Using icon: !ICON_FILE!" >> "%LOG_FILE%"
) else (
    echo "[WARNING] Icon file not found: !ICON_FILE!" >> "%LOG_FILE%"
)

set "ps=!ps! $s.Save(); "

powershell -NoProfile -ExecutionPolicy Bypass -Command "!ps!" >> "%LOG_FILE%" 2>&1

if exist "!lnk_path!" (
    echo "[SUCCESS] Shortcut created: !location!" >> "%LOG_FILE%"
) else (
    echo "[ERROR] Failed to create shortcut: !location!" >> "%LOG_FILE%"
    echo   "Target: !target!" >> "%LOG_FILE%"
    echo   "Link path: !lnk_path!" >> "%LOG_FILE%"
)

exit /b
