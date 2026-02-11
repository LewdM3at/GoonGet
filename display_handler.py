import os
import pty
import sys
import termios
import tty
import subprocess
import requests
import tempfile
#import shutil

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

    os.system(f"chafa {path}")

    _cleanup(path)

def _handle_gif(url: str, ext: str):
    path = _download_to_temp(url, ext)
    if not path:
        return

    os.system(f"chafa {path}")

    _cleanup(path)




def _handle_video(url: str, ext: str):
    """Placeholder for future video support."""
    print("Video support not implemented yet.")
    # Later: use mpv + chafa pipe
    # os.system(f"mpv --vo=tct {path}")

def _cleanup(path: str):
    try:
        os.remove(path)
    except Exception:
        pass
