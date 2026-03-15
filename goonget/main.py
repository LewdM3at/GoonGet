#!/usr/bin/env python3
import sys
import random
import curses
from .api_calls import fetch_posts
from .display_handler import display_result, display_slideshow
from .help import print_help
from .settings_ncurses import open_settings
from .settings_handler import (
    load_api_credentials,
    get_default_tags, build_tags,
    get_source, get_current_size, get_slideshow_timer,
)


def main():
    args = sys.argv[1:]

    # open settings page
    if args and args[0] == "--settings":
        curses.wrapper(open_settings)
        return

    # show default tags
    if args and args[0] == "--tags":
        tags = get_default_tags()
        print("Default Tags:", ", ".join(tags) if tags else "(none)")
        return

    # show help page
    if args and args[0] in ("--help", "--h"):
        print_help()
        return

    # result size setting
    if args and args[0].startswith("--size"):
        print(f"Current size: {get_current_size()}")
        return

    # show configured slideshow timer
    if args and args[0] in ("--ss", "--slideshow") and len(args) == 1:
        print(f"Slideshow timer: {get_slideshow_timer()} seconds")
        return

    # run slideshow with tags
    if args and args[0] in ("--ss", "--slideshow") and len(args) > 1:
        api_credentials = load_api_credentials()
        if not api_credentials:
            return
        final_tags = build_tags(args[1:])
        urls = fetch_posts(api_credentials, final_tags)
        urls = [u for u in urls if not u.lower().endswith(".gif")]
        display_slideshow(urls)
        return

    # get source
    if args and args[0] == "--source":
        print(f"Current source: {get_source()}")
        return

    # NORMAL MODE — no args or just tags, use defaults
    api_credentials = load_api_credentials()
    if not api_credentials:
        return
    final_tags = build_tags(args)
    urls = fetch_posts(api_credentials, final_tags)
    if not urls:
        print("No results found.")
        return
    result_url = random.choice(urls)
    display_result(result_url)


if __name__ == "__main__":
    main()