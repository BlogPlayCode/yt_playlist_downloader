import os
import sys
import platform

## CONSTANTS
MAX_THREADS = 8
GIT_LINK = "https://github.com/BlogPlayCode/yt_playlist_downloader"
DONATE_URL = "https://t.me/NktBlgv"
ALLOWED_BROWSERS = ['brave', 'chrome', 'chromium', 'edge', 'firefox', 'opera', 'safari', 'vivaldi', 'whale']

## DEFAULTS
DEFAULT_OUTPUT_DIR = "result"
COOKIES = None

## ENVIRON
IS_MOBILE = False
if hasattr(sys, "getandroidapilevel"):
    IS_MOBILE = True
if any(x in os.environ.keys() for x in ("ANDROID_DATA", "ANDROID_ROOT", "TERMUX_VERSION")):
    IS_MOBILE = True
if "android" in platform.release().lower():
    IS_MOBILE = True

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
  -h, --help                        Show this help message and exit
  -s, --single-input                Process only a single input and exit
  -nc, --no-checks                  Skip version and connection checks on startup
  -o [DIR], --output [DIR]          Specify output directory (default: ./output)
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
