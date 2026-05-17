import os
import cfg
import sys
import time
import logging
import requests
import subprocess
from main import Context, main


def version_check() -> tuple[bool, str, str]:
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
        url = cfg.GIT_LINK.strip('/').replace("://github.com/", "://raw.githubusercontent.com/")
        url += "/refs/heads/main/.version"
        resp = requests.get(url, timeout=5)
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
        if current == [-1]:
            current = None
        else:
            current = f"v{'.'.join([str(v) for v in current])}"
        return False, current, None

    latest = [v for v in latest.split('.') if v]
    try:
        latest = list(map(int, latest))
    except:
        latest = []
    if not latest:
        print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("    FAILED TO FETCH LATEST VERSION  ")
        print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if current == [-1]:
            current = None
        else:
            current = f"v{'.'.join([str(v) for v in current])}"
        return False, current, None
    
    for i in range(max(len(current), len(latest))):
        c = current[i] if i < len(current) else 0
        l = latest[i]  if i < len(latest)  else 0
        
        if l > c:
            print("  !!!!!!!!!!!!!!!!!!!!!")
            print("    NEW VERSION FOUND  ")
            print("  !!!!!!!!!!!!!!!!!!!!!")
            print(f"Found better version v{'.'.join(map(str, latest))}")
            print(f"Update via update script or here: {cfg.GIT_LINK}")
            print()
            if current == [-1]:
                current = None
            else:
                current = f"v{'.'.join([str(v) for v in current])}"
            latest = f"v{'.'.join([str(v) for v in latest])}"
            return True, current, latest
        elif l < c:
            print(f"Program version is newer (local v{'.'.join(map(str, current))} > latest v{'.'.join(map(str, latest))})")
            break
    else:
        print(f"Program is up to date (v{'.'.join(map(str, latest))})")
    if current == [-1]:
        current = None
    else:
        current = f"v{'.'.join([str(v) for v in current])}"
    latest = f"v{'.'.join([str(v) for v in latest])}"
    return False, current, latest

def connection_check():
    import requests
    print("Checking connection...", end=" ")
    try:
        res = requests.get("https://www.youtube.com", timeout=5)
        res.raise_for_status()
        print("OK")
    except Exception as e:
        print("BAD")
        print(cfg.BAD_CONNECTION_MESSAGE)

def cookies_check(context: Context):
    if not any(context.cookies.lower().startswith(x) for x in cfg.ALLOWED_BROWSERS):
        print("Browser for cookies not recognized! Disabling cookies")
        context.cookies = None
    else:
        print(f"Using cookies from {context.cookies}")


def cli():
    if any(x in sys.argv for x in ("-h", "--help", "help")):
        print(cfg.HELP_MESSAGE)
        sys.exit(0)
    
    context = Context()
    context.single_input = any(x in sys.argv for x in ("-s", "--single-input", "--singleinput"))
    context.launch_checks = not any(x in sys.argv for x in ("-nc", "--no-checks", "--nocheks", "--nochek", "--nochecks"))
    context.output = cfg.DEFAULT_OUTPUT_DIR
    arg = [x for x in ("-o", "--output", "--output-dir", "--outputdir") if x in sys.argv]
    if arg:
        arg = arg[0]
        try:
            output_index = sys.argv.index(arg)
            if output_index < len(sys.argv) - 1:
                context.output = sys.argv[output_index + 1]
        except:
            pass
    context.cookies = cfg.COOKIES
    arg = [x for x in ("-c", "--cookies") if x in sys.argv]
    if arg:
        arg = arg[0]
        try:
            cookies_index = sys.argv.index(arg)
            if cookies_index < len(sys.argv) - 1:
                context.cookies = sys.argv[cookies_index + 1]
        except:
            pass

    print(cfg.LOGO)
    if context.launch_checks:
        version_check()
        connection_check()
        if context.cookies:
            cookies_check(context)
        print()
    print(f"Output directory: {os.path.abspath(context.output)}")
    print("Type help for more information")
    inp = ""
    try:
        while not inp:
            inp = input("Enter URL or entry: \n> ").strip()
            if context.single_input:
                break
    except:
        sys.exit(1)
    os.makedirs("logs", exist_ok=True)
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
        while True:
            main(inp, context)
            if context.single_input:
                break
            inp = ""
            try:
                while not inp:
                    inp = input("Enter URL or entry: \n> ").strip()
            except:
                sys.exit(1)
    finally:
        print(f"Logs were saved to {log_file}")


if __name__ == "__main__":
    try:
        subprocess.run(
            "ffmpeg -L",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except:
        print("FFmpeg not found!", file=sys.stderr)
        sys.exit(1)

    cli()
