#!/bin/bash

set -e

echo "[SCRIPT] Removing current venv and portable ffmpeg (if exists)"
rm -rf ./venv ./ffmpeg

PM=""
if command -v apt >/dev/null 2>&1; then
    PM="apt"
    echo "Detected Debian/Ubuntu-based system (apt)"
elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
    echo "Detected Fedora (dnf)"
elif command -v yum >/dev/null 2>&1; then
    PM="yum"
    echo "Detected CentOS/RHEL older (yum)"
elif command -v pacman >/dev/null 2>&1; then
    PM="pacman"
    echo "Detected Arch Linux / Manjaro (pacman)"
elif command -v zypper >/dev/null 2>&1; then
    PM="zypper"
    echo "Detected openSUSE (zypper)"
elif command -v apk >/dev/null 2>&1; then
    PM="apk"
    echo "Detected Alpine Linux (apk)"
else
    echo "No supported package manager detected."
fi

echo "[SCRIPT] Checking Python3 with venv support"
if python3 --version >/dev/null 2>&1 && python3 -m venv --help >/dev/null 2>&1; then
    echo "Python3 with venv support is already installed"
else
    echo "Python3 or venv module not found. Attempting to install via package manager..."
    if [ -z "$PM" ]; then
        echo "Error: No supported package manager found."
        echo "Please install Python3 manually (with venv support)."
        echo "Common commands:"
        echo "  Debian/Ubuntu: sudo apt install python3 python3-venv"
        echo "  Fedora:        sudo dnf install python3 python3-venv"
        echo "  Arch:          sudo pacman -S python"
        echo "  openSUSE:      sudo zypper install python3 python3-venv"
        exit 1
    fi

    case $PM in
        apt)
            sudo apt update
            sudo apt install -y python3 python3-venv python3-pip
            ;;
        dnf)
            sudo dnf install -y python3 python3-venv
            ;;
        yum)
            sudo yum install -y python3 python3-venv
            ;;
        pacman)
            sudo pacman -S --noconfirm python
            ;;
        zypper)
            sudo zypper install -y python3 python311-venv
            ;;
        apk)
            sudo apk add python3 py3-pip
            ;;
    esac

    if ! python3 -m venv --help >/dev/null 2>&1; then
        echo "Error: Failed to install Python3 with venv support"
        exit 1
    fi
    echo "Python3 with venv support installed successfully"
fi

echo "[SCRIPT] Building venv"
python3 -m venv venv
echo "Virtual environment created"

echo "[SCRIPT] Upgrading pip and installing requirements"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
deactivate
echo "Requirements installed successfully"

echo "[SCRIPT] Checking if ffmpeg is installed"
if command -v ffmpeg >/dev/null 2>&1; then
    echo "FFmpeg is already installed"
else
    echo "FFmpeg not found. Attempting installation..."

    if [ -n "$PM" ]; then
        echo "Installing via package manager ($PM)..."
        case $PM in
            apt)
                sudo apt update
                sudo apt install -y ffmpeg
                ;;
            dnf)
                sudo dnf install -y ffmpeg
                ;;
            yum)
                sudo yum install -y ffmpeg
                ;;
            pacman)
                sudo pacman -S --noconfirm ffmpeg
                ;;
            zypper)
                sudo zypper install -y ffmpeg
                ;;
            apk)
                sudo apk add ffmpeg
                ;;
        esac
    else
        echo "No package manager detected. Downloading portable static build..."
        mkdir -p ffmpeg_temp
        cd ffmpeg_temp
        echo "Downloading latest git static build (amd64)..."
        curl -L -o ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
        if [ ! -f ffmpeg.tar.xz ]; then
            echo "Error: Failed to download FFmpeg archive"
            exit 1
        fi
        echo "Extracting..."
        tar -xJf ffmpeg.tar.xz
        mkdir -p ../ffmpeg
        for dir in ffmpeg-git-*-amd64-static; do
            if [ -d "$dir" ]; then
                mv "$dir"/* ../ffmpeg/
                break
            fi
        done
        chmod +x ../ffmpeg/ffmpeg ../ffmpeg/ffprobe ../ffmpeg/ffplay ../ffmpeg/qt-faststart 2>/dev/null || true
        cd ..
        rm -rf ffmpeg_temp
        export PATH="$(pwd)/ffmpeg:$PATH"
        echo "Portable FFmpeg installed in ./ffmpeg"
        echo "Added to PATH for current session."
        echo "To make it permanent, add the following line to your ~/.bashrc or ~/.zshrc:"
        echo "  export PATH=\"$(pwd)/ffmpeg:\$PATH\""
    fi

    if command -v ffmpeg >/dev/null 2>&1; then
        echo "FFmpeg successfully installed and available"
    else
        echo "Warning: FFmpeg still not found in PATH."
        echo "You may need to:"
        echo "  - Restart the terminal"
        echo "  - Log out and log in again (for system-wide install)"
        echo "  - Manually add ./ffmpeg to your PATH (for portable version)"
    fi
fi

echo ""
echo "Setup complete!"
echo "To run your project, use:"
echo "  source venv/bin/activate"
echo "  # your commands here"
echo "  deactivate"
read -p "Press Enter to exit..."
