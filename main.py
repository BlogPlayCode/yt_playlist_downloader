import re
import os
import sys
import time
import yt_dlp
import logging
from threading import Thread


MAX_THREADS = 16


def save_to_file(content: str, filename: str = 'input.txt'):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("""
# audio ; http://link.com ; song file name
# video ; https://link.com ; video file name


""")
        f.write(content)


def clean_filename(filename, replacement="-"):
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


def get_playlist(url: str):
    url = url.strip()
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    num = 0
    result = ""
    amount = len([i for i in info.get('entries', []) if i.get('url')])
    for entry in info.get('entries', []):
        title = entry.get('title', 'Untitled')
        vid_url = entry.get('url', '')
        if vid_url:
            num += 1
            ftype = "audio" if "music.youtube.com" in vid_url else "video"
            zeros = len(str(amount)) - len(str(num))
            title = f"{'0'*zeros}{num}.{title}"
            result += f"{ftype} ; {vid_url} ; {title}\n"
    
    return result


def download_item(item: dict) -> None:
    fn = clean_filename(item['filename'])
    opts = {
        'outtmpl': "result/" + fn + '.%(ext)s',
    }
    if item['type'] == 'audio':
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }
        ]
    else:  # video
        opts['format'] = 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]'
        opts['remuxvideo'] = 'mp4'

    logging.info(f"Downloading '{fn}'...")

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([item['url']])
        logging.info(f"Download complete '{fn}'")
    except Exception as e:
        logging.error(f"Download {item['filename']} failed")
        logging.error(f"{type(e)} - {e}")


def manage_threads(items: list[dict]) -> None:
    items = items.copy()
    threads = []
    while threads or items:
        remove_finished_threads(threads)
        for item in items.copy():
            if len(threads) < MAX_THREADS:
                threads.append(Thread(target=download_item, args=(item,)))
                threads[-1].start()
                items.remove(item)
        time.sleep(1)


def main():
    # with open('input.txt') as f:
    #     lines = f.readlines()
    inp = input("Enter URL or entry: \n> ").strip()
    if "/playlist" not in inp:
        logging.warning("Not a playlist URL")
        try:
            items = parse_items(inp.split("\n"))
            if not items:
                raise ValueError("Can not parse any items")
            download_item(items[0])
        except Exception as e:
            logging.debug(f"{type(e)} - {e}")
            logging.error("Invalid input")
            print("""
Expected youtube playlist url or single entry. Example:

https://youtube.com/playlist?list=example
or
audio ; https://music.youtube.com/watch?v=example ; song file name
or
video ; https://youtube.com/watch?v=example ; video file name
""")
        return

    url = inp
    lines = get_playlist(url).split("\n")
    logging.info(f"Read {len(lines)} lines")

    items = parse_items(lines)
    logging.info(f"Parsed {len(items)} items")
    
    beginning = time.time()
    manage_threads(items)
    for f in os.listdir("result"):
        if len(f) <= 4 or (f[-4:] != ".mp4" and f[-4:] != ".mp3"):
            os.remove(os.path.join("result", f))

    for i in range(4):
        new_files = [
            f for f in os.listdir("result")
            if os.path.getmtime(os.path.join("result", f)) > beginning
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
            download_item(item)


if __name__ == "__main__":
    log_file = f"logs/log_{int(time.time()*1000)}.txt"
    os.makedirs("logs", exist_ok=True)
    os.makedirs("result", exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Вывод в stdout
            logging.FileHandler(log_file, encoding="utf-8")       # Запись в файл
        ],
    )
    main()
    print(f"Logs were saved to {log_file}")
