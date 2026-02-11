import json
from pathlib import Path
from getpass import getpass

CONFIG_DIR = Path.home() / ".config" / "goonget"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_api_credentials():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "api_credentials" in data:
                    return data["api_credentials"]
        except json.JSONDecodeError:
            pass    # Corrupted file -» treat as missing

    # config file doesn't exist, prompt user for API credentials
    print("No API Access Credentials found. You need to get them from https://rule34.xxx/index.php?page=account&s=options")
    api_credentials = getpass("Enter your API Access Credentials: ").strip()

    # save credentials
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"api_credentials": api_credentials}, f, indent=4)

    print("API Access Credentials saved successfully.")
    return api_credentials