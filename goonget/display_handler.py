import os
import requests
import tempfile
import random
import time
import sys
import select
import shutil
import subprocess
import atexit
from .settings_handler import get_current_size, get_slideshow_timer, get_source, get_show_source_links

SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp"}
SUPPORTED_GIF_FORMATS = {"gif"}
SUPPORTED_VIDEO_FORMATS = {"mp4", "webm", "mkv"}

# Exit code mpv returns when the user presses ENTER during slideshow playback
# (bound via a temp input.conf below). Distinct from q / natural end, which are 0.
_SLIDESHOW_STOP_CODE = 47

def display_result(urls, slideshow: bool = False) -> bool:
    """Display a single result. Returns True only if the user asked to stop the
    slideshow (ENTER pressed during a video); False otherwise."""
    if not urls:
        print("No URLs provided.")
        return False

    file_url = urls["file_url"]
    source_url = urls["source_url"]
    ext = _get_extension(file_url)
    show_src_links = get_show_source_links()

    if ext in SUPPORTED_IMAGE_FORMATS:
        _handle_image(file_url, source_url, ext, show_src_links)
    elif ext in SUPPORTED_GIF_FORMATS:
        _handle_gif(file_url, source_url, ext, show_src_links)
    elif ext in SUPPORTED_VIDEO_FORMATS:
        return _handle_video(file_url, source_url, ext, show_src_links, slideshow)
    else:
        print(f"Unsupported file type: .{ext}")
    return False

def display_slideshow(urls: list[str]):
    timer = get_slideshow_timer()
    if not urls:
        print("No non-GIF images found.")
        return

    print("Slideshow mode! Stop by pressing Enter!")
    time.sleep(2)
    try:
        while True:
            random.shuffle(urls)
            for url in urls:
                _clear_screen()
                is_video = _get_extension(url["file_url"]) in SUPPORTED_VIDEO_FORMATS
                # During a video, mpv owns stdin; ENTER is bound to quit-with-code
                # so display_result can report a stop request.
                if display_result(url, slideshow=True):
                    return
                # For images/gifs, wait out the timer (or stop on a keypress).
                # Videos already gave the user their viewing time + stop chance.
                if not is_video and _wait_or_keypress(timer):
                    return
    except KeyboardInterrupt:
        pass
    finally:
        _reset_terminal()
        print("Slideshow stopped.")


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

def _handle_video(file_url: str, source_url: str, ext: str, show_src_links: bool,
                  slideshow: bool = False) -> bool:
    path = _download_to_temp(file_url, ext)
    if not path:
        return False

    stop_requested = False
    try:
        if shutil.which("mpv"):
            cmd = ["mpv", "--profile=sw-fast", "--vo=kitty", "--really-quiet"]
            if slideshow:
                # Bind ENTER -> quit with our sentinel code so pressing ENTER
                # during playback stops the whole slideshow.
                cmd.append("--input-conf=" + _slideshow_input_conf())
            cmd.append(path)
            result = subprocess.run(cmd, stderr=subprocess.DEVNULL)
            if slideshow and result.returncode == _SLIDESHOW_STOP_CODE:
                stop_requested = True
        else:
            if shutil.which("xdg-open"):
                subprocess.run(["xdg-open", path], stderr=subprocess.DEVNULL)
            else:
                print("No suitable video player found. Install mpv or set a default via xdg-mime.")
    finally:
        # mpv enables mouse reporting / alt-screen / hides the cursor and draws
        # kitty-graphics frames. If it exited cleanly it restores all of that, but
        # an interrupted exit (Ctrl+C mashed, crash) leaks those modes into the
        # shell. Reset defensively so the terminal is always usable afterwards.
        _reset_terminal()
        _cleanup(path)
    return stop_requested


def _cleanup(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

def _clear_screen():
    # Use write() (not print, which appends a newline that pushes the next image
    # down a row). \033[3J clears scrollback and the kitty graphics-delete removes
    # any leftover frames so the next chafa image is not shifted/overlaid.
    sys.stdout.write("\033[3J\033[2J\033[H\033_Ga=d,d=A\033\\")
    sys.stdout.flush()

def _reset_terminal():
    sys.stdout.write(
        "\033[?1000l\033[?1002l\033[?1003l\033[?1006l\033[?1015l"  # disable mouse reporting
        "\033[?1049l"          # leave the alternate screen, if still in it
        "\033[?25h"            # show the cursor
        "\033_Ga=d,d=A\033\\"  # delete all kitty graphics images
    )
    sys.stdout.flush()

_mpv_input_conf = None

def _slideshow_input_conf() -> str:
    """Path to a small mpv input.conf binding ENTER to quit with our sentinel
    exit code. Created once and reused for the session."""
    global _mpv_input_conf
    if _mpv_input_conf and os.path.exists(_mpv_input_conf):
        return _mpv_input_conf
    f = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False)
    f.write(f"ENTER quit {_SLIDESHOW_STOP_CODE}\n")
    f.close()
    _mpv_input_conf = f.name
    atexit.register(lambda: _cleanup(_mpv_input_conf))
    return _mpv_input_conf

def _wait_or_keypress(seconds: float) -> bool:
    r, _, _ = select.select([sys.stdin], [], [], seconds)
    if r:
        sys.stdin.read(1)  # consume key
        return True
    return False

def clickable(url, label=None):
    label = label or url
    return f"\033]8;;{url}\033\\{label}\033]8;;\033\\"



