import os
import requests
import tempfile
import random
import time
import sys
import select
import shutil
import subprocess
from .settings_handler import get_current_size, get_slideshow_timer, get_source, get_show_source_links

SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp"}
SUPPORTED_GIF_FORMATS = {"gif"}
SUPPORTED_VIDEO_FORMATS = {"mp4", "webm", "mkv"}  

def display_result(urls):
    if not urls:
        print("No URLs provided.")
        return

    file_url = urls["file_url"]
    source_url = urls["source_url"]
    ext = _get_extension(file_url)
    show_src_links = get_show_source_links()

    if ext in SUPPORTED_IMAGE_FORMATS:
        _handle_image(file_url, source_url, ext, show_src_links)
    elif ext in SUPPORTED_GIF_FORMATS:
        _handle_gif(file_url, source_url, ext, show_src_links)
    elif ext in SUPPORTED_VIDEO_FORMATS:
        _handle_video(file_url, source_url, ext, show_src_links)
    else:
        print(f"Unsupported file type: .{ext}")

def display_slideshow(urls: list[str]):
    timer = get_slideshow_timer()
    if not urls:
        print("No non-GIF images found.")
        return

    while True:
        random.shuffle(urls)
        print("Slideshow mode! Stop by pressing Enter!")
        time.sleep(2)
        for url in urls:
            _clear_screen()
            display_result(url)
            # Wait for timer OR keypress 
            if _wait_or_keypress(timer): 
                print("Slideshow stopped.") 
                return


def _get_extension(url: str) -> str:
    return url.split(".")[-1].lower().split("?")[0]

def _download_to_temp(url: str, ext: str) -> str | None:
    source = get_source()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://gelbooru.com/"
    }

    try:
        if source == "rule34.xxx":
            response = requests.get(url, timeout=10)
        if source == "gelbooru.com":
            response = requests.get(url, headers=headers, timeout=10)
            
        if response.status_code != 200:
            print("Failed to download file.")
            return None
    except Exception as e:
        print(f"Download error: {e}")
        return None

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(response.content)
    tmp.close()

    return tmp.name

def _handle_image(file_url: str, source_url: str, ext: str, show_src_links: bool):
    path = _download_to_temp(file_url, ext)
    if not path:
        return

    size = get_current_size()

    if not size or size.lower() == "fill":
        # No size → use chafa defaults
        #os.system(f"chafa {path}")
        subprocess.run(["chafa", path], stderr=subprocess.DEVNULL)
        if show_src_links == True:
            print("Source:", clickable(source_url))
    else:
        # Size provided → pass it to chafa
        #os.system(f"chafa --size={size} {path}")
        subprocess.run(["chafa", "--size=" + size, path], stderr=subprocess.DEVNULL)
        if show_src_links == True:
            print("Source: " + clickable(source_url))

    _cleanup(path)

def _handle_gif(file_url: str, source_url: str, ext: str, show_src_links: bool):
    path = _download_to_temp(file_url, ext)
    if not path:
        return

    size = get_current_size()

    if not size or size.lower() == "fill":
        # No size → use chafa defaults
        #os.system(f"chafa {path}")
        subprocess.run(["chafa", path], stderr=subprocess.DEVNULL)
        if show_src_links == True:
            print("Source: " + clickable(source_url))
    else:
        # Size provided → pass it to chafa
        #os.system(f"chafa --size={size} {path}")
        subprocess.run(["chafa", "--size=" + size, path], stderr=subprocess.DEVNULL)
        if show_src_links == True:
            print("Source: " + clickable(source_url))

    _cleanup(path)

def _handle_video(file_url: str, source_url: str, ext: str, show_src_links: bool):
    path = _download_to_temp(file_url, ext)
    if not path:
        return

    try:
        if shutil.which("mpv"):
            subprocess.run(["mpv", "--profile=sw-fast", "--vo=kitty", "--really-quiet", path], stderr=subprocess.DEVNULL)
        else:
            if shutil.which("xdg-open"):
                subprocess.run(["xdg-open", path], stderr=subprocess.DEVNULL)
            else:
                print("No suitable video player found. Install mpv or set a default via xdg-mime.")
    finally:
        _cleanup(path)


def _cleanup(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

def _clear_screen():
    print("\033[2J\033[H", flush=True)

def _wait_or_keypress(seconds: float) -> bool:
    r, _, _ = select.select([sys.stdin], [], [], seconds)
    if r:
        sys.stdin.read(1)  # consume key
        return True
    return False

def clickable(url, label=None):
    label = label or url
    return f"\033]8;;{url}\033\\{label}\033]8;;\033\\"



