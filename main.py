import re
import os
import sys
import time
import json
import yt_dlp
import logging
import tempfile
import requests
import subprocess
from pathlib import Path
from threading import Thread


MAX_THREADS = 8
USE_COOKIES = True
git_link = "https://github.com/BlogPlayCode/yt_playlist_downloader"


def save_to_file(content: str, filename: str = 'input.txt') -> None:
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("""
# audio ; http://link.com ; song %(title)s
# video ; https://link.com ; video %(title)s


""")
        f.write(content)


def clean_filename(filename: str, replacement="-") -> None:
    # / \ : * ? " < > | и управляющие символы 0-31
    forbidden_chars = r'[\\/:\*\?"<>|\x00-\x1f]'
    cleaned = re.sub(forbidden_chars, replacement, filename)
    reserved_names = {
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
        "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    name_part = os.path.splitext(cleaned)[0].upper()
    if name_part in reserved_names:
        cleaned = "file_" + cleaned
    cleaned = cleaned.strip(". ")

    return cleaned


def add_square_thumbnail_to_audio(audio_path: str, thumbnail_url: str) -> bool:
    audio_path = Path(audio_path).resolve()
    if not audio_path.is_file():
        logging.warning(f"[{audio_path}] File not found")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        temp_image = tmpdir / "thumb_original.jpg"
        temp_square = tmpdir / "thumb_square.jpg"

        try:
            resp = requests.get(
                thumbnail_url,
                timeout=12,
                stream=True,
                allow_redirects=True,
            )
            resp.raise_for_status()
            
            with open(temp_image, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
        except Exception as e:
            logging.warning(f"[{audio_path}] Thumbnail download error: {e}")
            return False

        cmd_crop = [
            "ffmpeg", "-y",
            "-loglevel", "quiet",
            "-i", str(temp_image),
            "-vf", r"crop=min(iw\,ih):min(iw\,ih):(iw-ow)/2:(ih-oh)/2",
            "-update", "1",
            str(temp_square)
        ]

        try:
            subprocess.run(
                cmd_crop,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            logging.warning(f"[{audio_path}] Image crop error: {e}")
            return False

        cmd_embed = [
            "ffmpeg", "-y",
            "-loglevel", "quiet",
            "-i", str(temp_square),
            "-i", str(audio_path),
            "-map", "0:v",
            "-map", "1:a",
            "-map_metadata", "1","-c", "copy",
            "-disposition:v", "attached_pic",
            "-metadata:s:v", "title=Cover",
            str(audio_path) + ".temp.mp3"
        ]

        try:
            subprocess.run(
                cmd_embed,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            
            os.replace(str(audio_path) + ".temp.mp3", audio_path)
            logging.info(f"[{audio_path}] Thumbnail was added successfully: {audio_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.warning(f"[{audio_path}] Thumbnail insert to audio file error: {e}")
            if (audio_path.with_suffix(".temp.mp3")).exists():
                (audio_path.with_suffix(".temp.mp3")).unlink()
            return False


def remove_finished_threads(threads: list[Thread]) -> list[Thread]:
    for thread in threads.copy():
        if not thread.is_alive():
            thread.join()
            threads.remove(thread)
    
    return threads


def parse_items(lines: list[str]) -> list[dict]:
    items = []
    for line in lines:
        line = line.strip()
        if not line or line[0] == "#":
            continue
        ftype, url, fname = line.split(';', 2)
        items.append({'type': ftype.strip(), 'filename': fname.strip(), 'url': url.strip()})
    
    return items


def get_playlist(url: str) -> str:
    url = url.strip()
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    import json
    with open("playlist.json", "w", encoding="utf-8") as f:
        json.dump(dict(info), f, indent=4)
    num = 0
    result = ""
    amount = len([i for i in info.get('entries', []) if i.get('url')])
    for entry in info.get('entries', []):
        # title = entry.get('title', 'Untitled')
        title = "%(title)s"
        vid_url = entry.get('url', '')
        if vid_url:
            num += 1
            ftype = "audio" if "music.youtube.com" in vid_url else "video"
            zeros = len(str(amount)) - len(str(num))
            title = f"{'0'*zeros}{num}.{title}"
            result += f"{ftype} ; {vid_url} ; {title}\n"
    
    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    name = info.get("title", f"Playlist-{now}")
    
    return name, result


def download_item(item: dict, catalogue: str = "") -> None:
    if "instagram.com/reel/" in item['filename']:
        item['filename'] = item['filename'].replace(
            "%(title)s", f"reel-{int(time.time()*1000)}"
        )
    fn = clean_filename(item['filename'])
    
    catalogue_processed = catalogue.strip('/\\').replace('\\', '/').split('/')[-1]
    if (
        catalogue_processed.startswith("Album - ")
        and catalogue_processed[8:].strip()
    ):
        catalogue_processed = catalogue_processed[8:].strip()
    
    opts = {
        'outtmpl': "result/" + catalogue + fn + '.%(ext)s',
        'noplaylist': True,
        # 'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'print-traffic': False,
        'retries': 1,
        'fragment_retries': 3,
        'concurrent_fragment_downloads': 4,
        'postprocessors': []
    }

    if USE_COOKIES:
        opts['cookiesfrombrowser'] = ('firefox',)

    is_audio = item['type'] == 'audio'

    if is_audio:
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'].append(
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }
        )
    else:    # video
        opts['format'] = 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]'
        opts['postprocessors'].append(
            {
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }
        )

    opts['postprocessors'].append({'key': 'FFmpegMetadata'})

    name_list = [None]
    def filename_hook(d):
        if d['status'] == 'finished' and name_list[0] is None:
            name_list[0] = d.get('info_dict', {}).get('_filename')
            if not name_list[0]:
                name_list[0] = d.get('filename', "Unknown.webm")

    opts['progress_hooks'] = [filename_hook]

    logging.info(f"Downloading '{fn}'...")

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            t1 = time.time()
            info = ydl.extract_info(item['url'], download=False)
            t1 = time.time()-t1
            with open(f"video_info.json", "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2)
            t2 = time.time()
            ydl.download(item['url'])
            t2 = time.time()-t2
            if not name_list[0]:
                name_list[0] = "Unknown.idk"
            final_filename = str(name_list[0].rsplit('.', 1)[0])
            final_filename += ".mp3" if is_audio else ".mp4"
            fn = final_filename.replace("\\", "/").split("/")[-1]
            logging.debug(f"[{fn}] Info extract time {t1}s")
            logging.debug(f"[{fn}] Downloading time {t2}s")
            if (
                is_audio 
                and "youtube.com/" in item['url'] 
                and "thumbnail" in info 
                and info["thumbnail"]
            ):
                logging.debug(f"[{fn}] Attaching thumbnail to audio {info["thumbnail"]}")
                add_square_thumbnail_to_audio(final_filename, info["thumbnail"])
            
        logging.info(f"Download complete '{final_filename}'")
    except Exception as e:
        logging.error(f"Download {item['filename']} ({item['url']}) failed")
        logging.error(f"{type(e)} - {e}")


def manage_threads(items: list[dict], catalogue:str = "") -> None:
    items = items.copy()
    threads = []
    while threads or items:
        remove_finished_threads(threads)
        for item in items.copy():
            if len(threads) < MAX_THREADS:
                threads.append(Thread(target=download_item, args=(item, catalogue, )))
                threads[-1].start()
                items.remove(item)
        time.sleep(1)


def main(inp):
    playlist = ""
    if inp == "file":
        with open('input.txt') as f:
            lines = f.readlines()
    elif inp.startswith("http") and "/playlist" in inp:
        name, lines = get_playlist(inp)
        lines = lines.split("\n")
        playlist = f"{name}/"
    else:
        if inp.startswith("http"):
            if "//music.youtube.com/" in inp:
                inp = f"audio ; {inp} ; %(title)s"
            else:
                inp = f"video ; {inp} ; %(title)s"

        try:
            items = parse_items(inp.split("\n"))
            if not items:
                raise ValueError("Can not parse any items")
            download_item(items[0])
        except Exception as e:
            logging.debug(f"{type(e)} - {e}")
            logging.error("Invalid input")
            print("""
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
""")
        return
    
    logging.info(f"Read {len(lines)} lines")

    items = parse_items(lines)
    logging.info(f"Parsed {len(items)} items")
    
    beginning = time.time()
    manage_threads(items, playlist)
    new_files = [
        f for f in os.listdir(f"result/{playlist}")
        if not os.path.isdir(f"result/{playlist}{f}")
        and os.path.getmtime(os.path.join(f"result/{playlist}", f)) > beginning
    ]
    for f in new_files:
        if (
            len(f) <= 4 
            or (
                f[-4:] != ".mp4" 
                and f[-4:] != ".mp3"
            ) 
            or f.endswith(".mp3.temp.mp3")
        ):
            os.remove(os.path.join(f"result/{playlist}", f))

    for i in range(4):
        new_files = [
            f for f in os.listdir(f"result/{playlist}")
            if not os.path.isdir(f"result/{playlist}{f}")
            and os.path.getmtime(os.path.join(f"result/{playlist}", f)) > beginning
        ]
        logging.info(f"Done {len(new_files)}/{len(items)}")
        if len(new_files) == len(items):
            return
        
        failed = []
        logging.info(f"Failed:")
        for item in items:
            for fn in new_files:
                if fn.split('.')[0] == item.get("filename", "").split('.')[0]:
                    break
            else:
                failed.append(item)
                logging.info(item.get("filename", "Unknown"))
        
        if i == 3:
            return

        logging.info(f"Retrying failed items ({i+1}/3):")

        for item in failed:
            download_item(item, playlist)


def version_check() -> bool:
    current = ""
    try:
        with open(".version", "r") as f:
            for l in str(f.read()):
                if l in ".0123456789":
                    current += l
    except:
        pass

    current = [v for v in current.split('.') if v]
    try:
        current = list(map(int, current))
    except:
        current = [-1]
    if not current:
        current = [-1]
    
    print(f"  v{'.'.join([str(v) for v in current])}")
    print()
    
    latest = ""
    try:
        url = git_link.strip('/').replace("://github.com/", "://raw.githubusercontent.com/")
        url += "/refs/heads/main/.version"
        resp = requests.get(url)
        if resp.status_code // 100 not in [2, 3]:
            raise ValueError()
        text = resp.text
        for l in text:
            if l in ".0123456789":
                latest += l
    except:
        print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("    FAILED TO FETCH LATEST VERSION  ")
        print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return False

    latest = [v for v in latest.split('.') if v]
    try:
        latest = list(map(int, latest))
    except:
        latest = [-1]
    if not latest:
        print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("    FAILED TO FETCH LATEST VERSION  ")
        print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return False
    
    for key in range(len(latest)):
        if key < len(current):
            if latest[key] > current[key]:
                break
    else:
        print(f"Program is up to date (latest v{'.'.join([str(v) for v in latest])})")
        return False
    
    print("  !!!!!!!!!!!!!!!!!!!!!")
    print("    NEW VERSION FOUND  ")
    print("  !!!!!!!!!!!!!!!!!!!!!")
    print(f"Found better version v{'.'.join([str(v) for v in latest])}")
    print(f"Update here: {git_link}")
    print()
    return True


if __name__ == "__main__":
    print("""
  ####     ####   ##   ##  ##  ##  ##      ####     ##    #####    ######  #####
  ## ##   ##  ##  ##   ##  ### ##  ##     ##  ##   ####   ##  ##   ##      ##  ##
  ##  ##  ##  ##  ##   ##  ######  ##     ##  ##  ##  ##  ##   ##  ##      ##  ##
  ##  ##  ##  ##  ## # ##  ######  ##     ##  ##  ######  ##   ##  ####    #####
  ##  ##  ##  ##  #######  ## ###  ##     ##  ##  ##  ##  ##   ##  ##      ####
  ## ##   ##  ##  ### ###  ##  ##  ##     ##  ##  ##  ##  ##  ##   ##      ## ##
  ####     ####   ##   ##  ##  ##  ######  ####   ##  ##  #####    ######  ##  ##
""")
    version_check()
    print()
    try:
        inp = input("Enter URL or entry: \n> ").strip()
    except:
        sys.exit(1)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("result", exist_ok=True)
    log_file = f"logs/log_{int(time.time()*1000)}.txt"
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    try:
        main(inp)
    finally:
        print(f"Logs were saved to {log_file}")
