## cli auto updater
import os
import time
import zipfile
import requests as rq
from main import version_check, git_link


zip_path = "./update.zip"


def main():
    need_update = version_check()
    print()
    if not need_update:
        print("[WARNING] Program is up to date, no update needed")
        print("[WARNING] You still can install latest version to replace files in this installation")

    answer = input("Install update? (type Y/n) \n> ").lower().strip()
    if not answer or answer[0] != 'y':
        return

    url = f"{git_link.strip('/')}/archive/refs/heads/main.zip"
    try:
        print("[UPDATER] Downloading update...")
        resp = rq.get(url, stream=True, allow_redirects=True)
        resp.raise_for_status()
        total = int(resp.headers.get('content-length', 0))

        with open(zip_path, "wb") as f:
            downloaded = 0
            for chunk in resp.iter_content(chunk_size=1024*16):
                if chunk:
                    downloaded += len(chunk)
                    print(
                        f"\r[UPDATER] Downloading {downloaded}",
                        end="",
                    )
                    if total > 0:
                        print(
                            f"/{total} ({int(downloaded/total*100)}%)",
                            end="",
                            flush=True,
                        )
                    f.write(chunk)
        print()
        print("[UPDATER] Download complete")
        
        print("[UPDATER] Installing update...")
        try:
            start_folder = None
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                for file in files:
                    if start_folder is None:
                        start_folder = file
                        continue
                    if start_folder is not None:
                        dest = file.removeprefix(start_folder)
                    print(
                        f"[EXTRACTOR] Extracting {file}",
                        flush=True,
                    )
                    zip_ref.extract(file, "./")
                    if os.path.isdir(file):
                        os.makedirs(dest, exist_ok=True)
                    else:
                        os.replace(file, dest)
                    time.sleep(0.1)
            os.rmdir(start_folder)
            
            print(f"[UPDATER] Successfully installed")
        except zipfile.BadZipFile:
            print(f"[EXTRACTOR] Error: {zip_path} is not a valid ZIP file")
            raise
        except Exception as e:
            print(f"Error extracting ZIP: {e}")
            raise

    except Exception as e:
        print(f"Update download error: {e}")
        input()
        return
    input("[UPDATER] Done. Press Enter to exit")


if __name__ == "__main__":
    main()
