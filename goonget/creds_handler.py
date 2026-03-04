import json
from pathlib import Path
from getpass import getpass
from .settings_handler import get_source

CONFIG_DIR = Path.home() / ".config" / "goonget"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_api_credentials():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                source = get_source()
                if source == "rule34.xxx":
                    if "rule34_api_key" in data:
                        return data["rule34_api_key"]
                elif source == "gelbooru.com":
                    if "gelbooru_api_key" in data:
                        return data["gelbooru_api_key"]
        except json.JSONDecodeError:
            pass    # Corrupted file -» treat as missing

    # config file doesn't exist, prompt user for API credentials
    source = get_source()
    if source == "rule34.xxx":
        print("No Rule34 API Key found. You need to get it from https://rule34.xxx/index.php?page=account&s=options")
        api_credentials = getpass("Enter your Rule34 API Key: ").strip()
    elif source == "gelbooru.com":
        print("No Gelbooru API Key found. You need to get it from https://gelbooru.com/index.php?page=account&s=options")
        api_credentials = getpass("Enter your Gelbooru API Key: ").strip()

    # save credentials
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "r+") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

        data["source"] = source
        if source == "rule34.xxx":
            data["rule34_api_key"] = api_credentials
        elif source == "gelbooru.com":
            data["gelbooru_api_key"] = api_credentials

        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    print("API Access Credentials saved successfully.")
    return api_credentials
