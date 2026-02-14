import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "goonget"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass    # Corrupted file -» treat as missing
    return {}

def _save_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_current_size():
    cfg = _load_config()
    return cfg.get("size", "Fill") # default if missing

def set_size(value: str):
    cfg = _load_config()
    cfg["size"] = value 
    _save_config(cfg)

def get_slideshow_timer():
    return _load_config().get("slideshow_timer", 3) # 3s as default timer

def set_slideshow_timer(value: int):
    cfg = _load_config()
    cfg["slideshow_timer"] = value
    _save_config(cfg)