import os
import requests
import tempfile
import random
import time
import sys
import select
from .settings_handler import get_current_size, get_slideshow_timer

SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp"}
SUPPORTED_GIF_FORMATS = {"gif"}
SUPPORTED_VIDEO_FORMATS = {"mp4", "webm", "mkv"}  

def display_result(url: str):
    if not url:
        print("No URL provided.")
        return

    ext = _get_extension(url)

    if ext in SUPPORTED_IMAGE_FORMATS:
        _handle_image(url, ext)
    elif ext in SUPPORTED_GIF_FORMATS:
        _handle_gif(url, ext)
    elif ext in SUPPORTED_VIDEO_FORMATS:
        _handle_video(url, ext)
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
    try:
        response = requests.get(url, timeout=10)
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

def _handle_image(url: str, ext: str):
    path = _download_to_temp(url, ext)
    if not path:
        return

    size = get_current_size()

    if not size or size.lower() == "fill":
        # No size → use chafa defaults
        os.system(f"chafa {path}")
    else:
        # Size provided → pass it to chafa
        os.system(f"chafa --size={size} {path}")

    _cleanup(path)

def _handle_gif(url: str, ext: str):
    path = _download_to_temp(url, ext)
    if not path:
        return

    size = get_current_size()

    if not size or size.lower() == "fill":
        # No size → use chafa defaults
        os.system(f"chafa {path}")
    else:
        # Size provided → pass it to chafa
        os.system(f"chafa --size={size} {path}")

    _cleanup(path)

def _handle_video(url: str, ext: str):
    print("Video support not implemented yet.")
    # Later: use mpv + chafa pipe
    # os.system(f"mpv --vo=tct {path}")

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


