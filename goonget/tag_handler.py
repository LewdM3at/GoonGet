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

def _fix_context_tags(tag: str) -> str:
    if "_." in tag:
        base, context = tag.split("_.", 1)
        return f"{base}_({context})"
    return tag


def get_default_tags() -> list[str]:
    cfg = _load_config()
    return cfg.get("default_tags", [])

def add_default_tag(tag: str):
    cfg = _load_config()
    tags = cfg.get("default_tags", [])

    if tag not in tags:
        tags.append(tag)

    cfg["default_tags"] = tags
    _save_config(cfg)

def remove_default_tag(tag: str):
    cfg = _load_config()
    tags = cfg.get("default_tags", [])

    if tag in tags:
        tags.remove(tag)

    cfg["default_tags"] = tags
    _save_config(cfg)

def build_tags(cli_args: list[str]) -> list[str]:
    default_tags = get_default_tags()
    # if no CLI tags were given, use default tags
    if not cli_args:
        return default_tags
    # otherwise merge the tags from cli
    normalized_cli_tags = [_fix_context_tags(t) for t in cli_args]
    final_tags = default_tags + normalized_cli_tags
    return final_tags

