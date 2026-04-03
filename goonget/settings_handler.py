import json
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "goonget"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ── Config I/O ────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass    # Corrupted file → treat as missing
    return {}


def _save_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ── Source / API ──────────────────────────────────────────────────────────────

def get_source() -> str:
    return _load_config().get("source", "rule34.xxx")


def set_source(source: str):
    cfg = _load_config()
    cfg["source"] = source
    _save_config(cfg)


def load_api_credentials() -> str | None:
    cfg    = _load_config()
    source = get_source()

    if source == "rule34.xxx":
        key = cfg.get("rule34_api_key", "").strip()
        if key:
            return key
        print("No Rule34 API Key found.")
        print("Get it from: https://rule34.xxx/index.php?page=account&s=options")
        print("Then add it via: goonget --settings")
        return None

    if source == "gelbooru.com":
        key = cfg.get("gelbooru_api_key", "").strip()
        if key:
            return key
        print("No Gelbooru API Key found.")
        print("Get it from: https://gelbooru.com/index.php?page=account&s=options")
        print("Then add it via: goonget --settings")
        return None


# ── Size ──────────────────────────────────────────────────────────────────────

def get_current_size() -> str:
    return _load_config().get("size", "Fill")


def set_size(value: str):
    cfg = _load_config()
    cfg["size"] = value
    _save_config(cfg)


# ── Slideshow ─────────────────────────────────────────────────────────────────

def get_slideshow_timer() -> int:
    return _load_config().get("slideshow_timer", 3)


def set_slideshow_timer(value: int):
    cfg = _load_config()
    cfg["slideshow_timer"] = value
    _save_config(cfg)

# ── Additional Information ─────────────────────────────────────────────────────────────────

def get_show_source_links() -> bool:
    return _load_config().get("show_source_links", False)


# ── Tags ──────────────────────────────────────────────────────────────────────

def _tag_str(entry) -> str:
    """Extract tag string from either old format (str) or new format (dict)."""
    if isinstance(entry, dict):
        return entry.get("tag", "")
    return str(entry)


def _tag_active(entry) -> bool:
    """Return whether a tag is active. Old plain-string format = always active."""
    if isinstance(entry, dict):
        return entry.get("active", True)
    return True


def _fix_context_tags(tag: str) -> str:
    if "_." in tag:
        base, context = tag.split("_.", 1)
        return f"{base}_({context})"
    return tag


def get_default_tags() -> list[str]:
    """Return only the active tags as plain strings."""
    cfg = _load_config()
    return [
        _tag_str(t) for t in cfg.get("default_tags", [])
        if _tag_active(t) and _tag_str(t).strip()
    ]


def add_default_tag(tag: str):
    cfg  = _load_config()
    tags = cfg.get("default_tags", [])
    if tag not in [_tag_str(t) for t in tags]:
        tags.append({"tag": tag, "active": True})
    cfg["default_tags"] = tags
    _save_config(cfg)


def remove_default_tag(tag: str):
    cfg  = _load_config()
    tags = cfg.get("default_tags", [])
    cfg["default_tags"] = [t for t in tags if _tag_str(t) != tag]
    _save_config(cfg)


def build_tags(cli_args: list[str]) -> list[str]:
    default_tags = get_default_tags()
    if not cli_args:
        return default_tags
    normalized_cli_tags = [_fix_context_tags(t) for t in cli_args]
    return default_tags + normalized_cli_tags