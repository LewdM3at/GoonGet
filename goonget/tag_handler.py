import json
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "goonget"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config():
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


def _fix_context_tags(tag: str) -> str:
    if "_." in tag:
        base, context = tag.split("_.", 1)
        return f"{base}_({context})"
    return tag


def _tag_str(entry) -> str:
    """Extract the tag string from either the old format (str) or new format (dict)."""
    if isinstance(entry, dict):
        return entry.get("tag", "")
    return str(entry)


def _tag_active(entry) -> bool:
    """Return whether a tag is active. Old format (plain string) = always active."""
    if isinstance(entry, dict):
        return entry.get("active", True)
    return True


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
    # check against existing tag strings to avoid duplicates
    existing = [_tag_str(t) for t in tags]
    if tag not in existing:
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
    # if no CLI tags were given, use default tags
    if not cli_args:
        return default_tags
    # otherwise merge the tags from cli
    normalized_cli_tags = [_fix_context_tags(t) for t in cli_args]
    return default_tags + normalized_cli_tags