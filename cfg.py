import os
import sys
import json
import platform

## CONSTANTS
MAX_THREADS = 8
GIT_LINK = "https://github.com/BlogPlayCode/yt_playlist_downloader"
DONATE_URL = "https://t.me/NktBlgv"
ALLOWED_BROWSERS = ['brave', 'chrome', 'chromium', 'edge', 'firefox', 'opera', 'safari', 'vivaldi', 'whale']
SETTINGS_FILE = "saved_settings.json"

## DEFAULTS
DEFAULT_OUTPUT_DIR = "result"  ## may be changed depending on the platform
COOKIES = None

## ENVIRON
IS_MOBILE = False
if hasattr(sys, "getandroidapilevel"):
    IS_MOBILE = True
if any(x in os.environ.keys() for x in ("ANDROID_DATA", "ANDROID_ROOT", "TERMUX_VERSION")):
    IS_MOBILE = True
if "android" in platform.release().lower():
    IS_MOBILE = True

if IS_MOBILE:
    try:
        test_dir = "/storage/emulated/0/Download"
        with open(os.path.join(test_dir, "test.mp3"), "wb") as f:
            f.write(b"test")
        test_dir = os.path.join(test_dir, "yt_playlist_downloader")
        os.makedirs(test_dir, exist_ok=True)
        DEFAULT_OUTPUT_DIR = test_dir
    except:
        test_dir = os.path.join(os.path.expanduser("~"), "Documents")
        with open(os.path.join(test_dir, "test.mp3"), "wb") as f:
            f.write(b"test")
        DEFAULT_OUTPUT_DIR = test_dir
    
## TEXTS
LOGO = """
  ####     ####   ##   ##  ##  ##  ##      ####     ##    #####    ######  #####
  ## ##   ##  ##  ##   ##  ### ##  ##     ##  ##   ####   ##  ##   ##      ##  ##
  ##  ##  ##  ##  ##   ##  ######  ##     ##  ##  ##  ##  ##   ##  ##      ##  ##
  ##  ##  ##  ##  ## # ##  ######  ##     ##  ##  ######  ##   ##  ####    #####
  ##  ##  ##  ##  #######  ## ###  ##     ##  ##  ##  ##  ##   ##  ##      ####
  ## ##   ##  ##  ### ###  ##  ##  ##     ##  ##  ##  ##  ##  ##   ##      ## ##
  ####     ####   ##   ##  ##  ##  ######  ####   ##  ##  #####    ######  ##  ##
"""
HELP_MESSAGE = """
Usage: python yt-playlist-downloader.py [options]
Options:
  -h,           --help              Show this help message and exit
  -r,           --reset-settings    Reset saved settings to defaults
  -s,           --single-input      Process only a single input and exit
  -nc,          --no-checks         Skip version and connection checks on startup
  -sv,          --save-settings     Save current settings to be used as defaults in the future
  -o [DIR],     --output [DIR]      Specify output directory (default: ./output)
  -c [BROWSER], --cookies [BROWSER] Use cookies from [BROWSER] in the current directory
""".strip("\n")
BAD_CONNECTION_MESSAGE = r"""
          /\
         /  \
        /    \
       /  !!  \
      /   !!   \
     /    !!    \
    /     !!     \
   /              \
  /       !!       \
 ====================
Connection is unstable, network errors may occur. Try to get stable connection or use restriction bypass tools
""".strip("\n")
INPUT_ERROR_MESSAGE = """
Expected youtube playlist/video/music url or single entry. Example:

https://youtube.com/playlist?list=example
or
https://youtube.com/watch?v=example
or
https://music.youtube.com/watch?v=example
or
audio ; https://music.youtube.com/watch?v=example ; song file name
or
video ; https://youtube.com/watch?v=example ; video file name
"""
