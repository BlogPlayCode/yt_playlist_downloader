# Youtube Playlist Downloader

---

### Quick start
1. Install [python 3.13](https://python.org/downloads/release/python-31311/) (should work on other versions but not tested)
2. Install ffmpeg and add it to PATH or do it automatically for windows 10+ [here](https://github.com/BlogPlayCode/ffmpeg-win-downloader/releases/download/2025-12-31-full_build-gyan.dev/ffmpeg-installer.exe)
3. Set up virtual environ:
```bash
python -m venv venv
```
4. Install dependencies:
Linux:
```bash
./venv/bin/activate
pip install -r requirements.txt
```
Windows:
```bash
.\venv\Scripts\activate.bat
pip install -r requirements.txt
```

5. Launch script: 
- Linux: `start.sh` 
- Windows: `start.bat`
or run `python main.py` command

---

### Functional
- type `help` in cli to get help
- for youtube music playlists auto save as audio
- for youtube music songs auto metadata + cover download
- for instagram reels names are set as reel-timestamp
- set `USE_COOKIES = True` in main.py for program to try to get cookies from firefox

---

### Troubleshooting
if firefox cookies extraction causes errors 
- try to download firefox
- try to update firefox
- try to close firefox before launching main.py
- or finaly set `USE_COOKIES = False` in main.py

